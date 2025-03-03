# src/notion_utils.py

from notion_client import Client
from datetime import datetime
from .config import NOTION_TOKEN, NOTION_DATABASE_ID
from .rss_fetch import clean_domain
import re
from typing import Optional, Dict, Any, List
import pytz
import json
import requests

# Notionクライアントを初期化
notion = Client(auth=NOTION_TOKEN)

def get_notion_client():
    """
    既に初期化されたグローバルな Notion クライアントのインスタンスを返します。
    """
    return notion

def create_notion_page(
    title: str,
    url: str,
    summary: str,
    published_date: datetime,
    source: str,
    category: str
) -> Optional[Dict[str, Any]]:
    """
    新しい Notionページを作成する関数
    """
    try:
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "URL": {"url": url if url else None},
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            "Category": {"select": {"name": category}},
            "Source": {"select": {"name": source}},
            "Published Date": {"date": {"start": published_date.isoformat()}},
            "AI Processing": {"select": {"name": "Not Started"}},
        }

        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )

        return new_page

    except Exception as e:
        print(f"❌ Notion Page Creation Failed [Title: '{title[:20]}...']")
        print(f"🛠️ Error Details: {str(e)}")
        return None

def append_page_content(page_id: str, content: str) -> bool:
    """
    Notionページにコンテンツを追加する関数
    """
    try:
        notion = get_notion_client()
        
        # コンテンツをブロックに変換
        blocks = convert_content_to_blocks(content)
        
        # 空のコンテンツチェック
        if not blocks:
            print("Warning: No content blocks generated")
            return False
            
        # ブロックの追加
        response = notion.blocks.children.append(
            block_id=page_id,
            children=blocks
        )
        
        if response:
            print(f"Successfully added {len(blocks)} blocks to page")
            update_notion_status(page_id, "Completed")
            return True
        return False
        
    except Exception as e:
        print(f"Error appending content to Notion: {e}")
        if hasattr(e, 'response'):
            print(f"Response details: {e.response.text if hasattr(e.response, 'text') else e.response}")
        update_notion_status(page_id, "Error")
        return False

def update_notion_status(page_id: str, new_status: str) -> None:
    """
    Notionページのステータスを更新する
    
    Args:
        page_id (str): NotionページのID
        new_status (str): 新しいステータス
    """
    try:
        notion = get_notion_client()
        
        notion.pages.update(
            page_id=page_id,
            properties={
                "AI Processing": {
                    "select": {
                        "name": new_status
                    }
                }
            }
        )
        
        print(f"Successfully updated status to: {new_status}")
        
    except Exception as e:
        print(f"Error updating Notion status: {e}")
        # エラーの詳細をログに記録
        if hasattr(e, 'response'):
            print(f"Response details: {e.response.text if hasattr(e.response, 'text') else e.response}")

