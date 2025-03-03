#!/usr/bin/env python3
"""
Perplexity Research Assistant
A tool for conducting research using Perplexity API and saving results to Notion.
"""

if __name__ == '__main__' and __package__ is None:
    import os
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    __package__ = "src"

from openai import OpenAI
from datetime import datetime
import argparse
import re
import logging
import time
import functools
from typing import Dict, Optional, List, Tuple, Any, Callable
import pytz
import unicodedata
from .config import PERPLEXITY_API_KEY, NOTION_TOKEN, NOTION_DATABASE_ID
from .notion_utils import create_notion_page, append_page_content, update_notion_status
from notion_client import Client
from .rss_fetch import clean_domain

#############################################
# ロギング設定
#############################################

# ロガーの設定
logger = logging.getLogger("perplexity")
logger.setLevel(logging.INFO)

# コンソールハンドラの設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

#############################################
# エラーハンドリング共通関数
#############################################

class PerplexityError(Exception):
    """Perplexityモジュールの基本例外クラス"""
    pass

class APIError(PerplexityError):
    """API呼び出し関連のエラー"""
    pass

class ContentProcessingError(PerplexityError):
    """コンテンツ処理中のエラー"""
    pass

class NotionError(PerplexityError):
    """Notion連携関連のエラー"""
    pass

def retry(max_attempts: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, 
          allowed_exceptions: tuple = (APIError,)):
    """
    関数の実行を指定回数リトライするデコレータ
    
    Args:
        max_attempts: 最大試行回数
        delay: 初期待機時間（秒）
        backoff_factor: バックオフ係数（待機時間の増加率）
        allowed_exceptions: リトライ対象の例外タプル
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"最大リトライ回数に達しました: {e}")
                        raise
                    
                    logger.warning(f"リトライ {attempts}/{max_attempts}: {e}, {current_delay}秒後に再試行")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    
        return wrapper
    return decorator

def handle_api_error(func: Callable) -> Callable:
    """API呼び出しのエラーハンドリングを行うデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # OpenAI API特有のエラーを確認
            error_message = str(e)
            if "rate_limit" in error_message or "429" in error_message:
                logger.warning(f"API Rate Limit に達しました: {error_message}")
                raise APIError(f"API Rate Limit: {error_message}")
            elif "insufficient_quota" in error_message:
                logger.error(f"APIクォータ不足: {error_message}")
                raise APIError(f"API Quota Exceeded: {error_message}")
            elif "invalid_request_error" in error_message:
                logger.error(f"無効なAPIリクエスト: {error_message}")
                raise APIError(f"Invalid API Request: {error_message}")
            elif "authentication" in error_message:
                logger.error(f"API認証エラー: {error_message}")
                raise APIError(f"API Authentication Error: {error_message}")
            else:
                # その他のAPIエラー
                logger.error(f"API呼び出し中にエラーが発生: {error_message}")
                raise APIError(f"API Error: {error_message}")
    return wrapper

