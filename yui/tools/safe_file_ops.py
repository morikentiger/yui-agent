"""
YUi Safe File Operations Tool - セキュアなファイル読み書き

ワークスペース内でのみファイル操作可能
"""

from pathlib import Path
from typing import Any

from yui.tools.base import BaseTool


class SafeFileOpsTool(BaseTool):
    name = "safe_file_ops"
    description = "Safe file operations within workspace sandbox."

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "append", "list", "exists"],
                    "description": "The file operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path (relative to workspace)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write or append (for write/append actions)",
                },
            },
            "required": ["action", "path"],
        }

    def _get_safe_path(self, path: str) -> tuple[Path | None, str]:
        """ワークスペース内の安全なパスを取得"""
        workspace = Path.cwd() / "workspace"
        workspace.mkdir(exist_ok=True)
        
        try:
            # パスを正規化
            target = workspace / path
            resolved = target.resolve()
            
            # ワークスペース内かチェック
            workspace_resolved = workspace.resolve()
            if not str(resolved).startswith(str(workspace_resolved)):
                return None, f"Path outside workspace: {path}"
            
            return resolved, "OK"
            
        except Exception as e:
            return None, f"Invalid path: {e}"

    def execute(self, action: str, path: str, content: str = "", **kwargs) -> Any:
        safe_path, error = self._get_safe_path(path)
        if not safe_path:
            return f"[BLOCKED] {error}"

        try:
            if action == "read":
                if not safe_path.exists():
                    return f"[NOT FOUND] {path}"
                return safe_path.read_text(encoding="utf-8")

            elif action == "write":
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                safe_path.write_text(content, encoding="utf-8")
                return f"[WRITTEN] {path} ({len(content)} chars)"

            elif action == "append":
                safe_path.parent.mkdir(parents=True, exist_ok=True)
                with open(safe_path, "a", encoding="utf-8") as f:
                    f.write(content)
                return f"[APPENDED] {path} (+{len(content)} chars)"

            elif action == "list":
                if not safe_path.exists():
                    return f"[NOT FOUND] {path}"
                if safe_path.is_file():
                    return str(safe_path.name)
                entries = sorted(safe_path.iterdir())
                return "\n".join(
                    f"{'[DIR] ' if e.is_dir() else ''}{e.name}" for e in entries
                )

            elif action == "exists":
                return str(safe_path.exists())

            return f"[UNKNOWN ACTION] {action}"
            
        except Exception as e:
            return f"[ERROR] {e}"