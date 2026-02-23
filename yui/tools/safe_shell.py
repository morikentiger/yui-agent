"""
YUi Safe Shell Tool - セキュアなコマンド実行

許可されたコマンドのみ実行可能
ワークスペース内でのみ動作
"""

import subprocess
from pathlib import Path
from typing import Any

from yui.tools.base import BaseTool


class SafeShellTool(BaseTool):
    name = "safe_shell"
    description = "Execute safe shell commands in workspace sandbox."

    # 許可されたコマンド
    ALLOWED_COMMANDS = {
        'ls', 'cat', 'echo', 'pwd', 'mkdir', 'touch', 'grep', 'find',
        'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
        'git', 'curl', 'wget', 'head', 'tail', 'wc', 'sort', 'uniq',
        'cp', 'mv', 'rm'  # ファイル操作は制限付きで許可
    }
    
    # 危険なオプション
    DANGEROUS_PATTERNS = [
        '..',  # 親ディレクトリアクセス
        '~',   # ホームディレクトリ
        '/',   # ルートアクセス
        '|',   # パイプ（制限）
        ';',   # コマンド連結
        '&&',  # コマンド連結
        '||',  # コマンド連結
        '`',   # コマンド置換
        '$(',  # コマンド置換
        '>',   # リダイレクト（制限）
        '>>',  # リダイレクト（制限）
    ]

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The safe shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                },
            },
            "required": ["command"],
        }

    def _is_safe_command(self, command: str) -> tuple[bool, str]:
        """コマンドが安全かチェック"""
        parts = command.strip().split()
        if not parts:
            return False, "Empty command"
        
        base_command = parts[0]
        
        # 許可されたコマンドかチェック
        if base_command not in self.ALLOWED_COMMANDS:
            return False, f"Command '{base_command}' not allowed"
        
        # 危険なパターンをチェック
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                return False, f"Dangerous pattern '{pattern}' detected"
        
        return True, "OK"

    def execute(self, command: str, timeout: int = 30, **kwargs) -> Any:
        # ワークスペースディレクトリを設定
        workspace = Path.cwd() / "workspace"
        workspace.mkdir(exist_ok=True)
        
        # コマンド安全性チェック
        is_safe, reason = self._is_safe_command(command)
        if not is_safe:
            return f"[BLOCKED] {reason}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workspace,  # ワークスペース内で実行
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