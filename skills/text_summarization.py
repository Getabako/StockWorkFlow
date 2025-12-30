"""
TextSummarizationSkill
テキストを要約するスキル
"""

import os
from typing import Dict, Any
from google import genai
from .base_skill import BaseSkill


class TextSummarizationSkill(BaseSkill):
    """テキストを要約するスキル"""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(
            name="text_summarization",
            description="AIを使用してテキストを要約する"
        )
        self.model_name = model_name
        self._model = None

    def _init_model(self):
        """AIモデルを初期化"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self._client = genai.Client(api_key=api_key)

    @property
    def client(self):
        """遅延初期化されたクライアントを返す"""
        if self._model is None:
            self._init_model()
        return self._client

    def summarize(self, text: str, max_length: int = 500, style: str = "formal") -> str:
        """
        テキストを要約

        Args:
            text: 要約するテキスト
            max_length: 最大文字数
            style: 要約スタイル（formal, casual, bullet_points）

        Returns:
            要約されたテキスト
        """
        style_instructions = {
            "formal": "フォーマルなビジネス文書のスタイルで",
            "casual": "カジュアルで読みやすいスタイルで",
            "bullet_points": "箇条書き形式で"
        }

        style_instruction = style_instructions.get(style, style_instructions["formal"])

        prompt = f"""
以下のテキストを{style_instruction}要約してください。
要約は{max_length}文字以内にしてください。

テキスト:
{text}

要約:
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text.strip()

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキルを実行

        Args:
            params:
                - text: 要約するテキスト
                - max_length: 最大文字数（デフォルト: 500）
                - style: 要約スタイル（デフォルト: formal）

        Returns:
            実行結果
                - summary: 要約されたテキスト
                - original_length: 元のテキストの文字数
                - summary_length: 要約の文字数
        """
        if not self.validate_params(params, ["text"]):
            raise ValueError("Missing required parameter: text")

        text = params["text"]
        max_length = params.get("max_length", 500)
        style = params.get("style", "formal")

        self.log(f"Summarizing text ({len(text)} chars) to {max_length} chars")

        summary = self.summarize(text, max_length, style)

        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary)
        }
