from openai import OpenAI
from src.config import DEEPSEEK_API_KEY  # 必要な設定のみインポート
from src.notion_utils import append_page_content, update_notion_status
from typing import List, Dict

# クライアントを遅延初期化するための関数
def get_client():
    if not hasattr(get_client, '_client'):
        get_client._client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
    return get_client._client

# 共通のパラメータ設定
COMPLETION_PARAMS = {
    "temperature": 0.7,  # 適度な具体性と創造性のバランス
    "presence_penalty": 0.1,  # 同じ内容の繰り返しを抑制
    "frequency_penalty": 0.1,  # 単調な表現の繰り返しを抑制
}

def summarize_text(text: str, max_tokens: int = 4000) -> str:
    """DeepSeek Reasonerを使用して短い要約を生成。"""
    try:
        # クライアントを関数内で取得
        client = get_client()
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "user",
                 "content": (
                    "以下の文章を200文字程度の日本語で要点整理をしてください。\n"
                    "箇条書きではなく、1文ごとを短くして読みやすい文章として構成してください。\n\n"
                    f"文章:\n{text}"
                 )}
            ],
            max_tokens=max_tokens
        )
        
        print("\n=== Reasoning Process (Summarize) ===")
        print(response.choices[0].message.reasoning_content)
        print("===================================\n")
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"DeepSeek API Error in summarize_text: {e}")
        return ""

def generate_detailed_summary(text: str, max_tokens: int = 6000) -> str:
    """DeepSeek Reasonerを使用して詳細なサマリーを生成。"""
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system",
                 "content": (
                    "# Goal\n"
                    "Analyze the given text comprehensively and organize key points in an easy-to-understand format.\n\n"
                    "# Return Format\n"
                    "Divide into 3 main sections, each with an introduction and 2-3 key points.\n"
                    "Use # for headings and - for bullet points.\n\n"
                    "Never use ** for emphasis.\n\n"
                    "# Warnings\n"
                    "- Include sufficient context for each point\n"
                    "- Focus on a small number of important points\n"
                    "- Explain technical terms appropriately\n"
                    "- Provide the final output in Japanese"
                 )
                },
                {"role": "user",
                 "content": (
                    "Analyze the following text and provide a summary in Japanese with this structure:\n\n"
                    "# 背景と概要\n"
                    "(Analysis of industry context and historical background)\n\n"
                    "# 主要な特徴と影響\n"
                    "(Analysis of technical and business significance)\n\n"
                    "# 展望と課題\n"
                    "(Analysis of future possibilities and challenges)\n\n"
                    f"Text to analyze:\n{text}"
                 )}
            ],
            max_tokens=max_tokens
        )
        
        print("\n=== Reasoning Process (Detailed Summary) ===")
        print(response.choices[0].message.reasoning_content)
        print("=========================================\n")
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"DeepSeek API Error in generate_detailed_summary: {e}")
        return ""

def generate_report_outline(text: str, max_tokens: int = 5000) -> str:
    """DeepSeek Reasonerを使用してレポートアウトラインを生成。"""
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system",
                 "content": (
                    "# Goal\n"
                    "Create a high-level report structure that:\n"
                    "- Captures key themes and arguments\n"
                    "- Shows main logical connections\n"
                    "- Maintains strategic perspective\n"
                    "- Avoids excessive detail\n\n"
                    "# Writing Style\n"
                    "- Use clear section introductions\n"
                    "- Focus on main points only\n"
                    "- Keep hierarchy simple\n"
                    "- Maintain strategic view\n\n"
                    "# Format Rules\n"
                    "- Use ## for main sections\n"
                    "- Use ### for key subsections\n"
                    "- Use - for main points\n"
                    "- Use  - for supporting points (indented)\n"
                    "- Use 「」 for emphasis (never use **)\n\n"
                    "# Critical Requirements\n"
                    "- Write in Japanese (think in English)\n"
                    "- Keep structure high-level\n"
                    "- Focus on key insights\n"
                    "- Maintain clarity\n"
                    "- Avoid excessive detail"
                 )
                },
                {"role": "user",
                 "content": (
                    "Create a strategic report outline with this structure:\n\n"
                    "## 論点の整理\n"
                    "(記事の主要な論点と背景)\n"
                    "- 主要な議論\n"
                    "  - 中心的な主張\n"
                    "  - 重要な前提条件\n\n"
                    "## 分析の視点\n"
                    "(分析アプローチの概要)\n"
                    "- 重要な観点\n"
                    "  - 市場的視点\n"
                    "  - 技術的視点\n\n"
                    "## 重要な示唆\n"
                    "- 市場への影響\n"
                    "  - 主要なインパクト\n"
                    "  - 今後の展開\n"
                    "- 対応の方向性\n"
                    "  - 検討すべき施策\n"
                    "  - 留意すべき課題\n\n"
                    f"Text to analyze:\n{text}"
                 )}
            ],
            **COMPLETION_PARAMS,
            max_tokens=max_tokens
        )
        
        print("\n=== Reasoning Process (Report Outline) ===")
        print(response.choices[0].message.reasoning_content)
        print("======================================\n")
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"DeepSeek API Error in generate_report_outline: {e}")
        return ""

