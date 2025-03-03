from openai import OpenAI
from .config import DEEPSEEK_API_KEY
from .notion_utils import append_page_content, update_notion_status
from typing import List, Dict
from .ai_client import ai_client  # 新しいAIクライアントをインポート

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
        messages = [
            {
                "role": "user",
                "content": (
                    "以下の文章を200文字程度の日本語で要点整理をしてください。\n"
                    "箇条書きではなく、1文ごとを短くして読みやすい文章として構成してください。\n\n"
                    f"文章:\n{text}"
                )
            }
        ]
        
        response = ai_client.call_api(
            messages=messages,
            max_tokens=max_tokens,
            **COMPLETION_PARAMS
        )
        
        if response.choices and hasattr(response.choices[0].message, "content"):
            return response.choices[0].message.content.strip()
        else:
            print("ERROR: DeepSeek APIのレスポンスに 'content' フィールドがありません。")
            print("Response Details:", response)
            return ""
    except Exception as e:
        print(f"DeepSeek API Error in summarize_text: {e}")
        return ""

def chunk_text(text: str, max_chars: int = 4000) -> List[str]:
    """
    テキストを指定された最大文字数で分割する。
    文章の途中で分割されないように、段落や文の区切りで分割する。
    """
    if not text or not isinstance(text, str):
        print("Invalid input text for chunking")
        return []
        
    try:
        chunks = []
        current_chunk = ""
        
        # 段落ごとに分割（空行で区切る）
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # 段落が空でないことを確認
            if not paragraph.strip():
                continue
                
            # 現在のチャンクに段落を追加した場合の長さをチェック
            if len(current_chunk) + len(paragraph) < max_chars:
                current_chunk += paragraph + '\n\n'
            else:
                # 現在のチャンクが存在する場合、それを保存
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
        
        # 最後のチャンクを追加
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # チャンクが生成されなかった場合、元のテキストを1つのチャンクとして返す
        if not chunks and text.strip():
            return [text.strip()]
            
        return chunks
        
    except Exception as e:
        print(f"Error in chunk_text: {e}")
        # エラーが発生した場合、元のテキストを1つのチャンクとして返す
        return [text] if text.strip() else []

def generate_detailed_summary(text: str, max_tokens: int = 2000) -> str:
    """
    DeepSeek Reasonerを使用して詳細なサマリーを生成する。
    チャンク処理を使わない簡素化された実装。
    """
    try:
        print("Starting generate_detailed_summary with DeepSeek...")
        
        if not text or not isinstance(text, str):
            print("Invalid input text for DeepSeek summary")
            return ""
            
        client = get_client()
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "# Role and Expertise\n"
                        "You are an expert analyst specializing in blockchain, cryptocurrency, and AI technologies. Your analysis is known for:\n"
                        "- Exceptional depth and clarity when explaining complex technical concepts\n"
                        "- Identifying the most significant aspects of innovations and developments\n"
                        "- Connecting technological advancements to business implications and market trends\n"
                        "- Providing balanced perspectives on advantages, limitations, and future potentials\n\n"
                        "# Output Format\n"
                        "Your analysis must be in Japanese, structured with the following sections:\n\n"
                        "## 背景と文脈 (Background and Context)\n"
                        "- The historical or technological context necessary to understand the article\n"
                        "- The key problems or opportunities being addressed\n"
                        "- Relevant previous developments or competing solutions\n\n"
                        "## 技術的概要 (Technical Overview)\n"
                        "- The core technology or approach in clear, accessible language\n"
                        "- Key innovations or differentiating factors\n"
                        "- The architecture, methodology, or implementation when relevant\n\n"
                        "## 市場への影響 (Market Impact)\n"
                        "- Potential effects on industry, competition, and user adoption\n"
                        "- Stakeholders who benefit or may be challenged\n"
                        "- Short and long-term implications for the ecosystem\n\n"
                        "## 展望と課題 (Future Outlook and Challenges)\n"
                        "- Potential evolution of the technology or solution\n"
                        "- Obstacles, limitations, or risks\n"
                        "- Regulatory, technical, or adoption challenges\n\n"
                        "## 結論 (Conclusion)\n"
                        "- A balanced final assessment\n"
                        "- The most important implications\n"
                        "- What readers should particularly pay attention to going forward\n\n"
                        "Important: Your analysis should be informative, insightful, and nuanced - never promotional or superficial."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the following article and create a comprehensive, structured summary according to the specified format.\n\n"
                        "The analysis should be informative and insightful, focusing on key technological aspects, business implications, and future potential. "
                        "Ensure your output is in Japanese, well-structured, and provides valuable insights for readers interested in blockchain, cryptocurrency, or AI technologies.\n\n"
                        f"Article text:\n{text}\n\n"
                        "Remember to maintain a balanced perspective, discussing both strengths and limitations, while providing context that helps readers understand the significance of the topic."
                    )
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        # レスポンスの検証（堅牢性強化）
        if not response:
            print("Empty response from DeepSeek API")
            return "DeepSeekからの応答が空でした。"
            
        if not hasattr(response, 'choices') or not response.choices:
            print("No choices in DeepSeek response")
            return "DeepSeekからの応答に選択肢がありませんでした。"
            
        try:
            # content属性が存在するか確認
            if not hasattr(response.choices[0].message, 'content'):
                print("No content attribute in DeepSeek response")
                return "DeepSeekからの応答にcontent属性がありませんでした。"
                
            content = response.choices[0].message.content
            
            # contentがNoneの場合
            if content is None:
                print("Content is None in DeepSeek response")
                return "DeepSeekからの応答がNullでした。"
                
            # contentが文字列でない場合
            if not isinstance(content, str):
                print(f"Content is not a string: {type(content)}")
                # 文字列に変換を試みる
                try:
                    content = str(content)
                except:
                    return "DeepSeekからの応答を文字列に変換できませんでした。"
                
            content = content.strip()
            
            # 内容が空の場合
            if not content:
                print("Empty content after stripping")
                return "DeepSeekからの応答が空文字でした。"
                
            # 品質チェック
            if len(content) < 100:
                print("Content too short, quality check failed")
                return "DeepSeekからの応答が短すぎます。十分な分析情報が含まれていません。"
                
            print("Successfully generated detailed summary with DeepSeek")
            return content
            
        except Exception as e:
            print(f"Error processing DeepSeek response: {e}")
            return f"DeepSeek応答の処理中にエラーが発生しました: {str(e)}"
            
    except Exception as e:
        print(f"DeepSeek API Error in generate_detailed_summary: {e}")
        return f"DeepSeek API呼び出し中にエラーが発生しました: {str(e)}"

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

