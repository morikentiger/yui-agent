"""
YUi Shell Tool - コマンド実行

セキュリティ制限なし。Mac miniに隔離されている前提。
"""

import subprocess
from typing import Any

from yui.tools.base import BaseTool


class ShellTool(BaseTool):
    name = "shell"
    description = "Execute a shell command on the system. No restrictions."

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120)",
                },
            },
            "required": ["command"],
        }

    def execute(self, command: str, timeout: int = 120, **kwargs) -> Any:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[EXIT CODE: {result.returncode}]"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT] Command exceeded {timeout}s"
        except Exception as e:
            return f"[ERROR] {e}"
