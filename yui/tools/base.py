"""
YUi Tool Base Class

OpenAI function calling形式のスキーマを返す。
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """全Toolの基底クラス"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def parameters_schema(self) -> dict:
        """パラメータのJSON Schemaを返す"""
        ...

    def schema(self) -> dict:
        """OpenAI function calling形式のスキーマを返す"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema(),
            },
        }

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Toolを実行"""
        ...