def safe_process(func: Callable) -> Callable:
    """コンテンツ処理のエラーハンドリングを行うデコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"コンテンツ処理中にエラーが発生: {e}")
            raise ContentProcessingError(f"Processing Error: {e}")
    return wrapper

#############################################
# クエリ分析モジュール - 旧query_analyzer.py
#############################################

@safe_process
def analyze_query(query: str) -> dict:
    """
    クエリを理解し、調査タスクを分解・定義するための前処理関数.
    
    このダミー実装では、シンプルなルールベースのアプローチで以下の要素を抽出します：
      - topics: クエリ中の主要キーワード（単語抽出による）
      - tasks: 調査タスクの候補リスト
      - research_methods: 調査に利用すべき手法の候補リスト
    
    Args:
        query (str): ユーザー入力のクエリ
    
    Returns:
        dict: 解析結果の辞書
              {
                "topics": [ ... ],
                "tasks": [ ... ],
                "research_methods": [ ... ]
              }
    """
    logger.info(f"クエリの分析を開始: {query[:50]}...")
    
    # 単語抽出：すべての単語をリスト化し、3文字以上の単語をトピック候補とする（重複排除）
    words = re.findall(r'\b\w+\b', query)
    topics = list({word.lower() for word in words if len(word) >= 3})
    
    # ダミー実装として、内容に応じたタスクと調査手法候補を用意
    tasks = [
        "クエリの背景整理",
        "主要キーワードの定義",
        "市場動向・統計データの確認",
        "関連事例や文献の調査"
    ]
    
    research_methods = [
        "文献レビュー",
        "インタビュー調査",
        "統計解析",
        "競合分析",
        "専門家意見の収集"
    ]
    
    result = {
        "topics": topics,
        "tasks": tasks,
        "research_methods": research_methods
    }
    
    logger.debug(f"クエリ分析結果: {result}")
    return result

#############################################
# 対話管理モジュール - 旧dialogue_manager.py
#############################################

class DialogueManager:
    """対話履歴を管理するクラス"""
    
    def __init__(self):
        self.conversation_history: List[Tuple[str, str]] = []
        self.max_history_length = 10
        logger.debug("DialogueManagerを初期化しました")

    def add_turn(self, role: str, content: str) -> None:
        """
        Add a new conversation turn to the history.
        
        Args:
            role (str): The role of the speaker ('user' or 'assistant')
            content (str): The content of the message
        """
        self.conversation_history.append((role, content))
        
        # Keep only the last N turns to prevent the history from growing too large
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
            
        logger.debug(f"会話ターンを追加しました: {role} - {content[:30]}...")

    def get_history(self) -> List[Tuple[str, str]]:
        """
        Get the conversation history.
        
        Returns:
            List[Tuple[str, str]]: List of (role, content) tuples
        """
        return self.conversation_history

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.debug("会話履歴をクリアしました")

    def get_formatted_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history formatted for API calls.
        
        Returns:
            List[Dict[str, str]]: List of message dictionaries with 'role' and 'content' keys
        """
        return [
            {"role": role, "content": content}
            for role, content in self.conversation_history
        ]

#############################################
# 回答後処理モジュール - 旧answer_post_processor.py
#############################################

@safe_process
def post_process_answer(content: str) -> str:
    """
    Post-process the API response content to ensure proper formatting.
    
    Args:
        content (str): Raw API response content
        
    Returns:
        str: Processed content with proper formatting
    """
    if not content:
        logger.warning("空のコンテンツが後処理に渡されました")
        return ""
    
    logger.debug(f"回答の後処理を開始: {len(content)}文字")
    
    # Remove any system-specific formatting
    content = re.sub(r'<s>.*?</s>', '', content, flags=re.DOTALL)
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    
    # Ensure proper markdown heading formatting
    content = re.sub(r'^(?!#)(.+?)\n={3,}$', r'# \1', content, flags=re.MULTILINE)
    content = re.sub(r'^(?!#)(.+?)\n-{3,}$', r'## \1', content, flags=re.MULTILINE)
    
    # Ensure proper list formatting
    content = re.sub(r'(?m)^[*•] ', '- ', content)
    
    # Ensure proper spacing around headings
    content = re.sub(r'(?m)^(#+\s.*?)(?:\n(?!\n))', r'\1\n', content)
    
    # Remove excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Ensure proper code block formatting
    content = re.sub(r'```\s*\n*([^`]+?)\s*\n*```', r'```\n\1\n```', content)
    
    logger.debug("回答の後処理が完了しました")
    return content.strip()

#############################################
# メイン研究アシスタントクラス - 旧perplexity.py
#############################################

