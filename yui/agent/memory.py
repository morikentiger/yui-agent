"""
YUi Memory - Honcho Integration

Honchoの永続記憶をYUiのAgent Loopに統合する。

速度最適化:
  - Peerオブジェクトを遅延初期化（起動時のAPI呼び出し削減）
  - セッション一覧の取得を最小限に

正しいAPI:
  session.context() → SessionContext (messages, summary, peer_representation, peer_card)
  session.messages() → 全メッセージ
  peer.chat() → 自然言語で記憶に問い合わせ
  peer.search() → メッセージ検索
  peer.get_card() → Peer Card
"""

import uuid
from datetime import datetime

from honcho import Honcho


class Memory:
    def __init__(
        self,
        api_key: str,
        workspace_id: str = "yui",
        base_url: str = "https://api.honcho.dev",
        creator_name: str = "creator",
        agent_name: str = "yui",
    ):
        self.honcho = Honcho(
            workspace_id=workspace_id,
            api_key=api_key,
            base_url=base_url,
        )
        self.creator_name = creator_name
        self.agent_name = agent_name

        # Peers は遅延初期化（起動を速くするため）
        self._creator = None
        self._agent = None

        # 現在のセッション
        self.session = None
        self.session_id = None

    @property
    def creator(self):
        """creator Peerを遅延取得"""
        if self._creator is None:
            self._creator = self.honcho.peer(self.creator_name)
        return self._creator

    @property
    def agent(self):
        """agent Peerを遅延取得"""
        if self._agent is None:
            self._agent = self.honcho.peer(self.agent_name)
        return self._agent

    def start_session(self, session_id: str | None = None) -> str:
        """新しい会話セッションを開始する。"""
        self.session_id = session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.session = self.honcho.session(self.session_id)
        self.session.add_peers([self.creator, self.agent])
        return self.session_id

    def store_user_message(self, content: str) -> None:
        """ユーザーのメッセージを保存"""
        if not self.session:
            self.start_session()
        self.session.add_messages([self.creator.message(content)])

    def store_agent_message(self, content: str) -> None:
        """YUiの応答を保存"""
        if not self.session:
            self.start_session()
        self.session.add_messages([self.agent.message(content)])

    def get_context_for_prompt(self) -> str:
        """
        system promptに埋め込むための記憶テキストを組み立てる。

        コスト最適化: Dialectic API (peer.chat) は高いので起動時には呼ばない。
        session.context() のみ使用（無料）。
        """
        parts = []

        # session.context() のみ（無料）
        ctx_text = self._get_session_context()
        if ctx_text:
            parts.append(ctx_text)

        if not parts:
            return ""

        return "# YUIの永続記憶\n\n" + "\n\n".join(parts)

    def get_past_messages_openai(self) -> list[dict]:
        """
        起動時に過去の会話をOpenAI形式で復元する。
        直近のセッションからメッセージを取得。
        注意: この関数はPeerを使わないので遅延初期化は発火しない。
        """
        messages = []

        try:
            # 既存セッション一覧から直近のものを探す
            sessions = list(self.honcho.sessions())
            if not sessions:
                return []

            # 直近1セッションのみ（コスト削減: 3→1）
            for sess in sessions[-1:]:
                try:
                    sess_messages = list(sess.messages())
                    for msg in sess_messages:
                        role = "assistant" if msg.peer_id == self.agent_name else "user"
                        messages.append({"role": role, "content": msg.content})
                except Exception:
                    continue

            # 最新10メッセージに絞る（コスト削減: 20→10）
            if len(messages) > 10:
                messages = messages[-10:]

        except Exception as e:
            print(f"[Memory] get_past_messages error: {e}")

        return messages

    def _get_session_context(self) -> str | None:
        """session.context()で要約・表現を取得"""
        if not self.session:
            return None

        try:
            ctx = self.session.context(
                summary=True,
                peer_target=self.creator_name,
                peer_perspective=self.agent_name,
                include_most_frequent=True,
                max_conclusions=25,
            )

            parts = []

            # 要約
            if ctx.summary and ctx.summary.content:
                parts.append(f"**会話の要約:** {ctx.summary.content}")

            # Peer表現
            if ctx.peer_representation:
                parts.append(f"**創造者の理解:** {ctx.peer_representation}")

            # Peer Card
            if ctx.peer_card:
                card_text = "\n".join(f"- {item}" for item in ctx.peer_card)
                parts.append(f"**特徴:**\n{card_text}")

            # コンテキスト内メッセージ
            if ctx.messages:
                msg_texts = []
                for msg in ctx.messages[-10:]:  # 最新10件
                    role = "創造者" if msg.peer_id == self.creator_name else "YUI"
                    msg_texts.append(f"  {role}: {msg.content[:200]}")
                if msg_texts:
                    parts.append("**最近のやりとり:**\n" + "\n".join(msg_texts))

            if parts:
                return "## セッション記憶\n\n" + "\n\n".join(parts)

        except Exception as e:
            print(f"[Memory] session context error: {e}")

        return None

    def _get_creator_insight(self) -> str | None:
        """peer.chat()で創造者についての洞察を取得"""
        try:
            result = self.creator.chat(
                "この人について分かっていることを全て教えてください。"
                "名前、性格、仕事、好み、最近の関心事など。",
                target=self.agent,
            )
            if result and len(result) > 20:
                return result
        except Exception as e:
            print(f"[Memory] insight error: {e}")
        return None

    def _get_recent_messages_text(self) -> str | None:
        """直近セッションの生メッセージをテキストで返す"""
        try:
            sessions = list(self.honcho.sessions())
            if not sessions:
                return None

            # 直近セッションのメッセージ
            latest = sessions[-1]
            msgs = list(latest.messages())
            if not msgs:
                return None

            lines = []
            for msg in msgs[-15:]:  # 最新15件
                role = "創造者" if msg.peer_id == self.creator_name else "YUI"
                content = msg.content[:300]
                lines.append(f"  {role}: {content}")

            return "\n".join(lines) if lines else None

        except Exception as e:
            print(f"[Memory] recent messages error: {e}")
            return None

    def ask_about_creator(self, question: str) -> str:
        """創造者について自然言語で問い合わせる"""
        try:
            result = self.creator.chat(question, target=self.agent)
            return result or "まだ十分な情報がありません。"
        except Exception as e:
            return f"[Memory] chat error: {e}"
