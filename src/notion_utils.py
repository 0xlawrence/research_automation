# src/notion_utils.py

from notion_client import Client
from src.config import NOTION_TOKEN, NOTION_DATABASE_ID

# Notionクライアントを初期化
notion = Client(auth=NOTION_TOKEN)

def create_notion_page(title: str, url: str, summary: str, published_date=None, source=None, category=None) -> dict:
    """
    Notionデータベースに新しいページを作成。
    初期ステータスは `Not Started`。
    """
    try:
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "URL": {"url": url},
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            "AI Processing": {"select": {"name": "Not Started"}},
        }

        if published_date:
            properties["Published Date"] = {"date": {"start": published_date.isoformat()}}

        if source:
            properties["Source"] = {"select": {"name": source}}
        
        if category:
            properties["Category"] = {"select": {"name": category}}

        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )
        return new_page

    except Exception as e:
        print("Error in create_notion_page:", e)
        return {}

def update_notion_status(page_id: str, status: str):
    """
    Notionページのステータスを更新。
    """
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "AI Processing": {"select": {"name": status}}
            }
        )
        print(f"Status updated to '{status}' for page ID: {page_id}")
    except Exception as e:
        print(f"Error in update_notion_status (page ID: {page_id}):", e)

def get_pages_by_status(status: str):
    """
    指定したステータスを持つNotionページを取得。
    """
    try:
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            filter={
                "property": "AI Processing",
                "select": {"equals": status}
            }
        )
        return response.get("results", [])
    except Exception as e:
        print(f"Error in get_pages_by_status (status: {status}): {e}")
        return []

def append_page_content(page_id: str, content: str):
    """
    Markdown形式のテキストをNotionのリッチテキスト形式でページに追加。
    """
    try:
        blocks = []

        for line in content.splitlines():
            line = line.strip()

            if not line:  # 空行をスキップ
                continue

            
            # 見出し（Markdownの "###", "##", "#" に対応）
            if line.startswith("### "):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            elif line.startswith("## "):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith("# "):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })

            # #### (見出し4に該当) を Bold に変換
            elif line.startswith("#### "):
                bold_text = line[5:].strip()  # #### の後のテキスト

                # 前後の記号を除去 (マークダウンが正しく認識されるように)
                if bold_text[0] in [":", "："]:
                    bold_text = bold_text[1:].strip()
                if bold_text[-1:] in [":", "："]:
                    bold_text = bold_text[:-1].strip()

                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": bold_text}, "annotations": {"bold": True}}
                        ]
                    }
                })

            # バレットリスト（Markdownの "- " に対応）
            elif line.startswith("- "):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })

            # 番号付きリスト（"1. 項目" の形式に対応）
            elif line[0].isdigit() and line[1] == "." and line[2] == " ":
                    blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })

            # 通常の段落
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })

        # Notionに追加
        notion.blocks.children.append(page_id, children=blocks)
        print(f"Content appended to page ID: {page_id}")

    except Exception as e:
        print(f"Error in append_page_content (page ID: {page_id}): {e}")
