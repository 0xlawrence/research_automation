#src/rss_fetch.py

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


def clean_domain(url: str) -> str:
    """
    URLからクリーンなドメイン名を抽出する。
    - www.を除去
    - substackの場合はサブドメインを保持
    - その他のドメインは通常通り処理
    """
    domain = url.split('/')[2]
    
    # www.を除去
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # サブドメインを保持するドメインのリスト
    keep_subdomain_domains = ['substack.com']
    
    # ドメインがkeep_subdomain_domainsのいずれかで終わる場合、サブドメインを保持
    for keep_domain in keep_subdomain_domains:
        if domain.endswith(keep_domain):
            return domain
    
    # それ以外の場合は、www.のみを除去して返す
    return domain


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
        
        # フィードのソース名を取得（ドメインをクリーンにする）
        source = clean_domain(feed_url)
        
        for entry in feed.entries[:max_items]:
            published = entry.published if 'published' in entry else ''
            published_dt = None
            
            if published:
                try:
                    # feedparserのパース結果をdatetimeオブジェクトに変換
                    published_dt = datetime(*entry.published_parsed[:6])
                except:
                    published_dt = None
            
            # 記事の要約を取得（descriptionまたはsummaryから）
            content = entry.get('description', '') or entry.get('summary', '')
            clean_content = remove_html_tags(content)
            
            items.append({
                'title': entry.title,
                'link': entry.link,
                'summary': clean_content,
                'published': published_dt,
                'source': source  # クリーンなドメインをソースとして使用
            })
            
        return items
    except Exception as e:
        print(f"Error fetching RSS feed {feed_url}:", e)
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
