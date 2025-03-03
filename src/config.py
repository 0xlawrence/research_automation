from dotenv import load_dotenv
import os

# .envの読み込み
load_dotenv()

# 環境変数を取得
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
USE_DEEPSEEK = os.getenv("USE_DEEPSEEK", "false").lower() == "true"
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


# 必須の環境変数が設定されているか確認
if not NOTION_TOKEN:
    raise EnvironmentError("環境変数 'NOTION_TOKEN' が設定されていません。 .envファイルを確認してください。")
if not NOTION_DATABASE_ID:
    raise EnvironmentError("環境変数 'NOTION_DATABASE_ID' が設定されていません。 .envファイルを確認してください。")
if not OPENAI_API_KEY:
    raise EnvironmentError("環境変数 'OPENAI_API_KEY' が設定されていません。 .envファイルを確認してください。")
if USE_DEEPSEEK and not DEEPSEEK_API_KEY:
    raise EnvironmentError("USE_DEEPSEEK=trueの場合、DEEPSEEK_API_KEYが必要です。 .envファイルを確認してください。")
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY is not set in .env file")

# 収集対象のRSSフィードを定義
RSS_FEEDS = [
    "https://wublock.substack.com/feed",
    "https://parsec.substack.com/feed",
    "https://www.decentralised.co/feed",
    "https://www.onchaintimes.com/rss/",
    "https://www.thedefinvestor.com/feed",
    "https://www.alphaplease.com/feed",
    "https://stacymuur.substack.com/feed",
    "https://www.ignasdefi.com/feed",
    "https://s4mmyeth.substack.com/feed",
    "https://pomp.substack.com/feed",
    "https://reflexivityresearch.substack.com/feed",
    "https://www.citationneeded.news/rss/",
    "https://www.shoal.gg/feed",
    "https://alearesearch.substack.com/feed",
    "https://magazine.sebastianraschka.com/feed",
    "https://newsletter.victordibia.com/feed",
    "https://arnicas.substack.com/feed",
    "https://www.ai-supremacy.com/feed",
    "https://review.stanfordblockchain.xyz/feed", 
    "https://www.noahpinion.blog/feed",
    "https://thegeneralist.substack.com/feed",
    "https://ouroborosresearch.substack.com/feed",
    "https://a16zcrypto.substack.com/feed",
    "https://reports.tiger-research.com/feed",
    "https://insights4vc.substack.com/feed",
    "https://thedailydegen.substack.com/feed",
    "https://www.lennysnewsletter.com/feed",
    "https://www.notboring.co/feed",
    "https://cryptohayes.substack.com/feed",
    "https://viktordefi.com/feed",
    "https://www.globalmacroresearch.org/jp/feed",
    "https://andrewchen.substack.com/feed",
    "https://rss.panewslab.com/zh/tvsq/rss",
    "https://patternventures.substack.com/feed",
    "https://recodechinaai.substack.com/feed",
]

# 必要であれば外部ファイルや環境変数からRSSフィードを取得する方法も提供
ADDITIONAL_RSS_FEEDS = os.getenv("ADDITIONAL_RSS_FEEDS")  # カンマ区切りでフィードを指定可能
if ADDITIONAL_RSS_FEEDS:
    RSS_FEEDS.extend([feed.strip() for feed in ADDITIONAL_RSS_FEEDS.split(",")])
