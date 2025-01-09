import requests
from bs4 import BeautifulSoup

def fetch_article_content(url: str) -> str:
    """
    指定されたURLから記事本文をスクレイピングして取得。
    - 記事の本文が見つからない場合はエラーメッセージを返す。
    
    Args:
        url (str): スクレイピング対象のURL。
    
    Returns:
        str: 記事本文のテキスト。
    """
    try:
        # HTTPリクエストを送信
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # HTTPステータスコードがエラーの場合、例外をスロー

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.content, "html.parser")

        # 記事本文を抽出するロジック（例: <div class="article-body">）
        # 各サイトのHTML構造に合わせて調整が必要
        article_body = soup.find("div", class_="article-body")  # 例: `<div class="article-body">`
        if article_body:
            return article_body.get_text(strip=True)

        # 他の可能性（例: <p> タグ内のテキストをすべて結合）
        paragraphs = soup.find_all("p")
        if paragraphs:
            return "\n".join([p.get_text(strip=True) for p in paragraphs])

        # 本文が取得できなかった場合
        return "記事本文が見つかりませんでした。"

    except requests.exceptions.RequestException as e:
        # ネットワーク関連のエラー処理
        print(f"HTTPリクエストエラー: {e}")
        return "HTTPリクエストエラーが発生しました。"

    except Exception as e:
        # その他のエラー処理
        print(f"スクレイピングエラー: {e}")
        return "スクレイピングエラーが発生しました。"