def get_pages_by_status(status: str):
    """
    指定した "AI Processing" ステータスを持つ Notionページを取得する。
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

def create_heading_block(level: int, text: str) -> dict:
    """
    指定したレベルの見出しブロックを作成する。
    level: 1, 2, 3 など
    """
    block_type = f"heading_{level}"
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def create_bulleted_list_block(text: str) -> dict:
    """
    箇条書き（リスト）ブロックを作成する。
    """
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def create_paragraph_block(text: str) -> dict:
    """
    段落ブロックを作成する。
    """
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    }

def parse_bold_line(line: str) -> list:
    """
    行内にある **...** の Bold 表現を解析し、Bold 表現直後に存在する
    句読点（半角: ; および全角： ；）を Bold に含める。
    Notion の rich_text 用オブジェクトのリストを返す。
    """
    rich_text = []
    last_end = 0
    pattern = re.compile(r'\*\*(.*?)\*\*')
    punctuation = {":", ";", "：", "；"}
    for match in pattern.finditer(line):
        start, end = match.span()
        if start > last_end:
            rich_text.append({
                "type": "text",
                "text": {"content": line[last_end:start]}
            })
        bold_text = match.group(1)
        # Bold 表現の直後に指定句読点があれば Bold に含める
        if end < len(line) and line[end] in punctuation:
            bold_text += line[end]
            end += 1
        rich_text.append({
            "type": "text",
            "text": {"content": bold_text},
            "annotations": {"bold": True}
        })
        last_end = end
    if last_end < len(line):
        rich_text.append({
            "type": "text",
            "text": {"content": line[last_end:]}
        })
    return rich_text

def parse_rich_text(text: str) -> list:
    """
    テキスト内のリッチテキスト要素（太字、イタリック、リンクなど）を解析して
    Notionのrich_text形式に変換します。
    """
    rich_text_elements = []
    current_pos = 0
    
    # リッチテキストのパターン
    patterns = [
        (r'\*\*(.+?)\*\*', 'bold'),           # **太字**
        (r'_(.+?)_', 'italic'),               # _イタリック_
        (r'\[(.+?)\]\((.+?)\)', 'link'),      # [テキスト](URL)
        (r'`(.+?)`', 'code'),                 # `コード`
    ]
    
    while current_pos < len(text):
        earliest_match = None
        earliest_pattern = None
        earliest_pos = len(text)
        
        # 各パターンで最も早く出現する要素を探す
        for pattern, type_ in patterns:
            match = re.search(pattern, text[current_pos:])
            if match and current_pos + match.start() < earliest_pos:
                earliest_match = match
                earliest_pattern = type_
                earliest_pos = current_pos + match.start()
        
        # プレーンテキストの追加
        if earliest_pos > current_pos:
            plain_text = text[current_pos:earliest_pos]
            if plain_text:
                rich_text_elements.append({
                    "type": "text",
                    "text": {"content": plain_text}
                })
        
        # リッチテキスト要素がない場合
        if not earliest_match:
            remaining_text = text[current_pos:]
            if remaining_text:
                rich_text_elements.append({
                    "type": "text",
                    "text": {"content": remaining_text}
                })
            break
        
        # リッチテキスト要素の追加
        if earliest_pattern == 'link':
            link_text = earliest_match.group(1)
            link_url = earliest_match.group(2)
            rich_text_elements.append({
                "type": "text",
                "text": {
                    "content": link_text,
                    "link": {"url": link_url}
                }
            })
        else:
            content = earliest_match.group(1)
            element = {
                "type": "text",
                "text": {"content": content},
                "annotations": {
                    "bold": earliest_pattern == 'bold',
                    "italic": earliest_pattern == 'italic',
                    "code": earliest_pattern == 'code',
                    "strikethrough": False,
                    "underline": False,
                    "color": "default"
                }
            }
            rich_text_elements.append(element)
        
        current_pos = current_pos + earliest_match.end()
    
    return rich_text_elements

def convert_content_to_blocks(content: str) -> list:
    """
    コンテンツ文字列を受け取り、Notion のブロック形式に変換します。
    Markdown形式のテキストを適切なNotionブロックに変換します。
    """
    if not content:
        return []
        
    blocks = []
    lines = content.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # 見出しの処理
        if line.startswith('# '):
            # 見出し1
            blocks.append(create_heading_block(1, line.lstrip('# ').strip()))
        elif line.startswith('## '):
            # 見出し2
            blocks.append(create_heading_block(2, line.lstrip('## ').strip()))
        elif line.startswith('### '):
            # 見出し3
            blocks.append(create_heading_block(3, line.lstrip('### ').strip()))
        # 箇条書きの処理
        elif line.startswith('- '):
            # リスト項目
            blocks.append(create_bulleted_list_block(line[2:].strip()))
        # 番号付きリストの処理
        elif re.match(r'^\d+\. ', line):
            match = re.match(r'^\d+\. (.*)', line)
            if match:
                text = match.group(1).strip()
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": parse_rich_text(text)
                    }
                })
        # 通常の段落の処理
        else:
            # 段落が連続している場合は結合して処理
            paragraph_text = line
            next_idx = i + 1
            while next_idx < len(lines) and lines[next_idx].strip() and not (
                lines[next_idx].strip().startswith('#') or 
                lines[next_idx].strip().startswith('-') or 
                re.match(r'^\d+\. ', lines[next_idx].strip())
            ):
                paragraph_text += "\n" + lines[next_idx].strip()
                i += 1
                next_idx += 1
                
            blocks.append(create_paragraph_block(paragraph_text))
        i += 1
    
    # Notionのブロック制限（最大100ブロック）に対応
    if len(blocks) > 100:
        print(f"Warning: Content has {len(blocks)} blocks, truncating to 100 blocks")
        blocks = blocks[:100]
    
    return blocks
