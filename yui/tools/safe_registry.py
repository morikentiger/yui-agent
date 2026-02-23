"""
YUi Safe Tool Registry - セキュアなツールセット
"""

from typing import Dict, Type

from yui.tools.base import BaseTool
from yui.tools.safe_shell import SafeShellTool
from yui.tools.safe_file_ops import SafeFileOpsTool
from yui.tools.web import WebTool


class SafeToolRegistry:
    """安全なツールのみを提供するレジストリ"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_safe_tools()
    
    def _register_safe_tools(self):
        """安全なツールを登録"""
        safe_tools = [
            SafeShellTool(),
            SafeFileOpsTool(),
            WebTool(),  # Web接続は比較的安全とみなす
        ]
        
        for tool in safe_tools:
            self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        return self._tools.copy()


# グローバルインスタンス
safe_registry = SafeToolRegistry()