class PerplexityResearch:
    """Perplexity APIを使用した研究アシスタントクラス"""
    
    def __init__(self):
        """Perplexity研究アシスタントの初期化"""
        logger.info("PerplexityResearchを初期化しています...")
        
        try:
            self.client = OpenAI(
                api_key=PERPLEXITY_API_KEY,
                base_url="https://api.perplexity.ai"
            )
            self.dialogue_manager = DialogueManager()
            logger.info("PerplexityResearchの初期化が完了しました")
        except Exception as e:
            logger.error(f"初期化中にエラーが発生: {e}")
            raise PerplexityError(f"初期化エラー: {e}")

    @handle_api_error
    def _call_perplexity_api(self, messages: List[Dict[str, str]], 
                            model: str = "pplx-70b-online", 
                            temperature: float = 0.7, 
                            max_tokens: int = 4000) -> str:
        """
        Perplexity APIを呼び出して応答を取得する共通メソッド
        
        Args:
            messages: APIに送信するメッセージリスト
            model: 使用するモデル名
            temperature: 生成の多様性
            max_tokens: 最大生成トークン数
            
        Returns:
            str: API応答の内容
        """
        logger.info(f"Perplexity APIを呼び出し中... (model: {model})")
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        logger.debug(f"API応答を受信: {len(content)}文字")
        
        return content

    def _create_research_prompt(self, query: str) -> list:
        """
        クエリ解析結果を含めたシステムプロンプトを生成する。
        """
        # クエリ解析を実施
        analysis = analyze_query(query)
        
        # 解析結果を文字列テキストに整形
        analysis_text = (
            "【解析結果】\n"
            f"■ トピック: {', '.join(analysis['topics'])}\n"
            f"■ 調査タスク: {', '.join(analysis['tasks'])}\n"
            f"■ 調査手法: {', '.join(analysis['research_methods'])}\n"
        )
        
        # システムプロンプトに解析結果を組み込み、タスク分解と調査方法の指示を追加
        system_content = (
            "あなたは市場分析の専門家です。以下の解析結果を参考に、ユーザーのクエリに対して徹底した調査タスクを実施し、"
            "調査計画と詳細な分析を行ってください。\n\n"
            f"{analysis_text}\n"
            "次のステップとして以下を実施してください。\n"
            "1. 問題の本質を分解し、重要な要素を整理する。\n"
            "2. 適切な調査手法を選定し、根拠となるデータや文献を統合する。\n"
            "3. 分析結果を以下の形式で出力してください：\n\n"
            "## Executive Summary\n"
            "（要約を500文字程度で記述）\n\n"
            "## Key Analysis Points\n"
            "（重要な分析ポイントを箇条書きで記述）\n"
            "- ポイント1\n"
            "- ポイント2\n"
            "...\n\n"
            "## Insights\n"
            "（市場洞察や示唆を箇条書きで記述）\n"
            "- インサイト1\n"
            "- インサイト2\n"
            "...\n\n"
            "## References\n"
            "（参考文献やURLを箇条書きで記述）\n"
            "- URL1\n"
            "- URL2\n"
            "...\n\n"
            "※各セクションは必ず見出し（##）から始めてください。\n"
            "※思考プロセスは <think>タグで囲んでください。\n"
        )
        
        return [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": f"対象クエリ: {query}\n上記の解析結果を踏まえ、調査計画及び分析結果を構築してください。"
            }
        ]

    @safe_process
    def _extract_sections(self, content: str) -> dict:
        """Extract sections from API response content"""
        sections = {
            "executive_summary": "",
            "key_points": "",
            "market_insights": "",
            "references": ""
        }
        
        # Remove any system-specific formatting
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        # Remove section separators
        content = re.sub(r'\n---+\n', '\n\n', content)
        
        # Regex patterns for section extraction (allow alternative headings for references, including common misspellings)
        patterns = {
            "executive_summary": r"(?:## )?Executive Summary\s*(.*?)(?=##|$)",
            "key_points": r"(?:## )?Key Analysis Points?\s*(.*?)(?=## |$)",
            "market_insights": r"(?:## )?(?:Market )?Insights?\s*(.*?)(?=## |$)",
            "references": r"(?:## )?(?:References|Reference|Refrence|参考文献)\s*(.*?)(?=$)"
        }
        
        for section, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                # Remove markdown formatting and others
                section_content = match.group(1).strip()
                section_content = self._clean_formatting(section_content)
                sections[section] = section_content
        
        # Fallback: if no sections were found, split by double newlines
        if not any(sections.values()):
            paragraphs = content.split('\n\n')
            if paragraphs:
                sections["executive_summary"] = paragraphs[0].strip()
                if len(paragraphs) > 1:
                    sections["key_points"] = '\n\n'.join(paragraphs[1:]).strip()
        
        return sections

    def _format_for_notion_blocks(self, text: str) -> str:
        """Format text specifically for Notion blocks"""
        # 各ブロックを明示的に分離
        blocks = text.split('\n\n')
        formatted_blocks = []
        
        for block in blocks:
            if block.startswith('#'):
                # 見出しブロック
                formatted_blocks.append(f"{block}\n")
            elif block.startswith('- '):
                # リストブロック
                formatted_blocks.append(block)
            else:
                # 段落ブロック
                formatted_blocks.append(block)
        
        return '\n\n'.join(formatted_blocks)

    def _build_section_content(self, title: str, content: str) -> list:
        """Build a properly formatted section"""
        section = []
        
        # メインセクションの見出し
        section.append(f"## {title}")
        section.append("")
        
        # 見出しレベルの調整と空の見出しを削除
        content = re.sub(r'(?m)^#+\s*$\n*', '', content)
        
        # 見出しの処理を改善
        content = re.sub(r'(?m)^#\s*(\d+\.\s*)?(\*\*)?([^#\n]+?)(\*\*)?$', r'### \3', content)
        
        # 段落を処理
        paragraphs = []
        current_paragraph = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # 見出しの処理
            if line.startswith('###'):
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                paragraphs.append('\n' + line)  # 見出しの前に空行を追加
                continue
            
            # 箇条書きの処理
            if line.startswith('- '):
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                paragraphs.append(line)
                continue
            
            # 空行の処理
            if not line:
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                continue
            
            # 通常の文章を段落に追加
            current_paragraph.append(line)
        
        # 最後の段落を追加
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # 段落を整形して追加
        for paragraph in paragraphs:
            if paragraph.strip():
                section.append(paragraph)
                if paragraph.startswith('###'):
                    section.append("")  # 見出しの後に空行を追加
        
        return section

    def _clean_formatting(self, text: str) -> str:
        """Clean and format text for Notion compatibility"""
        cleaned = text
        
        # 空の見出しを削除
        cleaned = re.sub(r'(?m)^#+\s*$\n*', '', cleaned)
        
        # 見出しの処理を改善
        cleaned = re.sub(r'(?m)^#\s*(\d+\.\s*)?(\*\*)?([^#\n]+?)(\*\*)?$', r'### \3', cleaned)
        
        # 見出しの前後に適切な空行を追加
        cleaned = re.sub(r'(?<!\n\n)(###\s+[^\n]+)', r'\n\n\1', cleaned)
        
        # 箇条書きの整形
        cleaned = re.sub(r'(?<!\n)\n\s*-\s+', '\n\n- ', cleaned)
        
        # 段落を処理
        paragraphs = []
        current_paragraph = []
        
        for line in cleaned.split('\n'):
            line = line.strip()
            
            # 見出しまたは箇条書きの場合は新しい段落として扱う
            if line.startswith('###') or line.startswith('- '):
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                paragraphs.append(line)
                continue
            
            # 空行の場合は段落を区切る
            if not line:
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                continue
            
            # 通常の文章を段落に追加
            current_paragraph.append(line)
        
        # 最後の段落を追加
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))
        
        # 段落を結合
        cleaned = '\n\n'.join(filter(None, paragraphs))
        
        return cleaned.strip()

    def _extract_first_url(self, text: str) -> str:
        """Extract first URL from references"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, text)
        return urls[0] if urls else ""

    def _determine_category(self, title: str, summary: str) -> str:
        """Determine category based on content using strict rules"""
        EXISTING_CATEGORIES = {
            "Blockchain", "Market", "Regulation", 
            "AI", "Security", "DeFi", "NFT",
            "Layer1", "Layer2", "DAO", "Bridge", "Social",
            "Gaming", "Metaverse", "Privacy", "Identity",
            "Product", "Development", "Airdrop", "Economy",
            "Funding"
        }
        
        try:
            response = self.client.chat.completions.create(
                model="sonar-reasoning-pro",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Select the most appropriate category from the following list. "
                            "Return ONLY the category name, no explanation:\n"
                            f"{', '.join(EXISTING_CATEGORIES)}\n\n"
                            "If no category matches with high confidence, return 'Other'"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Title: {title}\nSummary: {summary}"
                    }
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            category = response.choices[0].message.content.strip()
            category = re.sub(r'[^\w\s]', '', category).strip()
            
            return category if category in EXISTING_CATEGORIES else "Other"
            
        except Exception as e:
            print(f"Error in category determination: {e}")
            return "Other"

    @retry(max_attempts=3)
    @handle_api_error
    def research(self, query: str) -> Optional[str]:
        """
        与えられたクエリについて調査し、結果をNotionに保存する
        
        Args:
            query: 研究するクエリ
            
        Returns:
            Optional[str]: 作成されたNotionページのID、失敗時はNone
        """
        logger.info(f"研究クエリの処理を開始: {query[:50]}...")
        
        # プロンプトを作成
        messages = self._create_research_prompt(query)
        
        try:
            # APIを呼び出し
            content = self._call_perplexity_api(
                messages=messages,
                model="pplx-70b-online",
                temperature=0.7,
                max_tokens=8000
            )
            
            # 応答を後処理
            processed_content = post_process_answer(content)
            
            # セクションを抽出
            sections = self._extract_sections(processed_content)
            logger.debug(f"セクションの抽出完了: {list(sections.keys())}")
            
            # タイトルを生成
            title = self._generate_title(query)
            logger.info(f"生成されたタイトル: {title}")
            
            # 要約を取得
            summary = sections.get("executive_summary", "")
            if not summary:
                summary = self._extract_best_summary(processed_content)
            
            # カテゴリを決定
            category = self._determine_category(title, summary)
            
            # Notionページを作成
            current_time = datetime.now(pytz.timezone('Asia/Tokyo'))
            
            result = self._save_to_notion(
                title=title,
                summary=summary,
                category=category,
                content=processed_content,
                sections=sections,
                current_time=current_time
            )
            
            logger.info(f"研究完了: {title}")
            return result
            
        except APIError as e:
            logger.error(f"研究処理中のAPIエラー: {e}")
            return None
        except Exception as e:
            logger.error(f"研究処理中の予期せぬエラー: {e}")
            return None

    @handle_api_error
    def _save_to_notion(self, title: str, summary: str, category: str, 
                       content: str, sections: Dict[str, str], 
                       current_time: datetime) -> Optional[str]:
        """
        研究結果をNotionに保存する
        
        Args:
            title: ページタイトル
            summary: 要約
            category: カテゴリ
            content: 全体の内容
            sections: 抽出されたセクション
            current_time: 現在時刻
            
        Returns:
            Optional[str]: 作成されたNotionページのID、失敗時はNone
        """
        try:
            # Notionページを作成
            page = create_notion_page(
                title=title,
                url="",  # No URL for Perplexity analysis
                summary=summary,
                published_date=current_time,
                source="Perplexity API",
                category=category
            )
            
            if not page:
                logger.error("Notionページの作成に失敗しました")
                return None
                
            page_id = page["id"]
            logger.info(f"Notionページを作成しました: {page_id}")
            
            # コンテンツをNotionページに保存
            blocks = []
            
            # 各セクションを追加
            if sections["executive_summary"]:
                blocks.extend(self._build_section_content("Executive Summary", sections["executive_summary"]))
                
            if sections["key_points"]:
                blocks.extend(self._build_section_content("Key Analysis Points", sections["key_points"]))
                
            if sections["market_insights"]:
                blocks.extend(self._build_section_content("Insights", sections["market_insights"]))
                
            if sections["references"]:
                blocks.extend(self._build_section_content("References", sections["references"]))
            
            # Notionが一度に扱えるブロックのサイズ制限に合わせて分割
            from .notion_utils import convert_content_to_blocks
            block_chunks = self._split_content_for_notion(content)
            
            # 最初のチャンクを追加
            success = append_page_content(page_id, blocks)
            if not success:
                raise NotionError("Notionページへのコンテンツ追加に失敗しました")
                
            # 残りのチャンクを追加
            for i, chunk in enumerate(block_chunks[1:], 1):
                logger.debug(f"チャンク {i+1}/{len(block_chunks)} を追加中...")
                chunk_blocks = convert_content_to_blocks(chunk)
                if not append_page_content(page_id, chunk_blocks):
                    logger.warning(f"チャンク {i+1} の追加に失敗しました")
            
            # ステータスを更新
            update_notion_status(page_id, "Completed")
            logger.info(f"コンテンツをNotionに正常に保存しました: {page_id}")
            
            return page_id
            
        except Exception as e:
            logger.error(f"Notionへの保存中にエラー: {e}")
            if 'page_id' in locals():
                update_notion_status(page_id, "Error")
            raise NotionError(f"Notion保存エラー: {e}")

    def _generate_title(self, query: str) -> str:
        """クエリから適切なタイトルを生成"""
        # 長いクエリを切り詰める
        truncated_query = query[:80] + "..." if len(query) > 80 else query
        return f"Perplexity Analysis: {truncated_query}"

    @safe_process
    def _extract_best_summary(self, text: str) -> str:
        """テキストから最も適切な要約部分を抽出する"""
        logger.debug("最適な要約部分の抽出を開始")
        
        # 要約を含むと思われるセクションを探す
        summary_section = ""
        
        # Executive Summaryセクションを探す
        summary_match = re.search(r'##\s*Executive\s+Summary\s*\n(.*?)(?=##|\Z)', text, re.DOTALL)
        if summary_match:
            summary_section = summary_match.group(1).strip()
            
        # 要約セクションが見つからない場合は最初の段落を使用
        if not summary_section:
            paragraphs = text.split('\n\n')
            if paragraphs:
                # 最初の段落（見出しでない場合）
                for p in paragraphs:
                    if not p.startswith('#') and len(p.strip()) > 10:
                        summary_section = p
                        break
        
        # 最大300文字に制限
        if len(summary_section) > 300:
            summary_section = summary_section[:297] + "..."
            
        logger.debug(f"抽出された要約: {len(summary_section)}文字")
        return summary_section

    @safe_process
    def _extract_urls(self, text: str) -> list:
        """テキストからURLを安全に抽出"""
        logger.debug("URLの抽出を開始")
        
        try:
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
            # 重複排除＆最大5件
            unique_urls = list(dict.fromkeys(urls))[:5]
            
            logger.debug(f"{len(unique_urls)}件のURLを抽出しました")
            return unique_urls
        except Exception as e:
            logger.warning(f"URL抽出中にエラー: {e}")
            return []

    @safe_process
    def _split_content_for_notion(self, content: str, max_length: int = 2000) -> List[str]:
        """
        Split content into chunks that fit within Notion's size limits while preserving Japanese text integrity.
        
        Args:
            content (str): The content to split
            max_length (int): Maximum length for each chunk (default: 2000)
            
        Returns:
            List[str]: List of content chunks
        """
        logger.debug(f"コンテンツの分割を開始: {len(content)}文字")
        
        if not content:
            logger.warning("分割対象のコンテンツが空です")
            return []

        # 文字化け対策：文字コードの正規化
        content = unicodedata.normalize('NFKC', content)
        
        # 見出しと本文を分離するための正規則表現
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        # 段落を分割（空行で区切る）
        paragraphs = []
        current_paragraph = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # 見出しの処理
            heading_match = re.match(heading_pattern, line)
            if heading_match:
                if current_paragraph:
                    paragraphs.append('\n'.join(current_paragraph))
                    current_paragraph = []
                paragraphs.append(line)
                continue
            
            # 空行の処理
            if not line:
                if current_paragraph:
                    paragraphs.append('\n'.join(current_paragraph))
                    current_paragraph = []
                paragraphs.append('')
                continue
            
            # 箇条書きの処理
            if line.startswith(('- ', '* ', '1. ')):
                if current_paragraph:
                    paragraphs.append('\n'.join(current_paragraph))
                    current_paragraph = []
                paragraphs.append(line)
                continue
            
            # 通常の段落の処理
            current_paragraph.append(line)
        
        # 最後の段落を追加
        if current_paragraph:
            paragraphs.append('\n'.join(current_paragraph))
        
        # セクションに分割
        sections = []
        current_section = []
        current_length = 0
        
        for paragraph in paragraphs:
            # 段落の長さを計算（改行文字を含む）
            paragraph_length = len(paragraph) + 1  # +1 for newline
            
            # 新しいセクションが必要か判断
            if current_length + paragraph_length > max_length:
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
                    current_length = 0
            
            # 段落を追加
            current_section.append(paragraph)
            current_length += paragraph_length
        
        # 最後のセクションを追加
        if current_section:
            sections.append('\n'.join(current_section))
        
        # セクション間の空行を調整
        sections = [re.sub(r'\n{3,}', '\n\n', section) for section in sections]
        
        logger.debug(f"{len(sections)}個のセクションに分割しました")
        return sections

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    ロギングの設定をセットアップ
    
    Args:
        log_level: ロギングレベル
        log_file: ログファイルのパス（指定した場合）
    """
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # フォーマッタの設定
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # ファイルハンドラの設定（オプション）
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # デフォルトで使用するPerplexityロガーの設定
    perplexity_logger = logging.getLogger("perplexity")
    perplexity_logger.setLevel(log_level)
    
    return root_logger

