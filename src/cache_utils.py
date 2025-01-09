import os

PROCESSED_URLS_FILE = "processed_urls.txt"

def load_processed_urls() -> set:
    """
    処理済みURLをファイルから読み込む。
    Returns:
        set: 処理済みURLのセット
    """
    if not os.path.exists(PROCESSED_URLS_FILE):
        return set()
    with open(PROCESSED_URLS_FILE, "r") as file:
        return set(line.strip() for line in file)

def save_processed_url(url: str):
    """
    処理済みURLをファイルに追加する。
    Args:
        url (str): 処理済みURL
    """
    with open(PROCESSED_URLS_FILE, "a") as file:
        file.write(url + "\n")
