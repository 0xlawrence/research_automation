#!/usr/bin/env python3
from datetime import datetime
import logging
from typing import List, Dict
import time
import os
from dotenv import load_dotenv
import sys  # sys モジュールをインポート

# 相対インポートに変更
from .config import RSS_FEEDS, USE_DEEPSEEK, OPENAI_API_KEY  

# ユーティリティのインポート
from .rss_fetch import fetch_all_rss_items
from .hackernews_fetch import fetch_top_hackernews_stories
from .ai_client import ai_client  # 統一されたAIクライアント

# OpenAIユーティリティから関数をインポート
from .openai_utils import (
    summarize_text,
    categorize_article_with_ai,
    generate_detailed_summary,
    generate_insights_and_questions,
    process_article_content,
    transform_title
)

# APIの使用状況を表示
print(f"Using {'DeepSeek' if USE_DEEPSEEK else 'OpenAI'} API for content processing")
if not USE_DEEPSEEK:
    print(f"OpenAI API Key configured: {bool(OPENAI_API_KEY)}")

from .scraper import fetch_article_content
from .notion_utils import (
    create_notion_page, 
    append_page_content, 
    update_notion_status, 
    get_pages_by_status
)
from .cache_utils import load_processed_urls, save_processed_url

def register_new_articles():
    """
    新しい記事をRSSフィードとHackerNewsから取得し、Notionに登録。
    1. 各RSSフィードから最新5件を確認
    2. HackerNewsから最新5件を確認
    3. 未処理のURLのみを登録
    4. AI処理ステータスを指定
    """
    print("\n📚 Starting to fetch articles from RSS feeds...")
    processed_urls = load_processed_urls()
    
    total_checked = 0
    total_new = 0
    
    # RSSフィードからの記事取得
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
                
            # 元記事のタイトルを変換
            raw_title = item["title"]
            refined_title = transform_title(raw_title)
            
            # Notionページを作成
            result = create_notion_page(
                title=refined_title,
                url=article_url,
                summary=summary,
                published_date=item.get("published"),
                source=item.get("source", "Unknown"),
                category=categorize_article_with_ai(raw_title, summary)
            )
            
            if result:  # Notionページの作成が成功した場合のみURLを保存
                save_processed_url(article_url.strip())
                total_new += 1
                print(f"✅ Registered: {item['title']}")
            else:
                print(f"⚠️ Failed to create Notion page for: {item['title']}")
            
        except Exception as e:
            print(f"❌ Error processing: {article_url} - {str(e)}")
    
    # HackerNewsからの記事取得
    print("\n📚 Fetching articles from HackerNews...")
    for item in fetch_top_hackernews_stories(max_items=10):  # 一時的に10件に増やす
        total_checked += 1
        article_url = item.get("url") or item.get("link")
        if not article_url:
            print(f"❌ No URL found in HackerNews item: {item}")
            continue
            
        if article_url.strip() in processed_urls:
            print(f"⏭️ Already processed: {item['title']}")
            continue
            
        try:
            # 記事の要約を生成
            content = item.get("summary", "")
            if not content:
                # HackerNewsの場合、コンテンツが空の場合があるため、最低限の情報を追加
                content = f"HackerNews Score: {item.get('score', 0)}, Comments: {item.get('comments', 0)}"
                
            summary = summarize_text(content)
            if not summary:
                # 要約に失敗した場合でも、最低限の情報で要約を作成
                summary = f"HackerNews discussion with {item.get('comments', 0)} comments and {item.get('score', 0)} points."
                
            # 元記事のタイトルを変換
            raw_title = item["title"]
            refined_title = transform_title(raw_title)
            
            # Notionページを作成
            result = create_notion_page(
                title=refined_title,
                url=article_url,
                summary=summary,
                published_date=item.get("published"),
                source=item.get("source", "Unknown"),  # ドメイン名をソースとして使用
                category=categorize_article_with_ai(raw_title, summary)
            )
            
            if result:  # Notionページの作成が成功した場合のみURLを保存
                save_processed_url(article_url.strip())
                total_new += 1
                print(f"✅ Registered from HackerNews: {item['title']}")
                
                # AI処理を自動的に開始する場合はここでステータスを更新
                update_notion_status(result["id"], "Processing")
            else:
                print(f"⚠️ Failed to create Notion page for HackerNews item: {item['title']}")
            
        except Exception as e:
            print(f"❌ Error processing HackerNews item: {item.get('title', 'Unknown')} - {str(e)}")
    
    print(f"\n📊 Summary:\n- Checked articles: {total_checked}\n- New articles registered: {total_new}")

def process_pending_articles():
    """
    `Processing` ステータスの記事を処理。
    HackerNewsの記事も含めて処理します。
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
            
            # 処理ステータスを更新
            update_notion_status(page["id"], "Processing")
            print("Successfully updated status to: Processing")
            
            # 記事本文を取得
            content = fetch_article_content(url)
            if not content:
                print(f"⚠️ No content fetched for: {title}")
                update_notion_status(page["id"], "Error")
                continue
                
            print(f"Fetched {len(content)} characters of content")
            
            # 記事が長すぎる場合は切り詰める
            if len(content) > 50000:
                print("Content too long, truncating to 50000 characters")
                content = content[:50000] + "...[truncated due to length]"
            
            # process_article_contentを使用して処理
            print("Generating initial summary...")
            processing_result = process_article_content(page["id"], content)
            
            if processing_result:
                update_notion_status(page["id"], "Completed")
                print(f"✅ Successfully processed: {title}")
            else:
                update_notion_status(page["id"], "Error")
                print(f"⚠️ Failed to process: {title}")
            
            # API制限を考慮して待機
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Error in process_pending_articles: {e}")
            if 'page' in locals():
                update_notion_status(page["id"], "Error")

def main():
    """
    メイン処理
    1. 新しい記事の登録
    2. 保留中の記事の処理
    """
    # DryRunモードの判定
    if "--dry-run" in sys.argv:
        print("⚠️ Running in DRY RUN mode - no actual API calls will be made")
        return
        
    register_new_articles()
    process_pending_articles()

if __name__ == "__main__":
    main()