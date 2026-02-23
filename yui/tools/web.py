"""
YUi Web Tool - Web検索・取得

最小限: URLフェッチのみ。後で検索APIを追加できる。
"""

import urllib.request
import urllib.error
from typing import Any

from yui.tools.base import BaseTool


class WebTool(BaseTool):
    name = "web_fetch"
    description = "Fetch content from a URL. Returns the raw text content."

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum characters to return (default: 10000)",
                },
            },
            "required": ["url"],
        }

    def execute(self, url: str, max_length: int = 10000, **kwargs) -> Any:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "YUi/0.1"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                if len(content) > max_length:
                    content = content[:max_length] + f"\n\n[TRUNCATED at {max_length} chars]"
                return content
        except Exception as e:
            return f"[ERROR] {e}"
