import requests
import json
from datetime import datetime
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

def fetch_hackernews_top_stories(limit: int = 30) -> List[int]:
    """
    HackerNews APIから最新のトップストーリーを取得します。
    
    Args:
        limit: 取得する記事数（デフォルト30）
    
    Returns:
        List[int]: ストーリーIDのリスト
    """
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(url)
        response.raise_for_status()
        
        # 最大500件のIDリストが返ってくるので、指定された件数に制限
        story_ids = response.json()
        return story_ids[:limit]
    except Exception as e:
        print(f"❌ Error fetching HackerNews top stories: {str(e)}")
        return []

def extract_domain(url: str) -> str:
    """
    URLからドメイン名を抽出します。
    
    Args:
        url: 記事のURL
    
    Returns:
        str: ドメイン名（例: 'example.com'）
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # www.を削除
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return "Unknown"

def fetch_story_details(story_id: int) -> Optional[Dict[str, Any]]:
    """
    HackerNews APIから特定のストーリーの詳細を取得します。
    
    Args:
        story_id: ストーリーID
    
    Returns:
        Dict or None: ストーリー情報の辞書またはNone（エラー時）
    """
    try:
        url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        response = requests.get(url)
        response.raise_for_status()
        
        story = response.json()
        
        # 必須フィールドのチェック
        if not story or not story.get('title') or not story.get('url', story.get('text')):
            print(f"⚠️ Missing required fields for story ID {story_id}")
            return None
            
        # 'Ask HN'や'Show HN'のストーリーは'text'フィールドをコンテンツとして持つことがある
        content = story.get('text', '')
        if not content and 'url' in story:
            content = f"Original URL: {story['url']}"
        
        # 日付の変換（UnixタイムスタンプからDatetime）
        publish_date = None
        if 'time' in story:
            try:
                publish_date = datetime.fromtimestamp(story['time'])
            except (TypeError, ValueError) as e:
                print(f"⚠️ Error parsing date for story ID {story_id}: {e}")
        
        # URLからドメイン名を抽出
        url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
        source = extract_domain(url)
        
        # RSSフィードの形式に合わせて辞書を作成
        return {
            'title': story.get('title', ''),
            'link': url,
            'url': url,
            'summary': content,
            'published': publish_date,
            'source': source,  # ドメインを記事のソースとして使用
            'score': story.get('score', 0),
            'comments': story.get('descendants', 0)
        }
    except Exception as e:
        print(f"❌ Error fetching story details for ID {story_id}: {str(e)}")
        return None

def fetch_top_hackernews_stories(max_items: int = 5) -> List[Dict[str, Any]]:
    """
    HackerNews APIからトップストーリーとその詳細を取得します。
    
    Args:
        max_items: 取得する最大記事数（デフォルト5件）
    
    Returns:
        List[Dict]: ストーリー情報のリスト
    """
    print(f"\n🔍 Checking HackerNews top stories")
    
    # トップストーリーのIDを取得（多めに取得して、詳細フェッチでフィルタリング後に十分な数を確保）
    story_ids = fetch_hackernews_top_stories(limit=max_items * 3)
    
    if not story_ids:
        print("❌ Failed to fetch HackerNews story IDs")
        return []
        
    stories = []
    fetched_count = 0
    
    for story_id in story_ids:
        # 指定された数の有効なストーリーを取得できたら終了
        if fetched_count >= max_items:
            break
            
        story = fetch_story_details(story_id)
        if story:
            stories.append(story)
            fetched_count += 1
    
    print(f"📄 Found {len(stories)} valid stories from HackerNews")
    return stories 