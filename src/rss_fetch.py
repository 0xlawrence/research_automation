import feedparser
from datetime import datetime
from html.parser import HTMLParser


class HTMLTagRemover(HTMLParser):
    """
    HTMLタグを除去するクラス
    """
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_clean_text(self):
        return ''.join(self.text)


def remove_html_tags(html_content: str) -> str:
    """
    HTMLタグを除去する関数
    Args:
        html_content (str): HTMLコンテンツ
    Returns:
        str: HTMLタグが除去されたテキスト
    """
    parser = HTMLTagRemover()
    parser.feed(html_content)
    return parser.get_clean_text()


def fetch_rss_items(feed_url: str, max_items: int = 5):
    """
    指定したRSSフィードURLから最新の記事を取得しリストとして返す。
    Args:
        feed_url (str): RSSフィードのURL
        max_items (int): 最大取得記事数
    Returns:
        list: 記事情報のリスト
    """
    try:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            published = entry.published if 'published' in entry else ''
            published_dt = None
            if published:
                try:
                    published_dt = datetime(*entry.published_parsed[:6])
                except Exception as e:
                    print(f"Error parsing published date: {e}")

            # サマリーのHTMLタグを除去
            summary = entry.get("summary", "")
            clean_summary = remove_html_tags(summary)

            items.append({
                "title": entry.title,
                "link": entry.link,
                "published": published_dt,
                "summary": clean_summary,
            })
        return items
    except Exception as e:
        print(f"Error fetching RSS items from {feed_url}: {e}")
        return []


def fetch_all_rss_items(feed_urls):
    """
    複数のRSSフィードURLから記事を取得してまとめて返す。
    Args:
        feed_urls (list): RSSフィードのURLリスト
    Returns:
        list: 記事情報をまとめたリスト
    """
    all_items = []
    for url in feed_urls:
        if not isinstance(url, str):
            print(f"Invalid URL: {url} (type: {type(url)})")
            continue

        print(f"Fetching articles from: {url}")
        try:
            items = fetch_rss_items(url, max_items=5)
            all_items.extend(items)
        except Exception as e:
            print(f"Error fetching articles from {url}: {e}")
    return all_items