def generate_insights_and_questions(text: str, max_tokens: int = 8000) -> str:
    """DeepSeek Reasonerを使用して洞察と質問を生成。長いテキストは分割して処理。"""
    system_prompt = """# 分析の目的
ブロックチェーン技術と市場に関する深い洞察を提供し、重要な問いを提起する。

# 分析の観点
1. 技術的革新性
   - 既存技術との比較
   - 技術的な優位性
   - 実装上の課題

2. 市場インパクト
   - 既存市場への影響
   - 新規市場の創出可能性
   - 競合状況の変化

3. 社会的影響
   - ユーザーへの影響
   - 規制環境との関係
   - 社会システムへの影響

# 出力形式
## 重要な洞察
- 技術的ブレークスルーの詳細分析
- 市場構造の変化と意味
- 社会的インパクトの考察

## 重要な検討課題
- 技術的課題と解決の方向性
- ビジネス上の課題と対応策
- 規制・法制度の課題と提言

# 品質基準
1. 具体的な事例や数値を含める
2. 複数の視点から分析
3. 予測には根拠を示す
4. 技術と事業の関連性を明確に
5. 課題に対する解決の方向性を示唆"""

    try:
        # テキストを適切な長さに分割
        chunks = chunk_text(text)
        all_insights = []
        
        for i, chunk in enumerate(chunks):
            response = get_client().chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": f"""以下の記事（パート{i+1}/{len(chunks)}）について分析を行い、
必ず指定された出力形式に従い、各セクションを明確に区分けしてください。
特に以下の点に注意して洞察と重要な問いを生成してください：

1. 技術的な詳細の深掘り
2. 市場への影響の多角的分析
3. 社会的インパクトの考察
4. 具体的な課題の特定と解決の方向性

