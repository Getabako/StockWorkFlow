"""
ベーススキルクラス
すべてのスキルが継承する基底クラス
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseSkill(ABC):
    """スキルの基底クラス"""

    def __init__(self, name: str, description: str):
        """
        Args:
            name: スキル名
            description: スキルの説明
        """
        self.name = name
        self.description = description
        self.version = "1.0.0"

    def log(self, message: str, level: str = "INFO"):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [Skill:{self.name}] [{level}] {message}")

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        スキルのメイン処理を実行

        Args:
            params: 実行パラメータ

        Returns:
            実行結果
        """
        pass

    def validate_params(self, params: Dict[str, Any], required: list) -> bool:
        """
        パラメータの検証

        Args:
            params: 検証するパラメータ
            required: 必須パラメータのリスト

        Returns:
            検証結果
        """
        for param in required:
            if param not in params:
                self.log(f"Missing required parameter: {param}", "ERROR")
                return False
        return True

    def get_info(self) -> Dict[str, Any]:
        """スキル情報を返す"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }
