from typing import List, Dict, Any
from openai import OpenAI
from .config import USE_DEEPSEEK, OPENAI_API_KEY, DEEPSEEK_API_KEY

class AIClient:
    """統一されたAIクライアントクラス"""
    
    def __init__(self):
        self._client = None
        self.is_deepseek = USE_DEEPSEEK
        
    def get_client(self):
        """遅延初期化されたクライアントを取得"""
        if self._client is None:
            if self.is_deepseek:
                self._client = OpenAI(
                    api_key=DEEPSEEK_API_KEY,
                    base_url="https://api.deepseek.com"
                )
            else:
                self._client = OpenAI(api_key=OPENAI_API_KEY)
        return self._client
    
    def call_api(self, messages, model=None, max_tokens=1000, **kwargs):
        """APIを呼び出す共通メソッド"""
        client = self.get_client()
        if not model:
            model = "deepseek-reasoner" if self.is_deepseek else "gpt-4o-mini"
            
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # DeepSeekの場合はレスポンスにreasoning_contentがある可能性がある
        if self.is_deepseek and hasattr(response.choices[0].message, 'reasoning_content'):
            print("\n=== Reasoning Process ===")
            print(response.choices[0].message.reasoning_content)
            print("========================\n")
            
        return response

# グローバルインスタンス
ai_client = AIClient() 