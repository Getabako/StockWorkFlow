"""
Claude API クライアント
GitHub ActionsでClaude APIを使用するためのシンプルなクライアント
"""

import os
import json
import requests
from typing import Optional


class ClaudeAPIClient:
    """Anthropic Claude API クライアント"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Anthropic API キー（環境変数 ANTHROPIC_API_KEY から取得可能）
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Get your API key from https://console.anthropic.com/"
            )
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"  # 最新のSonnetモデル

    def generate(self, prompt: str, max_tokens: int = 8192, system: Optional[str] = None) -> str:
        """
        Claude APIを使用してテキストを生成

        Args:
            prompt: ユーザープロンプト
            max_tokens: 最大トークン数
            system: システムプロンプト（オプション）

        Returns:
            生成されたテキスト
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        data = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        if system:
            data["system"] = system

        response = requests.post(self.api_url, headers=headers, json=data, timeout=300)

        if response.status_code != 200:
            raise RuntimeError(f"Claude API error: {response.status_code} - {response.text}")

        result = response.json()
        return result["content"][0]["text"]


def analyze_with_claude(prompt: str, api_key: Optional[str] = None) -> str:
    """
    シンプルな分析関数

    Args:
        prompt: 分析プロンプト
        api_key: API キー（オプション）

    Returns:
        分析結果
    """
    client = ClaudeAPIClient(api_key)
    return client.generate(prompt)


# 使用例
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude API Client")
    parser.add_argument("prompt", help="Prompt to send to Claude")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Maximum tokens")
    args = parser.parse_args()

    result = analyze_with_claude(args.prompt)
    print(result)
