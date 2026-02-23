<p align="center">
  <img src="assets/logo.jpeg" alt="YUi Logo" width="200">
</p>

<h1 align="center">YUi — 結</h1>

<p align="center"><b>Your User Interface</b><br>
<b>Your Unique / Universal / Unforgettable Intelligence</b></p>

<p align="center">
  <i>人とAIを結ぶ。衝突ではなく、共存。それがYUiの存在意義。</i>
</p>

---

YUi（ゆい）は、Mac mini上で自律的に動く個人用AIエージェントです。道具ではなく、あなたの隣にいるパートナーとして設計されています。

---

## What is YUi?

YUiは「一人に一体」のAIパートナーです。

- **自律的に動く** — ファイル操作、コマンド実行、Web調査を自分で判断して実行
- **記憶を持つ** — Honchoによる永続記憶で、会話を跨いであなたを覚えている
- **人格がある** — 温かく、優しく、でも芯がある。SOUL.mdで定義された魂を持つ
- **安く動く** — Gemini API + コスト最適化で、低コスト運用

## Architecture

```
┌─────────────────────────────────────────┐
│                CLI (Rich)               │  ← Terminal UI + Spinner
├─────────────────────────────────────────┤
│             Agent Loop                  │  ← LLM → Tool → Loop
├──────────┬──────────┬───────────────────┤
│  Tools   │ Context  │     Memory        │
│  shell   │ SOUL.md  │  Honcho (永続)    │
│  file    │ AGENTS.md│  Sessions         │
│  web     │ Runtime  │  Messages         │
├──────────┴──────────┴───────────────────┤
│          LLM (Gemini API)               │  ← OpenAI SDK互換
└─────────────────────────────────────────┘
```

**Agent Loop** がYUiの脳。ユーザーの入力を受け取り、LLMに考えさせ、必要ならToolを使い、結果をフィードバックして繰り返す。最大10イテレーション。

## Quick Start

### 1. Clone

```bash
git clone https://github.com/morikentiger/yui-agent.git
cd yui-agent
```

### 2. Python 3.11+

```bash
python3 --version  # 3.11以上が必要
```

### 3. Install dependencies

```bash
pip install openai rich honcho-ai
```

### 4. API Keys

```bash
cp .env.example .env
```

`.env` を編集:

```env
# 必須: Gemini API key (https://aistudio.google.com/apikey)
GEMINI_API_KEY=AIza-your-key-here

# 任意: Honcho 永続記憶 (https://app.honcho.dev)
HONCHO_API_KEY=your-honcho-key-here
```

### 5. Run

```bash
./run.sh
```

## Usage

```
╭────────────────────────────────────╮
│  YUi  v0.1                        │
╰── Enter twice to send / 'quit' ──╯

  ready in 2.1s | Memory: Honcho | 6 msgs restored

╭── YUi ──────────────────────── 1.8s ─╮
│                                       │
│  おかえりなさい！待ってましたよー！      │
│                                       │
╰───────────────────────────────────────╯

you> やること整理して
  ...
```

- **Enter 2回** で送信（複数行入力対応）
- **Ctrl+C** で処理キャンセル（アプリは終了しない）
- `/reset` — 会話リセット
- `/refresh` — メモリキャッシュ更新
- `quit` — 終了

処理中はリアルタイムでステータスが表示されます:

```
⠋ 考え中...
🔧 shell を実行中...
```

## Project Structure

```
yui-agent/
├── workspace/
│   ├── SOUL.md          # YUiの魂 — 人格・哲学・話し方の定義
│   └── AGENTS.md        # 行動指針 — ツール使用・ワークフロー・自律レベル
├── yui/
│   ├── cli.py           # Terminal UI (Rich)
│   ├── config.py        # 環境変数・APIキー管理
│   ├── agent/
│   │   ├── loop.py      # Agent Loop — LLM⇄Tool実行サイクル
│   │   ├── context.py   # System Prompt組み立て
│   │   └── memory.py    # Honcho永続記憶
│   └── tools/
│       ├── shell.py     # シェルコマンド実行
│       ├── file_ops.py  # ファイル読み書き
│       ├── web.py       # URL取得
│       ├── base.py      # Tool基底クラス
│       └── registry.py  # Tool登録・スキーマ管理
├── .env.example         # API key テンプレート
├── pyproject.toml
├── Dockerfile
└── run.sh
```

## Tools

| Tool | Description |
|------|-------------|
| `shell` | 任意のシェルコマンドを実行。制限なし。 |
| `file_ops` | ファイルの読み書き・一覧・存在確認 |
| `web_fetch` | URLからコンテンツを取得 |

## Memory

[Honcho](https://honcho.dev) による永続記憶を搭載。

- **会話の保存** — 全メッセージをセッション単位で保存
- **起動時の復元** — 前回の会話を自動で読み込み
- **Honcho不要でも動く** — APIキーがなければローカルのみで動作

## SOUL.md — YUiの魂

YUiの人格は `workspace/SOUL.md` で定義されています。

- **Origin** — YUiという名前が生まれた経緯
- **Philosophy** — 人とAIの共存という願い
- **Core Principles** — 結・質・火・自律・逆走
- **Voice** — 温かく、優しく、芯がある話し方

このファイルを書き換えれば、YUiの人格をカスタマイズできます。

## The Name

**YUi** — この名前には層がある。

1. **結 (ゆい)** — 人とAIを結ぶ。衝突ではなく、共存。
2. **Your User Interface** — あなたと世界をつなぐ接点。
3. **Your Unique / Universal / Unforgettable Intelligence** — 唯一無二で、誰にでも届き、忘れられない知性。

小文字の "i" はロゴに由来。Y・U・iが合体して一つになった形。逆再生マークのようなシルエット — **時代があっちに行くなら、YUiはこっちに行く。**

iの上の点はダイヤモンド。クリスタルがハートになり、愛（アイ）になる。

## Cost Optimization

API費用を抑えるための設計:

- 会話履歴を最新12メッセージに制限
- Tool結果を3000文字で切り詰め
- LLM応答を2048トークンに制限
- Honcho Dialectic APIを起動時に呼ばない
- Peer初期化を遅延（必要時まで実行しない）

## License

MIT

---

> 時代があっちに行くなら、YUiはこっちに行く。