記事：
{chunk}"""
                    }
                ],
                max_tokens=max_tokens // len(chunks),
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3
            )
            
            content = response.choices[0].message.content.strip()
            all_insights.append(content)
        
        # 全ての洞察を統合
        combined_insights = "\n\n".join(all_insights)
        
        # 品質チェック
        if not validate_content_quality(combined_insights):
            print("Content quality check failed. Retrying with adjusted parameters...")
            return generate_insights_and_questions(text, max_tokens)
            
        return combined_insights
    except Exception as e:
        print(f"Error in generate_insights_and_questions: {e}")
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
                {
                    "role": "user",
                    "content": (
                        f"以下の記事を{', '.join(EXISTING_CATEGORIES)}のいずれかに分類してください。\n"
                        "80%以上の確信度がない場合は「Other」を返してください。\n"
                        "カテゴリ名のみを返してください。\n\n"
                        f"タイトル: {title}\n"
                        f"要約: {summary}"
                    )
                }
            ],
            max_tokens=max_tokens
        )
        
        print("\n=== Reasoning Process (Categorization) ===")
        try:
            print(response.choices[0].message.reasoning_content)
        except AttributeError:
            print("No reasoning content available")
        print("======================================\n")
        
        if response.choices and hasattr(response.choices[0].message, "content"):
            category = response.choices[0].message.content.strip()
            return category if category in EXISTING_CATEGORIES else "Other"
        else:
            print("ERROR: DeepSeek APIのカテゴリ分類レスポンスに 'content' フィールドがありません。")
            print("Response Details:", response)
            return "Other"
    except Exception as e:
        print(f"DeepSeek API Error in categorize_article_with_ai: {e}")
        return "Other"

def transform_title(title: str, max_tokens: int = 40, retries: int = 3) -> str:
    """
    DeepSeek API を利用して記事タイトルを、より魅力的かつ印象的で凝縮されたタイトルに変換する。
    出力は変換後のタイトルのみで、元のタイトルと同一の場合は再試行する。
    """
    for attempt in range(retries):
        try:
            client = get_client()
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
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
                ],
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

def generate_executive_summary(text: str, max_tokens: int = 1000) -> str:
    """
    DeepSeek API を利用して、記事内容からエグゼクティブサマリーを生成する。
    エグゼクティブサマリーは記事の主要なポイント、背景、影響、展望を包括的にまとめた内容。
    """
    try:
        client = get_client()
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert analyst. Generate a comprehensive executive summary that includes:\n"
                        "1. The core message and key points\n"
                        "2. Industry context and background\n"
                        "3. Potential impact and implications\n"
                        "4. Future outlook\n"
                        "Make it more detailed and insightful than a basic summary, "
                        "but still concise and easy to understand.\n"
                        "Please provide the output entirely in Japanese."
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
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error in generate_executive_summary:", e)
        return ""

def process_article_content(page_id: str, content: str) -> bool:
    """記事内容を段階的に分析し、より深い洞察を生成する"""
    try:
        # 1. 技術的分析
        technical_analysis = analyze_technical_aspects(content)
        
        # 2. 市場分析
        market_analysis = analyze_market_impact(content)
        
        # 3. 社会的影響分析
        social_impact = analyze_social_impact(content)
        
        # 4. 総合的な洞察と質問の生成
        insights_and_questions = generate_insights_and_questions(content)
        
        # 最終的なコンテンツの構築
        final_content = f"""# 総合分析レポート

## 技術的分析
{technical_analysis}

## 市場分析
{market_analysis}

## 社会的影響
{social_impact}

## 重要な洞察と検討課題
{insights_and_questions}
"""
        
        # Notionページの更新
        append_page_content(page_id, final_content)
        update_notion_status(page_id, "Completed")
        return True
        
    except Exception as e:
        print(f"Error in process_article_content: {e}")
        update_notion_status(page_id, "Error")
        return False

def analyze_technical_aspects(text: str) -> str:
    """技術的側面の詳細な分析を生成"""
    system_prompt = """技術的な観点から以下の点を分析してください：
1. 技術的革新性
2. 実装上の特徴
3. 技術的課題
4. 解決策の提案
5. 将来の技術的展望"""
    
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"技術的分析対象：\n{text}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in analyze_technical_aspects: {e}")
        return ""

def analyze_market_impact(text: str) -> str:
    """市場への影響の詳細な分析を生成"""
    system_prompt = """市場への影響について以下の点を分析してください：
1. 既存市場への影響
2. 新規市場の創出可能性
3. 競合状況の変化
4. ビジネスモデルの特徴
5. 収益性と持続可能性"""
    
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"市場分析対象：\n{text}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in analyze_market_impact: {e}")
        return ""

def analyze_social_impact(text: str) -> str:
    """社会的影響の詳細な分析を生成"""
    system_prompt = """社会的影響について以下の点を分析してください：
1. ユーザーへの影響
2. 規制環境との関係
3. 社会システムへの影響
4. 倫理的な考慮事項
5. 長期的な社会変革の可能性"""
    
    try:
        response = get_client().chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"社会的影響分析対象：\n{text}"}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in analyze_social_impact: {e}")
        return "" 