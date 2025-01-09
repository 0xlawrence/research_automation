from dotenv import load_dotenv
import os

# .envの読み込み
load_dotenv()

# 環境変数を取得
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 必須の環境変数が設定されているか確認
if not NOTION_TOKEN:
    raise EnvironmentError("環境変数 'NOTION_TOKEN' が設定されていません。 .envファイルを確認してください。")
if not NOTION_DATABASE_ID:
    raise EnvironmentError("環境変数 'NOTION_DATABASE_ID' が設定されていません。 .envファイルを確認してください。")
if not OPENAI_API_KEY:
    raise EnvironmentError("環境変数 'OPENAI_API_KEY' が設定されていません。 .envファイルを確認してください。")

# 収集対象のRSSフィードを定義
RSS_FEEDS = [
    "https://wublock.substack.com/feed",
    "https://parsec.substack.com/feed",
    "https://www.decentralised.co/feed",
    "https://blockworks.co/feed",
    "https://www.onchaintimes.com/rss/",
    # 必要に応じて追加
]

# 必要であれば外部ファイルや環境変数からRSSフィードを取得する方法も提供
ADDITIONAL_RSS_FEEDS = os.getenv("ADDITIONAL_RSS_FEEDS")  # カンマ区切りでフィードを指定可能
if ADDITIONAL_RSS_FEEDS:
    RSS_FEEDS.extend([feed.strip() for feed in ADDITIONAL_RSS_FEEDS.split(",")])
