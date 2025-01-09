import openai
from src.config import OPENAI_API_KEY

# OpenAI APIキーを設定
openai.api_key = OPENAI_API_KEY

def summarize_text(text: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
    """
    GPTモデルを用いて短い要約を生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀なプロのブロックチェーンリサーチャーです。"},
                {
                    "role": "user",
                    "content": f"以下の文章を短く日本語で要約してください。\n{text}"
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        summary = response["choices"][0]["message"]["content"].strip()
        return summary
    except Exception as e:
        print("Error in summarize_text:", e)
        return ""

def generate_detailed_summary(text: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    記事本文から詳細なサマリーを生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀なプロのブロックチェーンリサーチャーです。"},
                {
                    "role": "user",
                    "content": f"以下の記事本文を基に詳細な要点まとめを日本語で作成してください。\n\n{text}"
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        detailed_summary = response["choices"][0]["message"]["content"].strip()
        return detailed_summary
    except Exception as e:
        print("Error in generate_detailed_summary:", e)
        return ""

def generate_report_outline(text: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    記事本文を基にレポート作成の骨子を生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀なプロのブロックチェーンリサーチャーです。"},
                {
                    "role": "user",
                    "content": f"以下の記事本文を基にレポートの骨子を日本語で提案してください。\n\n{text}\n\n"
                               "骨子には以下を含めてください:\n"
                               "- 背景\n"
                               "- 課題\n"
                               "- 解決策\n"
                               "- 結論"
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        report_outline = response["choices"][0]["message"]["content"].strip()
        return report_outline
    except Exception as e:
        print("Error in generate_report_outline:", e)
        return ""

def generate_insights_and_questions(text: str, max_tokens: int = 300, temperature: float = 0.7) -> str:
    """
    記事本文を基に考察の視点や問いを生成。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "あなたは優秀なプロのブロックチェーンリサーチャーです。"},
                {
                    "role": "user",
                    "content": f"以下の記事本文を基にレポート作成に必要な考察の視点や問いを日本語で提案してください。\n\n{text}"
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        insights_and_questions = response["choices"][0]["message"]["content"].strip()
        return insights_and_questions
    except Exception as e:
        print("Error in generate_insights_and_questions:", e)
        return ""
