"""
YUi Agent Loop - The Brain

LLM呼び出し → Tool実行 → 結果反映 のサイクルを最大MAX_ITERATIONS回繰り返す。
Gemini API (OpenAI SDK互換エンドポイント) を使用。

コスト最適化:
  - 会話履歴をMAX_CONTEXT_MESSAGESに制限（古いものは切り捨て）
  - Tool結果をMAX_TOOL_RESULT_CHARSに切り詰め
  - max_tokensを適正値に
  - Honchoの起動時Dialecticを廃止（コスト高）
起動速度最適化:
  - Honcho Peerを遅延初期化
  - ブートステータスでUI更新
"""

import json
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

from yui.config import get_gemini_api_key, get_honcho_api_key, get_honcho_base_url
from yui.agent.context import ContextBuilder
from yui.agent.memory import Memory
from yui.tools.registry import ToolRegistry

MAX_ITERATIONS = 10  # 20→10 に削減（暴走防止）
MAX_CONTEXT_MESSAGES = 12  # 会話履歴の最大メッセージ数
MAX_TOOL_RESULT_CHARS = 3000  # Tool結果の最大文字数
DEFAULT_MODEL = "gemini-3-flash-preview"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

WORKSPACE_DIR = Path.home() / "Workspace" / "YUi" / "workspace"


class AgentLoop:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        workspace: Path = WORKSPACE_DIR,
        on_boot_status: Callable | None = None,
    ):
        self.model = model
        self.workspace = workspace
        self._boot_status = on_boot_status

        # ステータスコールバック: (kind, text) を受け取る関数
        # kind: "thinking" | "tool" | "done"
        self.on_status: Callable | None = None

        self._emit_boot("Gemini API 準備中...")
        self.client = OpenAI(
            api_key=get_gemini_api_key(),
            base_url=GEMINI_BASE_URL,
        )

        # Memory (Honcho) — セッション開始は復元後に行う
        self._emit_boot("Honcho 接続中...")
        self.memory = self._init_memory()

        self._emit_boot("ワークスペース読み込み中...")
        self.context_builder = ContextBuilder(workspace, memory=self.memory)
        self.tool_registry = ToolRegistry()
        self.conversation: list[dict] = []

        # 起動時に過去の会話を復元（新セッション開始の前に！）
        self._emit_boot("記憶を復元中...")
        self._restore_past_context()

        # 復元完了後に新セッションを開始
        self._emit_boot("セッション開始...")
        if self.memory:
            self.memory.start_session()

        self._boot_status = None  # ブート完了

    def _emit_boot(self, text: str):
        """ブート中のステータスをUIに通知"""
        if self._boot_status:
            self._boot_status(text)

    def _init_memory(self) -> Memory | None:
        """Honcho永続記憶を初期化。APIキーがなければスキップ。
        注意: start_session()はここでは呼ばない。
        先に過去の会話を復元してから新セッションを開始する。
        """
        honcho_key = get_honcho_api_key()
        if not honcho_key:
            return None
        try:
            memory = Memory(
                api_key=honcho_key,
                base_url=get_honcho_base_url(),
            )
            return memory
        except Exception as e:
            print(f"[YUi] Honcho init failed (continuing without memory): {e}")
            return None

    def _restore_past_context(self):
        """
        起動時にHonchoから過去の会話コンテキストを復元する。
        これにより、前回の会話の続きが可能になる。
        """
        if not self.memory:
            return

        try:
            past_messages = self.memory.get_past_messages_openai()
            if past_messages:
                # OpenAI形式のメッセージを会話履歴に注入
                self.conversation = past_messages
        except Exception as e:
            print(f"[YUi] Past context restore failed: {e}")

    def _trim_conversation(self):
        """会話履歴をMAX_CONTEXT_MESSAGESに制限。古いものを切り捨てる。"""
        if len(self.conversation) > MAX_CONTEXT_MESSAGES:
            self.conversation = self.conversation[-MAX_CONTEXT_MESSAGES:]

    def run(self, user_message: str) -> str:
        """
        ユーザーメッセージを受け取り、Agent Loopを回して最終応答を返す。
        """
        self.conversation.append({"role": "user", "content": user_message})
        self._trim_conversation()

        # Honchoにユーザーメッセージを保存
        if self.memory:
            try:
                self.memory.store_user_message(user_message)
            except Exception as e:
                print(f"[Memory] store error: {e}")

        system_prompt = self.context_builder.build_system_prompt()
        tools = self.tool_registry.get_tool_schemas()

        for iteration in range(MAX_ITERATIONS):
            self._emit_status("thinking", "考え中...")
            response = self._call_llm(system_prompt, tools)
            message = response.choices[0].message

            # アシスタントメッセージを会話に追加
            assistant_msg = {"role": "assistant", "content": message.content or ""}
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]
            self.conversation.append(assistant_msg)

            # Tool呼び出しがなければ最終応答
            if not message.tool_calls:
                final_response = message.content or ""

                # Honchoにエージェント応答を保存
                if self.memory:
                    try:
                        self.memory.store_agent_message(final_response)
                    except Exception as e:
                        print(f"[Memory] store error: {e}")

                return final_response

            # Tool実行
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                self._emit_status("tool", f"{tool_name} を実行中...")

                try:
                    params = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    params = {}

                result = self.tool_registry.execute(tool_name, params)

                # Tool結果を切り詰め
                result_str = self._format_tool_result(result)
                if len(result_str) > MAX_TOOL_RESULT_CHARS:
                    result_str = result_str[:MAX_TOOL_RESULT_CHARS] + f"\n\n[TRUNCATED at {MAX_TOOL_RESULT_CHARS} chars]"

                self.conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                })

        return "[YUi] 最大イテレーション数に到達しました。途中結果を返します。"

    def _call_llm(self, system_prompt: str, tools: list[dict]) -> Any:
        """Gemini API (OpenAI互換エンドポイント) を呼び出す"""
        messages = [{"role": "system", "content": system_prompt}] + self.conversation

        kwargs = {
            "model": self.model,
            "max_tokens": 2048,  # 8096→2048 (応答は長くなくていい)
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        return self.client.chat.completions.create(**kwargs)

    def _emit_status(self, kind: str, text: str):
        """UIにステータス更新を通知"""
        if self.on_status:
            self.on_status(kind, text)

    def _format_tool_result(self, result: Any) -> str:
        """Tool実行結果を文字列に変換"""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    def reset(self):
        """会話履歴をクリアし、新しいセッションを開始"""
        self.conversation = []
        if self.memory:
            try:
                self.memory.start_session()
            except Exception as e:
                print(f"[Memory] new session error: {e}")
        self.context_builder.refresh_memory()