def generate_insights_and_questions(text: str, max_tokens: int = 5000) -> str:
    """DeepSeek Reasonerを使用して洞察と質問を生成。"""
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system",
                 "content": (
                    "# Goal\n"
                    "Generate deep insights and meaningful questions that:\n"
                    "- Reveal underlying patterns and implications\n"
                    "- Connect different aspects of the topic\n"
                    "- Challenge assumptions constructively\n"
                    "- Suggest new directions for inquiry\n\n"
                    "# Writing Style\n"
                    "- Use well-structured paragraphs (3-5 sentences each)\n"
                    "- Insert a line break when a paragraph exceeds 500 Japanese characters\n"
                    "- Ensure the break comes at a natural point in the discussion\n"
                    "- Maintain logical connection before and after the break\n"
                    "- Keep paragraph lengths balanced (250-500 characters ideal)\n\n"
                    "# Format Rules\n"
                    "- Use ## for main sections\n"
                    "- Use ### for subsections\n"
                    "- Use 「」 for emphasis (never use **)\n"
                    "- Use paragraphs as primary structure\n"
                    "- Add single line break for long paragraphs\n"
                    "- Reserve lists only for truly sequential items\n\n"
                    "# Critical Requirements\n"
                    "- Write in Japanese (think in English)\n"
                    "- Maintain analytical depth\n"
                    "- Support insights with evidence\n"
                    "- Ask probing questions\n"
                    "- Keep formatting minimal\n"
                    "- Break long paragraphs at natural points"
                 )
                },
                {"role": "user",
                 "content": (
                    "Analyze the text and provide insights and questions with this structure:\n\n"
                    "## 重要な洞察\n"
                    "(発見事項の意義と背景)\n\n"
                    "### 市場と事業への示唆\n"
                    "(市場構造の変化と意味)\n\n"
                    "### 技術と実装の方向性\n"
                    "(技術進化の文脈理解)\n\n"
                    "## 探求すべき課題\n"
                    "### 短期的な検討事項\n"
                    "(直近の重要課題の構造)\n\n"
                    "### 長期的な展望\n"
                    "(将来シナリオの展開)\n\n"
                    f"Text to analyze:\n{text}"
                 )}
            ],
            **COMPLETION_PARAMS,
            max_tokens=max_tokens
        )
        
        print("\n=== Reasoning Process (Insights & Questions) ===")
        print(response.choices[0].message.reasoning_content)
        print("============================================\n")
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"DeepSeek API Error in generate_insights_and_questions: {e}")
        return ""

def categorize_article_with_ai(title: str, summary: str, max_tokens: int = 100) -> str:
    """DeepSeek Reasonerを使用してカテゴリを推定。"""
    EXISTING_CATEGORIES = {
        "Blockchain", "Market", "Regulation", 
        "AI", "Security", "DeFi", "NFT",
        "Layer1", "Layer2", "DAO", "Bridge", "Social",
        "Gaming", "Metaverse", "Privacy", "Identity",
        "Product", "Development", "Airdrop", "Economy",
        "Funding",
    }
    
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "user",
                 "content": (
                    f"以下の記事を{', '.join(EXISTING_CATEGORIES)}のいずれかに分類してください。\n"
                    "80%以上の確信度がない場合は「Other」を返してください。\n"
                    "カテゴリ名のみを返してください。\n\n"
                    f"タイトル: {title}\n"
                    f"要約: {summary}"
                 )}
            ],
            max_tokens=max_tokens
        )
        
        print("\n=== Reasoning Process (Categorization) ===")
        print(response.choices[0].message.reasoning_content)
        print("======================================\n")
        
        category = response.choices[0].message.content.strip()
        return category if category in EXISTING_CATEGORIES else "Other"
            
    except Exception as e:
        print(f"DeepSeek API Error in categorize_article_with_ai: {e}")
        return "Other"

def process_article_content(page_id: str, content: str) -> bool:
    """
    記事本文を処理し、結果をNotionページに追加。
    """
    try:
        # 詳細なサマリーを生成
        detailed_summary = generate_detailed_summary(content)
        if detailed_summary:
            append_page_content(page_id, "# Detailed Summary\n" + detailed_summary)
        
        # インサイトと問いを生成
        insights = generate_insights_and_questions(content)
        if insights:
            append_page_content(page_id, "\n# Insights and Questions\n" + insights)
        
        # 処理完了後、ステータスを更新
        update_notion_status(page_id, "Completed")
        return True
        
    except Exception as e:
        print(f"Error in process_article_content: {e}")
        update_notion_status(page_id, "Failed")
        return False 