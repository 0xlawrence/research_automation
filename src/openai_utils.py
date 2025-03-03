# src/openai_utils.py

from openai import OpenAI
from .config import OPENAI_API_KEY
from .notion_utils import append_page_content, update_notion_status
from typing import List, Dict
import time
from .ai_client import ai_client  # 新しいAIクライアントをインポート

# クライアントの初期化をget_client関数として分離
def get_client():
    if not hasattr(get_client, '_client'):
        get_client._client = OpenAI(api_key=OPENAI_API_KEY)
    return get_client._client

def summarize_text(text: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """
    GPTモデルを用いて短い要約を生成。
    """
    try:
        messages = [
            {"role": "system", 
             "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
            },
            {
                "role": "user",
                "content": (
                    "以下の文章を200文字程度の日本語で要約をしてください。\n\n"
                    f"文章:\n{text}"
                )
            }
        ]
        
        response = ai_client.call_api(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print("Error in summarize_text:", e)
        return ""

def transform_title(title: str, max_tokens: int = 40, retries: int = 3) -> str:
    """
    OpenAI API を利用して記事のタイトルを、より魅力的かつ印象的で凝縮されたタイトルに変換する。
    出力は変換されたタイトルのみを返し、元のタイトルと同一の場合は再試行する。
    """
    for attempt in range(retries):
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a skilled editor. Follow these rules to transform the article title:\n"
                        "1. Always transform the given article title into a new, more attractive, impressive, and concise title.\n"
                        "2. The output must contain only the transformed title, with no additional prefixes, descriptions, or the original title.\n"
                        "3. The transformed result must not be identical to the original title; generate a completely new title.\n"
                        "4. Even if the input title is already good, you must perform the transformation.\n"
                        "Example: If the input is '世界経済の最新動向', the output must be '革新的な視点で紐解く世界経済の真実'.\n"
                        "Please provide the output entirely in Japanese."
                    )
                },
                {
                    "role": "user",
                    "content": f"Article Title: {title}"
                }
            ]
            
            response = ai_client.call_api(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.55,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            new_title = response.choices[0].message.content.strip()
            if new_title and new_title != title:
                return new_title
            else:
                print(f"Transformed title is identical to the original; retrying (attempt {attempt + 1}/{retries})")
        except Exception as e:
            print(f"Error in transform_title (attempt {attempt + 1}): {e}")
    return title

def handle_api_error(e: Exception, fallback_function=None, *args, **kwargs):
    """APIエラーを処理し、必要に応じてフォールバック処理を実行"""
    error_message = str(e)
    
    if "insufficient_quota" in error_message or "429" in error_message:
        print("OpenAI APIのクォータ制限に達しました。DeepSeekにフォールバックします...")
        if fallback_function:
            try:
                from deepseek_utils import get_client as get_deepseek_client
                # DeepSeekクライアントが利用可能か確認
                get_deepseek_client()
                return fallback_function(*args, **kwargs)
            except Exception as fallback_error:
                print(f"フォールバック処理中にエラーが発生: {fallback_error}")
                return ""
    
    print(f"API Error: {error_message}")
    return ""

def generate_executive_summary(text: str, max_tokens: int = 5000) -> str:
    """
    OpenAI API を利用して、記事内容からエグゼクティブサマリーを生成する。
    エグゼクティブサマリーは記事の主要なポイント、背景、影響、展望を包括的にまとめた内容。
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは優秀なブロックチェーンアナリストです。以下の記事について、包括的なエグゼクティブサマリーを生成してください。\n"
                    )
                },
                {
                    "role": "user",
                    "content": f"Article Content:\n{text}"
                }
            ],
            max_tokens=max_tokens,
            temperature=0.65,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        if not response or not hasattr(response.choices[0], 'message'):
            print("Invalid response structure")
            return ""
            
        return response.choices[0].message.content.strip()
    except Exception as e:
        from deepseek_utils import generate_executive_summary as deepseek_summary
        return handle_api_error(e, deepseek_summary, text, max_tokens)

def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    """
    テキストを指定された最大文字数で分割する。
    文章の途中で分割されないように、段落や文の区切りで分割する。
    max_chars: デフォルトを3000に減らしてトークン制限に対応
    """
    chunks = []
    current_chunk = ""
    
    # 段落ごとに分割（空行で区切る）
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # 現在のチャンクに段落を追加した場合の長さをチェック
        if len(current_chunk) + len(paragraph) < max_chars:
            current_chunk += paragraph + '\n\n'
        else:
            # 現在のチャンクが存在する場合、それを保存
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + '\n\n'
    
    # 最後のチャンクを追加
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def validate_content_quality(content: str) -> bool:
    """
    生成されたコンテンツの品質をチェックし、最低限の要件を満たしているか確認する
    """
    try:
        # 入力値の検証
        if not content or not isinstance(content, str):
            print("Invalid content type or empty content")
            return False
            
        # 最低限の長さチェック
        min_length = 100  # 少なくとも100文字はあるべき
        if len(content) < min_length:
            print(f"Content too short: {len(content)} chars (min {min_length})")
            return False
            
        # 最低限の構造チェック（見出しが含まれているか）
        if "##" not in content and "背景" not in content and "概要" not in content:
            print("Content lacks structure (no headings found)")
            return False
            
        # 文字化けなどのチェック（ASCII以外の文字が一定量あるべき）
        non_ascii = sum(1 for c in content if ord(c) > 127)
        if non_ascii < len(content) * 0.1:  # 少なくとも10%は非ASCII文字（日本語など）
            print("Content may have encoding issues (too few non-ASCII chars)")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error in validate_content_quality: {e}")
        return False

def add_rate_limit_delay():
    """APIリクエスト間にディレイを追加"""
    time.sleep(1)  # 1秒のディレイを追加

def generate_detailed_summary(text: str, max_tokens: int = 4000) -> str:
    """
    記事の詳細な要約と分析を生成する。
    チャンク処理を簡素化し、より安定した実装に変更。
    max_tokens: デフォルトを4000に設定（トークン制限に対応）
    """
    # 英語のシステムプロンプトに改善（出力は日本語）
    system_prompt = """# Role and Expertise
    You are an expert analyst specializing in blockchain, cryptocurrency, and AI technologies. Your analysis is known for:
    - Exceptional depth and clarity when explaining complex technical concepts
    - Identifying the most significant aspects of innovations and developments
    - Connecting technological advancements to business implications and market trends
    - Providing balanced perspectives on advantages, limitations, and future potentials

    # Output Format
    Your analysis must be in Japanese, structured with the following sections:

    ## 背景と文脈 (Background and Context)
    - Explain the historical or technological context necessary to understand the article
    - Identify the key problems or opportunities being addressed
    - Mention relevant previous developments or competing solutions

    ## 技術的概要 (Technical Overview)
    - Explain the core technology or approach in clear, accessible language
    - Highlight key innovations or differentiating factors
    - Describe the architecture, methodology, or implementation when relevant

    ## 市場への影響 (Market Impact)
    - Analyze potential effects on industry, competition, and user adoption
    - Identify stakeholders who benefit or may be challenged
    - Consider short and long-term implications for the ecosystem

    ## 展望と課題 (Future Outlook and Challenges)
    - Discuss potential evolution of the technology or solution
    - Identify obstacles, limitations, or risks
    - Consider regulatory, technical, or adoption challenges

    ## 結論 (Conclusion)
    - Provide a balanced final assessment
    - Highlight the most important implications
    - Share what readers should particularly pay attention to going forward

    Important: Your analysis should be informative, insightful, and nuanced - never promotional or superficial."""

    try:
        print("Generating detailed summary with OpenAI...")
        client = get_client()
        
        # テキスト長の確認
        if len(text) > 30000:
            print("Text too long, truncating to 30000 characters")
            text = text[:30000] + "..."
            
        response = client.chat.completions.create(
            model="gpt-4o-mini", # より小さなモデルを使用
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"""Analyze the following article and create a comprehensive, structured summary according to the specified format.

The analysis should be informative and insightful, focusing on key technological aspects, business implications, and future potential. Ensure your output is in Japanese, well-structured, and provides valuable insights for readers interested in blockchain, cryptocurrency, or AI technologies.

Article text:
{text}

Remember to maintain a balanced perspective, discussing both strengths and limitations, while providing context that helps readers understand the significance of the topic."""
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        if not response or not hasattr(response, 'choices') or len(response.choices) == 0:
            print("Invalid response structure")
            raise ValueError("Invalid response structure from OpenAI API")
            
        content = response.choices[0].message.content
        if not content or not isinstance(content, str):
            print("Invalid content received")
            raise ValueError("Invalid content from OpenAI API")
            
        # 内容の品質チェック
        if not validate_content_quality(content):
            print("Content quality check failed for OpenAI response")
            raise ValueError("Content quality check failed")
            
        print("Successfully generated detailed summary with OpenAI")
        return content
            
    except Exception as e:
        print(f"Error in generate_detailed_summary: {e}")
        
        # DeepSeekにフォールバック
        try:
            print("Falling back to DeepSeek for detailed summary...")
            from deepseek_utils import generate_detailed_summary as deepseek_summary
            
            # 直接呼び出し、戻り値の型チェックは不要
            fallback_content = deepseek_summary(text, max_tokens // 2)  # DeepSeekはトークン数半分に制限
            print("DeepSeek API call completed")
            
            # DeepSeek側で適切なエラーメッセージを返す実装に変更したため、
            # ここでの複雑なチェックは不要になった
            print(f"Returning DeepSeek fallback content ({len(fallback_content)} chars)")
            return fallback_content
                
        except Exception as fallback_error:
            print(f"DeepSeek fallback failed completely: {fallback_error}")
            return "要約の生成に失敗しました。記事が長すぎるか、API制限に達している可能性があります。"

def generate_insights_and_questions(text: str, max_tokens: int = 8000) -> str:
    """
    OpenAI API を利用して、記事内容に基づいたインサイトと問いを生成する。
    出力はすべて日本語で返す。
    """
    try:
        response = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an experienced analyst. Please extract insights from the article and generate thought-provoking questions. "
                        "Ensure that the output is entirely in Japanese."
                    )
                },
                {
                    "role": "user",
                    "content": f"Article Content:\n{text}"
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7,
            frequency_penalty=0.1,
            presence_penalty=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        from deepseek_utils import generate_insights_and_questions as deepseek_insights
        return handle_api_error(e, deepseek_insights, text, max_tokens)

def categorize_article_with_ai(title: str, summary: str, max_tokens: int = 10, temperature: float = 0.1) -> str:
    """
    記事のタイトルとサマリーからカテゴリを推定。
    
    Returns:
        str: 既存カテゴリまたは新規カテゴリ（条件を満たす場合のみ）
    """
    EXISTING_CATEGORIES = {
        # 既存カテゴリ
        "Blockchain", "Market", "Regulation", 
        "AI", "Security", "DeFi", "NFT",
        "Layer1", "Layer2", "DAO", "Bridge", "Social",
        "Gaming", "Metaverse", "Privacy", "Identity",
        "Product", "Development", "Airdrop", "Economy",
        "Funding",
    }
    
    try:
        # Step 1: 既存カテゴリとの適合性確認
        response_existing = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": (
                    "与えられた記事を既存のカテゴリーに分類してください。\n\n"
                    "【ルール】\n"
                    "1. 以下のカテゴリーのいずれかに75%以上の確信度で分類できる場合のみ、そのカテゴリーを選択\n"
                    "2. それ以外の場合は、必ず「None」を返す\n"
                    "3. カテゴリー名のみを出力（説明等は一切付けない）\n\n"
                    "【有効なカテゴリー】\n"
                    "Blockchain, Crypto, Market, Regulation, AI, Security, DeFi, NFT, Infrastructure, DAO, Other"
                 )
                },
                {
                    "role": "user",
                    "content": f"タイトル: {title}\n要約: {summary}"
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        category = response_existing.choices[0].message.content
        
        if category in EXISTING_CATEGORIES:
            return category
            
        # Step 2: 新規カテゴリの検討
        response_new = get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": (
                    "新しいカテゴリー名を提案してください。\n\n"
                    "【ルール】\n"
                    "1. 以下の条件をすべて満たす場合のみ新カテゴリーを提案\n"
                    "2. 条件を満たさない場合は「Other」のみを返す\n"
                    "3. カテゴリー名のみを出力（説明等は一切付けない）\n\n"
                    "【条件】\n"
                    "- ブロックチェーン/Web3領域に直接関連する\n"
                    "- 技術・概念が具体的で明確\n"
                    "- 業界で一般的に認知された用語\n"
                    "- 単一の英単語または略語（スペースなし）\n"
                    "- すべて英数字"
                 )
                },
                {
                    "role": "user",
                    "content": f"タイトル: {title}\n要約: {summary}"
                }
            ],
            max_tokens=10,
            temperature=temperature
        )
        
        new_category = response_new.choices[0].message.content
        
        if (new_category != "Other" and 
            new_category.isalnum() and
            len(new_category.split()) == 1 and
            new_category.upper() == new_category):
            return new_category
        
        return "Other"
            
    except Exception as e:
        print("Error in categorize_article_with_ai:", e)
        return "Other"

def process_article_content(page_id: str, content: str) -> bool:
    """記事内容を段階的に分析し、より深い洞察を生成する"""
    try:
        print("Processing article content...")
        
        # 1. 初期要約の生成
        print("Generating initial summary...")
        initial_summary = summarize_text(content, max_tokens=1000)
        if not initial_summary:
            print("Failed to generate initial summary")
            raise ValueError("Failed to generate initial summary")
            
        # 2. 詳細な分析の生成
        print("Generating detailed analysis...")
        detailed_analysis = generate_detailed_summary(content)
        if not detailed_analysis:
            print("Warning: Failed to generate detailed analysis")
            # 詳細分析に失敗しても続行
            detailed_analysis = "詳細分析を生成できませんでした。"
        
        # 3. 技術的深掘りと洞察の生成
        print("Generating technical insights...")
        insights = generate_insights_and_questions(content)
        if not insights:
            print("Warning: Failed to generate insights")
            # 洞察生成に失敗しても続行
            insights = "技術的洞察を生成できませんでした。"
        
        # 最終的なコンテンツの構築
        final_content = f"""

## Executive Summary
{initial_summary}

## Detailed Analysis
{detailed_analysis}

## Technical Questions and Insights
{insights}
"""
        
        # Notionページの更新
        print("Adding content to Notion page...")
        blocks_added = append_page_content(page_id, final_content)
        if blocks_added:
            print(f"Successfully added {blocks_added} blocks to page")
            update_notion_status(page_id, "Completed")
            return True
        else:
            print("Failed to add content to Notion page")
            update_notion_status(page_id, "Error")
            return False
        
    except Exception as e:
        print(f"Error in process_article_content: {e}")
        try:
            update_notion_status(page_id, "Error")
        except Exception:
            pass
        return False