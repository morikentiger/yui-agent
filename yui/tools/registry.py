"""
YUi Tool Registry

全ToolをAnthropicのtool_use形式で管理し、名前で呼び出す。
"""

from typing import Any

from yui.tools.shell import ShellTool
from yui.tools.file_ops import FileOpsTool
from yui.tools.web import WebTool


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Any] = {}
        self._register_defaults()

    def _register_defaults(self):
        """デフォルトToolを登録"""
        for tool_cls in [ShellTool, FileOpsTool, WebTool]:
            tool = tool_cls()
            self.tools[tool.name] = tool

    def get_tool_schemas(self) -> list[dict]:
        """全Toolのスキーマを返す（Anthropic API形式）"""
        return [tool.schema() for tool in self.tools.values()]

    def execute(self, tool_name: str, params: dict) -> Any:
        """Tool名とパラメータで実行"""
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Unknown tool '{tool_name}'"
        try:
            return tool.execute(**params)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
