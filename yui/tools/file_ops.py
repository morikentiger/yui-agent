"""
YUi File Operations Tool - ファイル読み書き
"""

from pathlib import Path
from typing import Any

from yui.tools.base import BaseTool


class FileOpsTool(BaseTool):
    name = "file_ops"
    description = "Read, write, list, or append to files on the filesystem."

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
                    "description": "File or directory path",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write or append (for write/append actions)",
                },
            },
            "required": ["action", "path"],
        }

    def execute(self, action: str, path: str, content: str = "", **kwargs) -> Any:
        p = Path(path).expanduser()

        if action == "read":
            if not p.exists():
                return f"[NOT FOUND] {p}"
            return p.read_text(encoding="utf-8")

        elif action == "write":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"[WRITTEN] {p} ({len(content)} chars)"

        elif action == "append":
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(content)
            return f"[APPENDED] {p} (+{len(content)} chars)"

        elif action == "list":
            if not p.exists():
                return f"[NOT FOUND] {p}"
            if p.is_file():
                return str(p)
            entries = sorted(p.iterdir())
            return "\n".join(
                f"{'[DIR] ' if e.is_dir() else ''}{e.name}" for e in entries
            )

        elif action == "exists":
            return str(p.exists())

        return f"[UNKNOWN ACTION] {action}"
