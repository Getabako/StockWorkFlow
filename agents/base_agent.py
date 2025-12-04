"""
ベースエージェントクラス
すべてのサブエージェントが継承する基底クラス
"""

import os
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import google.generativeai as genai


class BaseAgent(ABC):
    """サブエージェントの基底クラス"""

    def __init__(self, name: str, description: str, model_name: str = "gemini-2.5-flash"):
        """
        Args:
            name: エージェント名
            description: エージェントの説明
            model_name: 使用するAIモデル名
        """
        self.name = name
        self.description = description
        self.model_name = model_name
        self.skills: List[str] = []
        self._model = None

        # 作業ディレクトリの設定
        self.base_dir = Path(__file__).parent.parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

    def _init_model(self):
        """AIモデルを初期化"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self.model_name)

    @property
    def model(self):
        """遅延初期化されたモデルを返す"""
        if self._model is None:
            self._init_model()
        return self._model

    def generate(self, prompt: str) -> str:
        """
        AIを使用してテキストを生成

        Args:
            prompt: 生成プロンプト

        Returns:
            生成されたテキスト
        """
        response = self.model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response from AI model")
        return response.text

    def log(self, message: str, level: str = "INFO"):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.name}] [{level}] {message}")

    def save_output(self, data: Any, filename: str, as_json: bool = True):
        """
        出力データを保存

        Args:
            data: 保存するデータ
            filename: ファイル名
            as_json: JSON形式で保存するか
        """
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if as_json:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(data))

        self.log(f"Output saved to {output_path}")
        return output_path

    def load_input(self, filename: str, as_json: bool = True) -> Any:
        """
        入力データを読み込む

        Args:
            filename: ファイル名
            as_json: JSON形式で読み込むか

        Returns:
            読み込んだデータ
        """
        input_path = self.output_dir / filename
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            if as_json:
                return json.load(f)
            return f.read()

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェントのメイン処理を実行

        Args:
            context: 実行コンテキスト（前のエージェントからの出力など）

        Returns:
            実行結果（次のエージェントへの入力となる）
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """エージェントのステータスを返す"""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model_name,
            "skills": self.skills,
        }
