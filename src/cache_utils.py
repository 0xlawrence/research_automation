import os

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed_urls.txt")

def load_processed_urls():
    """処理済みURLのリストを読み込む"""
    try:
        if not os.path.exists(CACHE_FILE):
            # キャッシュディレクトリがない場合は作成
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            return set()
        
        with open(CACHE_FILE, 'r') as f:
            # URLを正規化して保存
            return {line.strip() for line in f if line.strip()}
            
    except Exception as e:
        print(f"⚠️ Error loading processed URLs: {e}")
        return set()

def save_processed_url(url: str):
    """URLを処理済みとして保存"""
    with open(CACHE_FILE, 'a') as f:
        f.write(url + '\n')
