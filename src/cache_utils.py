import os

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed_urls.txt")

def load_processed_urls():
    """処理済みURLのリストを読み込む"""
    if not os.path.exists(CACHE_FILE):
        return set()
    
    with open(CACHE_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_url(url: str):
    """URLを処理済みとして保存"""
    with open(CACHE_FILE, 'a') as f:
        f.write(url + '\n')
