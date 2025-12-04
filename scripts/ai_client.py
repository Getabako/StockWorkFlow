"""
AIクライアント - GeminiとClaudeの統一インターフェース
環境変数 AI_PROVIDER で切り替え可能
"""

import os
from typing import Optional


class AIClient:
    """Gemini/Claude 統一AIクライアント"""

    def __init__(self, provider: Optional[str] = None):
        """
        Args:
            provider: "gemini" または "claude"（環境変数 AI_PROVIDER から取得可能）
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "gemini")
        self._client = None

    def _init_gemini(self):
        """Geminiクライアントを初期化"""
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")

    def _init_claude(self):
        """Claudeクライアントを初期化"""
        from claude_api_client import ClaudeAPIClient
        return ClaudeAPIClient()

    @property
    def client(self):
        """遅延初期化されたクライアントを返す"""
        if self._client is None:
            if self.provider == "claude":
                self._client = self._init_claude()
            else:
                self._client = self._init_gemini()
        return self._client

    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        """
        テキストを生成

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            生成されたテキスト
        """
        if self.provider == "claude":
            return self.client.generate(prompt, max_tokens)
        else:
            # Gemini
            response = self.client.generate_content(prompt)
            if not response.text:
                raise ValueError("Empty response from Gemini")
            return response.text


def get_ai_client(provider: Optional[str] = None) -> AIClient:
    """
    AIクライアントを取得

    Args:
        provider: "gemini" または "claude"

    Returns:
        AIClient インスタンス
    """
    return AIClient(provider)


# 使用例
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Client")
    parser.add_argument("prompt", help="Prompt to send")
    parser.add_argument("--provider", choices=["gemini", "claude"], help="AI provider")
    args = parser.parse_args()

    client = get_ai_client(args.provider)
    print(f"Using provider: {client.provider}")
    result = client.generate(args.prompt)
    print(result)
