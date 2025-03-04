# Research Automation Tool

ブロックチェーン・AI関連のニュースやリサーチを収集・分析し、Notionデータベースで管理するツール。
- Site: https://0xlawrence.notion.site/17650a8c997080948d93fe473cbed22d?v=17d50a8c997080d8b92a000ca48509f9
   - （現在は実行結果の閲覧のみ）

## 機能概要

1. **RSSフィードとHackerNewsからの記事収集**
   - 設定したRSSフィードから新規記事を取得
   - HackerNews上位記事の取得と分析
   - Notionデータベースに記事情報を登録
   - AIによる初期要約生成
   - カテゴリの自動分類（DeFi, NFT, Layer1, Layer2, DAO, AI, その他）

2. **AI分析機能**
   - 統一AIクライアント（OpenAI/DeepSeekの切り替え対応）
   - 詳細なサマリー生成（背景、概要、仕組み・技術的構造、市場への影響、今後の展望）
   - レポート作成のための骨子提案（Background, Problems, Solutions, Conclusion）
   - 考察の視点（3-5個）と追加調査が必要な問い（3-5個）の生成

3. **Notion統合**
   - 記事のメタデータ管理（タイトル、URL、公開日、ソース、カテゴリ）
   - ステータス管理（Not Started → Processing → Completed）
   - AI生成コンテンツのMarkdown形式での構造化出力

## セットアップ

1. 必要な環境変数を設定（`.env`ファイル）:
- NOTION_TOKEN=your_notion_token
- NOTION_DATABASE_ID=your_database_id
- OPENAI_API_KEY=your_openai_api_key

2. 依存パッケージのインストール:
```
bash
pip install -r requirements.txt
```

## 使用方法

1. RSSフィードの設定
   - `src/config.py`の`RSS_FEEDS`リストにフィードURLを追加

2. 新規記事の取得・登録
```
bash
python main.py
```
3. 記事の詳細分析
   - Notionデータベース上で対象記事の`AI Processing`ステータスを`Processing`に変更
   - `main.py`を実行すると、`Processing`ステータスの記事に対して：
     - 記事本文のスクレイピング
     - 詳細なサマリーの生成
     - レポート骨子の作成
     - 考察と問いの生成
     - 結果をNotionページに追加

## セットアップ

### 1. 環境変数の設定
`.env`ファイルに以下を設定：

- NOTION_TOKEN=your_notion_token
- NOTION_DATABASE_ID=your_database_id
- OPENAI_API_KEY=your_openai_api_key
- DEEPSEEK_API_KEY=your_deepseek_api_key  # オプション
- USE_DEEPSEEK=false  # true/false

### 2. 依存パッケージのインストール
```
pip install -r requirements.txt
```

## 使用方法

### 1. API選択の設定
- `src/config.py`の`USE_DEEPSEEK`でAIプロバイダを選択
  - `True`: DeepSeek API
  - `False`: OpenAI API（デフォルト）

### 2. RSSフィードの設定
- `src/config.py`の`RSS_FEEDS`リストにフィードURLを追加

### 3. 新規記事の取得・登録

python main.py

### 4. 記事の詳細分析
- Notionデータベース上で対象記事の`Status`を`Processing`に変更
- `main.py`を実行すると、`Processing`ステータスの記事に対して：
  - 記事本文のスクレイピング
  - 詳細なサマリーの生成
  - インサイトと問いの抽出
  - レポート骨子の作成
  - 結果をNotionページに追加

## プロジェクト構造

```
research-automation/
├── .env                  # 環境変数
├── .gitignore           # Git除外設定
├── README.md            # プロジェクト説明
├── requirements.txt     # 依存パッケージ
├── run_script.sh        # 実行スクリプト
├── src/                 # ソースコード
│   ├── __init__.py
│   ├── main.py         # メインスクリプト
│   ├── config.py       # 設定・RSSフィード
│   ├── ai_client.py    # 統一AIクライアント
│   ├── hackernews_fetch.py # HackerNews取得
│   ├── notion_utils.py # Notion API関連
│   ├── openai_utils.py # OpenAI API関連
│   ├── deepseek_utils.py # DeepSeek API関連
│   ├── perplexity.py   # Perplexity API関連
│   ├── rss_fetch.py    # RSSフィード取得
│   ├── scraper.py      # Webスクレイピング
│   └── cache_utils.py  # URL処理履歴管理
├── logs/               # ログファイル
│   └── .gitkeep
└── data/              # キャッシュなどのデータ
    └── .gitkeep
```

## 依存パッケージ

- feedparser==6.0.10
- openai>=1.12.0
- notion-client==2.3.0
- python-dotenv==1.0.0
- requests==2.31.0
- beautifulsoup4==4.12.2

## 注意事項

- `.env`ファイルは必ずGitignoreに含めること
- OpenAI/DeepSeek APIの利用料金に注意
- スクレイピング対象サイトの利用規約を確認
- 大量の記事を一度に処理する場合はAPIレート制限に注意

## ライセンス

MIT License
