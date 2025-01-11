# src/openai_utils.py

import openai
from src.config import OPENAI_API_KEY

# OpenAI APIキーを設定
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
                        "以下の文章を300文字程度の日本語で要点をまとめてください。\n\n"
                        f"文章:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        summary = response["choices"][0]["message"]["content"].strip()
        return summary
    except Exception as e:
        print("Error in summarize_text:", e)
        return ""


def generate_detailed_summary(text: str, 
                              max_tokens: int = 3000, 
                              temperature: float = 0.7) -> str:
    """
    記事本文から詳細なサマリーを生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", 
                 "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                            "Markdown形式で文章を整え、Notionで見やすい要約を作成してください。"
                            "箇条書きを行う際はBoldを使用しないでください。"
                },
                {
                    "role": "user",
                    "content": (
                        "以下の記事本文を基に、詳細なサマリーを日本語で作成してください。"
                        "以下の見出しを使って、段階的に整理をお願いします：\n\n"
                        "# Overview\n"
                        "# Take away\n"
                        "# Insights\n"
                        "# Conclusion\n\n"
                        f"本文:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        detailed_summary = response["choices"][0]["message"]["content"].strip()
        return detailed_summary
    except Exception as e:
        print("Error in generate_detailed_summary:", e)
        return ""


def generate_report_outline(text: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    記事本文を基にレポート作成の骨子を生成（Markdown形式）。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                               "Markdown形式で文章を整え、Notionで見やすいアウトラインを作成してください。"
                },
                {
                    "role": "user",
                    "content": (
                        "以下の記事本文を基にレポートの骨子を日本語で提案してください。\n\n"
                        "【出力形式】\n"
                        "# Background\n"
                        "- 箇条書き\n"
                        "# Ploblems\n"
                        "- 箇条書き\n"
                        "# Solutions\n"
                        "- 箇条書き\n"
                        "# Conclustion\n\n"
                        f"本文:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        report_outline = response["choices"][0]["message"]["content"].strip()
        return report_outline
    except Exception as e:
        print("Error in generate_report_outline:", e)
        return ""

def generate_insights_and_questions(text: str, 
                                    max_tokens: int = 1000, 
                                    temperature: float = 0.7) -> str:
    """
    記事本文を基にレポート作成に必要な考察の視点や問いをMarkdown形式で生成。
    Notionで見やすくなるよう、見出しや箇条書きを活用した出力を指示する。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "あなたは優秀なプロのブロックチェーンリサーチャー兼テクニカルライターです。"
                        "Markdown形式で文章を整え、Notionで見やすい考察の視点や問いを提案してください。"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "以下の記事本文を基に、レポート作成に役立つ考察の視点や問いを"
                        "日本語で提案してください。\n\n"
                        "【出力形式例】\n"
                        "# 考察の視点\n"
                        "- 箇条書き\n"
                        "# 質問一覧\n"
                        "1. 箇条書き\n"
                        f"本文:\n{text}"
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            frequency_penalty=0.2,  # 繰り返し表現を少し抑える
            presence_penalty=0.3    # 新しいトピックに触れることを促す
        )
        insights_and_questions = response["choices"][0]["message"]["content"].strip()
        return insights_and_questions
    except Exception as e:
        print("Error in generate_insights_and_questions:", e)
        return ""

def categorize_article_with_ai(title: str, summary: str, max_tokens: int = 10, temperature: float = 0.3) -> str:
    """
    OpenAIを使用して記事のカテゴリを自動割り当て。
    """
    try:
        prompt = (
            "以下のタイトル、要約、および本文の抜粋を基に、以下のカテゴリから1つを選んでください。"
            "DeFi, NFT, Layer1, Layer2, DAO, AI, その他。\n\n"
            "カテゴリを決定する際には以下を考慮してください：\n"
            "- DeFi: 分散型金融に関連するトピック\n"
            "- NFT: デジタルアートやトークンに関連するトピック\n"
            "- Layer1: ビットコイン、イーサリアムなど基盤チェーンに関連するトピック\n"
            "- Layer2: スケーラビリティ技術に関連するトピック\n"
            "- DAO: 自律分散型組織やガバナンスに関連するトピック\n"
            "- AI: 人工知能や機械学習に関連するトピック\n"
            "- その他: 上記に該当しないトピック\n\n"
            f"タイトル: {title}\n"
            f"要約: {summary}\n"
            "カテゴリを一つだけ選んでください："
        )
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたは記事の内容に基づいてカテゴリを割り当てるプロです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        category = response["choices"][0]["message"]["content"].strip()
        valid_categories = ["DeFi", "NFT", "Layer1", "Layer2", "DAO", "AI", "その他"]
        return category if category in valid_categories else "その他"
    except Exception as e:
        print(f"Error in categorize_article_with_ai: {e}")
        return "その他"