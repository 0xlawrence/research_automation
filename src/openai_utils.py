# src/openai_utils.py

import openai
from src.config import OPENAI_API_KEY
from src.notion_utils import append_page_content, update_notion_status

# OpenAIのAPI keyを設定
openai.api_key = OPENAI_API_KEY

def summarize_text(text: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    GPTモデルを用いて短い要約を生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                },
                {
                    "role": "user",
                    "content": (
                        "以下の文章を200文字程度の日本語で要点整理をしてください。\n\n"
                        f"文章:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        summary = response.choices[0].message['content'].strip()
        return summary
    except Exception as e:
        print("Error in summarize_text:", e)
        return ""

def generate_detailed_summary(text: str, max_tokens: int = 3000, temperature: float = 0.7) -> str:
    """
    記事本文から詳細なサマリーを生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                },
                {
                    "role": "user",
                    "content": (
                        "以下の文章を詳細に分析し、1000文字程度の日本語で以下の項目に分けて整理してください：\n"
                        "1. 背景\n"
                        "2. 概要\n"
                        "3. 仕組み・技術的構造\n"
                        "4. 市場への影響\n"
                        "5. 今後の展望\n\n"
                        f"文章:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("Error in generate_detailed_summary:", e)
        return ""

def generate_report_outline(text: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    記事の内容から報告書のアウトラインを生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                },
                {
                    "role": "user",
                    "content": (
                        "以下の文章を参考にして、レポートを作成するためのレポートアウトラインを日本語で作成してください。\n"
                        "重要なポイントを階層的に整理し、箇条書きで表現してください。\n\n"
                        f"文章:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("Error in generate_report_outline:", e)
        return ""

def generate_insights_and_questions(text: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """
    記事の内容から洞察と質問を生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                },
                {
                    "role": "user",
                    "content": (
                        "以下の文章を分析し、以下の2つの観点で日本語でまとめてください：\n"
                        "1. 重要な洞察（3-5個）\n"
                        "2. 追加調査が必要な質問（3-5個）\n\n"
                        f"文章:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("Error in generate_insights_and_questions:", e)
        return ""

def categorize_article_with_ai(title: str, summary: str, max_tokens: int = 10, temperature: float = 0.3) -> str:
    """
    記事のタイトルとサマリーからカテゴリを推定。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": "以下のカテゴリーから最も適切なものを1つ選んでください：\n"
                           "Blockchain, Crypto, Market, Regulation, AI, Security, DeFI, NFT, Layer1, Layer2, DAO"
                },
                {
                    "role": "user",
                    "content": f"タイトル: {title}\n要約: {summary}"
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print("Error in categorize_article_with_ai:", e)
        return "Uncategorized"

def process_article_content(page_id: str, article_content: str) -> bool:
    """
    記事の内容を処理し、各種分析結果をNotionに追加。
    """
    try:
        # 要約を生成
        summary = summarize_text(article_content)
        if not summary:
            return False
            
        # 詳細なサマリーを生成
        detailed_summary = generate_detailed_summary(article_content)
        
        # アウトラインを生成
        outline = generate_report_outline(article_content)
        
        # 洞察と質問を生成
        insights = generate_insights_and_questions(article_content)
        
        # 結果をNotionに追加
        content = f"## 要約\n{summary}\n\n## 概要\n{detailed_summary}\n\n## レポートアウトラインの提案\n{outline}\n\n## インサイトと問い\n{insights}"
        append_page_content(page_id, content)
        
        # ステータスを更新
        update_notion_status(page_id, "Processed")
        
        return True
        
    except Exception as e:
        print("Error in process_article_content:", e)
        return False