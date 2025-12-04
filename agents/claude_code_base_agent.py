"""
ClaudeCodeベースエージェントクラス
Gemini APIの代わりにClaude Code CLIを使用するエージェントの基底クラス
"""

import os
import json
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class ClaudeCodeBaseAgent(ABC):
    """Claude Codeを使用するサブエージェントの基底クラス"""

    def __init__(self, name: str, description: str):
        """
        Args:
            name: エージェント名
            description: エージェントの説明
        """
        self.name = name
        self.description = description
        self.skills: List[str] = []

        # 作業ディレクトリの設定
        self.base_dir = Path(__file__).parent.parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        """
        Claude Code CLIを使用してテキストを生成

        Args:
            prompt: 生成プロンプト
            max_tokens: 最大トークン数

        Returns:
            生成されたテキスト
        """
        # claude CLIを非対話モードで実行
        cmd = [
            "claude",
            "--print",  # 結果を標準出力に出力
            "--no-input",  # 対話入力を無効化
            "--max-turns", "1",  # 1回のみ応答
        ]

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,  # 5分タイムアウト
                cwd=str(self.base_dir)
            )

            if result.returncode != 0:
                self.log(f"Claude Code error: {result.stderr}", "ERROR")
                raise RuntimeError(f"Claude Code failed: {result.stderr}")

            response = result.stdout.strip()
            if not response:
                raise ValueError("Empty response from Claude Code")

            return response

        except subprocess.TimeoutExpired:
            raise TimeoutError("Claude Code request timed out")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude Code CLI not found. Please ensure 'claude' is installed and in PATH. "
                "Install with: npm install -g @anthropic-ai/claude-code"
            )

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
            "model": "claude-code",
            "skills": self.skills,
        }
