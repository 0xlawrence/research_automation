# main.py

import sys
import os
from datetime import datetime

# src ディレクトリをモジュール検索パスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import RSS_FEEDS
from src.rss_fetch import fetch_all_rss_items
from src.openai_utils import summarize_text, categorize_article_with_ai, generate_detailed_summary, generate_report_outline, generate_insights_and_questions
from src.scraper import fetch_article_content
from src.notion_utils import create_notion_page, append_page_content, update_notion_status, get_pages_by_status
from src.cache_utils import load_processed_urls, save_processed_url

def register_new_articles():
    """
    RSSフィードから新しい記事を取得して、Notionページを `Not Started` ステータスで作成。
    """
    print("Fetching articles from RSS feeds...")
    articles = fetch_all_rss_items(RSS_FEEDS)

    # 処理済みURLを読み込む
    processed_urls = load_processed_urls()

    for article in articles:
        url = article["link"]
        if url in processed_urls:
            print(f"Skipping already processed article: {url}")
            continue

        # 記事の情報を取得
        title = article["title"]
        raw_summary = article.get("summary", "No summary available.")
        published_date = article.get("published")
        
        # 高品質な要約を生成
        summary = summarize_text(raw_summary)

        # カテゴリを自動割り当て
        category = categorize_article_with_ai(title, summary, max_tokens=10)

        # Notionページを作成
        create_notion_page(
            title=title,
            url=url,
            summary=summary,  # AI生成の要約を渡す
            published_date=published_date,
            source=article.get("source"),
            category=category  # 新たにカテゴリを追加
        )

        # 処理済みURLとして保存
        save_processed_url(url)

    print("All new articles have been registered with 'Not Started' status.")


def process_articles():
    """
    ステータスが `Processing` の記事を処理し、Notionページを更新。
    """
    print("Fetching Notion pages with 'Processing' status...")
    pages = get_pages_by_status("Processing")

    for page in pages:
        try:
            page_id = page["id"]
            title = page["properties"]["Name"]["title"][0]["text"]["content"]
            url = page["properties"]["URL"]["url"]

            print(f"Fetching content for: {title}")
            article_content = fetch_article_content(url)

            print(f"Generating AI summaries for: {title}")
            detailed_summary = generate_detailed_summary(article_content)
            report_outline = generate_report_outline(article_content)
            insights_and_questions = generate_insights_and_questions(article_content)

            # ページ内容をMarkdown形式でフォーマット
            append_page_content(page_id, f"# 詳細なサマリー\n{detailed_summary}")
            append_page_content(page_id, f"# レポートの骨子\n{report_outline}")
            append_page_content(page_id, f"# 考察の視点と問い\n{insights_and_questions}")

            # ステータスを "Completed" に更新
            update_notion_status(page_id, "Completed")
            print(f"Processing completed for: {title}")

        except Exception as e:
            print(f"Error processing page ID {page['id']}: {e}")

if __name__ == "__main__":
    # RSSフィードから記事を登録
    register_new_articles()
    # ステータスが `Processing` の記事を処理
    process_articles()