@retry(max_attempts=3)
def interactive_mode():
    """対話モードでPerplexity研究アシスタントを実行"""
    try:
        logger.info("対話モードを開始します...")
        researcher = PerplexityResearch()
        
        print("\n===== Perplexity Research Assistant =====")
        print("質問を入力してください（'exit'で終了）")
        
        while True:
            try:
                query = input("\n>> ")
                if query.lower() in ["exit", "quit", "q"]:
                    print("対話モードを終了します。")
                    break
                    
                if not query.strip():
                    continue
                    
                notion_id = researcher.research(query)
                
                if notion_id:
                    print(f"\n✅ Notionページを作成しました: https://notion.so/{notion_id.replace('-', '')}")
                else:
                    print("\n❌ 処理中にエラーが発生しました。")
                    
            except KeyboardInterrupt:
                print("\n対話モードを終了します。")
                break
            except Exception as e:
                logger.error(f"対話モード実行中のエラー: {e}")
                print(f"\n❌ エラー: {e}")
    
    except Exception as e:
        logger.error(f"対話モードの初期化中にエラー: {e}")
        print(f"致命的なエラー: {e}")

def main():
    """コマンドラインからの実行のメインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description='Research Assistant - A tool for conducting research using Perplexity API'
    )
    parser.add_argument('query', nargs='?', help='Research query')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--log', '-l', help='Log file path')
    
    args = parser.parse_args()
    
    # ロギングのセットアップ
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level=log_level, log_file=args.log)
    
    if args.interactive:
        interactive_mode()
    elif args.query:
        researcher = PerplexityResearch()
        notion_id = researcher.research(args.query)
        
        if notion_id:
            print(f"\n✅ Notionページを作成しました: https://notion.so/{notion_id.replace('-', '')}")
        else:
            print("\n❌ 処理中にエラーが発生しました。")
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 