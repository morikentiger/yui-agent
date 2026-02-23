"""
YUi Context Builder

Agent Loopの毎回のLLM呼び出し前に、system promptを組み立てる。
SOUL.md (人格) + AGENTS.md (行動指針) + Honchoメモリ をマージ。
"""

from pathlib import Path
from datetime import datetime

from yui.agent.memory import Memory


class ContextBuilder:
    def __init__(self, workspace: Path, memory: Memory | None = None):
        self.workspace = workspace
        self.memory = memory
        # 起動時に1回だけHonchoから記憶を取得（毎ターン呼ぶと遅い）
        self._cached_memory_text: str | None = None
        self._memory_loaded = False

    def build_system_prompt(self) -> str:
        """
        system promptを組み立てる。
        優先順位: SOUL.md > AGENTS.md > Honchoメモリ > Runtime
        """
        parts = []

        # Core identity
        soul = self._load_file("SOUL.md")
        if soul:
            parts.append(soul)

        # Behavioral guidelines
        agents = self._load_file("AGENTS.md")
        if agents:
            parts.append(agents)

        # Honcho persistent memory
        if self.memory:
            memory_text = self._get_memory_text()
            if memory_text:
                parts.append(memory_text)
        else:
            # Fallback: ローカルMEMORY.md
            local_memory = self._load_file("memory/MEMORY.md")
            if local_memory:
                parts.append(f"# Long-term Memory\n\n{local_memory}")

        # Runtime context
        parts.append(self._runtime_context())

        return "\n\n---\n\n".join(parts)

    def _get_memory_text(self) -> str | None:
        """Honchoの記憶テキストを取得（初回のみ、以降はキャッシュ）"""
        if not self.memory:
            return None

        if not self._memory_loaded:
            self._memory_loaded = True
            try:
                self._cached_memory_text = self.memory.get_context_for_prompt()
            except Exception as e:
                print(f"[Context] memory load error: {e}")
                self._cached_memory_text = None

        return self._cached_memory_text

    def refresh_memory(self):
        """記憶キャッシュを更新（/refreshコマンド用）"""
        self._memory_loaded = False
        self._cached_memory_text = None

    def _load_file(self, relative_path: str) -> str | None:
        """workspaceからMarkdownファイルを読み込む"""
        path = self.workspace / relative_path
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return None

    def _runtime_context(self) -> str:
        """実行時コンテキスト（日時、環境情報など）"""
        now = datetime.now()
        memory_status = "Honcho (persistent)" if self.memory else "Local files only"
        return f"""# Runtime Context
- Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}
- Workspace: {self.workspace}
- Memory: {memory_status}
- Available tools: Use tool calls to take actions."""
