from datetime import datetime
import logging
from typing import List, Dict
import time

# srcディレクトリからのインポート
from src.config import RSS_FEEDS, USE_DEEPSEEK, OPENAI_API_KEY
from src.rss_fetch import fetch_all_rss_items

# APIの切り替え
if not USE_DEEPSEEK:
    from src.openai_utils import (
        summarize_text,
        categorize_article_with_ai,
        generate_detailed_summary,
        generate_insights_and_questions,
        process_article_content
    )
else:
    # DeepSeek APIを使用
    from src.deepseek_utils import (
        summarize_text,
        categorize_article_with_ai,
        generate_detailed_summary,
        generate_insights_and_questions,
        process_article_content
    )

from src.scraper import fetch_article_content
from src.notion_utils import (
    create_notion_page, 
    append_page_content, 
    update_notion_status, 
    get_pages_by_status
)
from src.cache_utils import load_processed_urls, save_processed_url

def register_new_articles():
    """
    新しい記事をRSSフィードから取得し、Notionに登録。
    1. 各RSSフィードから最新5件を確認
    2. 未処理のURLのみを登録
    """
    print("\n📚 Starting to fetch articles from RSS feeds...")
    processed_urls = load_processed_urls()
    
    total_checked = 0
    total_new = 0
    
    for item in fetch_all_rss_items(RSS_FEEDS):
        total_checked += 1
        article_url = item.get("url") or item.get("link")
        if not article_url:
            print(f"❌ No URL found in item: {item}")
            continue
            
        if article_url.strip() in processed_urls:
            print(f"⏭️ Already processed: {item['title']}")
            continue
            
        try:
            # 記事の要約を生成
            content = item.get("summary", "")
            if not content:
                print(f"⚠️ No content found for: {article_url}")
                continue
                
            summary = summarize_text(content)
            if not summary:
                continue
                
            # Notionページを作成
            result = create_notion_page(
                title=item["title"],
                url=article_url,
                summary=summary,
                published_date=item.get("published"),
                source=item.get("source", "Unknown"),
                category=categorize_article_with_ai(item["title"], summary)
            )
            
            if result:  # Notionページの作成が成功した場合のみURLを保存
                save_processed_url(article_url.strip())
                total_new += 1
                print(f"✅ Registered: {item['title']}")
            else:
                print(f"⚠️ Failed to create Notion page for: {item['title']}")
            
        except Exception as e:
            print(f"❌ Error processing: {article_url} - {str(e)}")
    
    print(f"\n📊 Summary:")
    print(f"- Checked articles: {total_checked}")
    print(f"- New articles registered: {total_new}")

def process_pending_articles():
    """
    `Processing` ステータスの記事を処理。
    """
    print("\n📝 Fetching Notion pages with 'Processing' status...")
    pages = get_pages_by_status("Processing")
    
    if not pages:
        print("No articles with 'Processing' status found.")
        return
        
    print(f"Found {len(pages)} articles to process.")
    
    for page in pages:
        try:
            # Notionページのプロパティから必要な情報を取得
            title = page["properties"]["Name"]["title"][0]["text"]["content"]
            url = page["properties"]["URL"]["url"]
            
            print(f"\n🔍 Processing: {title}")
            
            # 記事本文を取得
            content = fetch_article_content(url)
            if not content:
                print(f"⚠️ No content fetched for: {title}")
                continue
            
            # process_article_contentを使用して処理
            if process_article_content(page["id"], content):
                print(f"✅ Successfully processed: {title}")
            else:
                print(f"⚠️ Failed to process: {title}")
            
            # API制限を考慮して待機
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing page {page.get('id', 'unknown')}: {str(e)}")
            continue

def main():
    """
    メイン処理
    1. 新しい記事の登録
    2. 保留中の記事の処理
    """
    register_new_articles()
    process_pending_articles()

if __name__ == "__main__":
    main()