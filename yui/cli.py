"""
YUi CLI - 対話インターフェース

richを使ったターミナルUI。
- 起動中は各ステップをリアルタイム表示
- 処理中はスピナーでステータス表示
- 経過時間の表示
- Ctrl+C で処理キャンセル（アプリは終了しない）
- 複数行入力対応: 空行（Enter2回）で送信
"""

import time

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from yui.agent.loop import AgentLoop


console = Console()


def print_banner():
    banner = Text()
    banner.append("Y", style="bold cyan")
    banner.append("U", style="bold magenta")
    banner.append("i", style="bold yellow")
    banner.append("  v0.1", style="dim")

    console.print()
    console.print(Panel(banner, subtitle="Enter twice to send / 'quit' to exit", border_style="cyan"))
    console.print()


def print_yui(response: str, elapsed: float | None = None):
    """YUiの応答を表示"""
    subtitle = f"[dim]{elapsed:.1f}s[/dim]" if elapsed else None
    console.print(Panel(
        Markdown(response),
        title="[bold magenta]YUi[/bold magenta]",
        subtitle=subtitle,
        border_style="magenta",
        padding=(1, 2),
    ))
    console.print()


def read_multiline() -> str | None:
    """
    複数行入力を読む。
    - 1行目: プロンプト付き
    - 2行目以降: "..." プロンプト
    - 空行（Enter2回）で送信
    - Ctrl+C / Ctrl+D で中断
    """
    try:
        first_line = console.input("[bold cyan]you>[/bold cyan] ")
    except (EOFError, KeyboardInterrupt):
        return None

    # 1行目がコマンドならそのまま返す
    stripped = first_line.strip()
    if stripped.lower() in ("quit", "exit", "q", "/reset", "/refresh"):
        return stripped

    lines = [first_line]

    # 1行目が空でなければ、追加行を待つ
    if stripped:
        while True:
            try:
                next_line = console.input("[dim]  ...[/dim] ")
            except (EOFError, KeyboardInterrupt):
                break

            # 空行 = 送信
            if next_line.strip() == "":
                break

            lines.append(next_line)

    result = "\n".join(lines).strip()
    return result if result else ""


def run_with_status(agent: AgentLoop, message: str) -> tuple[str | None, float]:
    """
    agent.run()をスピナー付きで実行。
    リアルタイムでステータスが更新される。
    Ctrl+Cでキャンセル可能。
    """
    status = console.status(
        "[bold magenta]  考え中...[/bold magenta]",
        spinner="dots",
        spinner_style="magenta",
    )

    def on_status(kind: str, text: str):
        if kind == "thinking":
            status.update(f"[bold magenta]  {text}[/bold magenta]")
        elif kind == "tool":
            status.update(f"[bold yellow]  🔧 {text}[/bold yellow]")

    agent.on_status = on_status
    start_time = time.time()

    try:
        status.start()
        response = agent.run(message)
        status.stop()
        elapsed = time.time() - start_time
        agent.on_status = None
        return response, elapsed
    except KeyboardInterrupt:
        status.stop()
        agent.on_status = None
        console.print("[dim]  (中断しました)[/dim]\n")
        return None, 0
    except Exception as e:
        status.stop()
        agent.on_status = None
        raise e


def main():
    print_banner()

    # --- ブート（ステップごとにステータス表示） ---
    boot_start = time.time()
    boot_status = console.status("[dim]起動中...[/dim]", spinner="dots", spinner_style="cyan")
    boot_status.start()

    def on_boot(text: str):
        boot_status.update(f"[dim]  {text}[/dim]")

    try:
        agent = AgentLoop(on_boot_status=on_boot)
    except Exception as e:
        boot_status.stop()
        console.print(f"[bold red]起動エラー:[/bold red] {e}\n")
        return

    boot_status.stop()
    boot_elapsed = time.time() - boot_start

    # ブート結果を1行で表示
    memory_tag = "[green]Honcho[/green]" if agent.memory else "[yellow]local[/yellow]"
    restored = len(agent.conversation)
    restore_tag = f" | [green]{restored} msgs restored[/green]" if restored > 0 else ""
    console.print(f"[dim]  ready in {boot_elapsed:.1f}s | Memory: {memory_tag}{restore_tag}[/dim]")
    console.print()

    # 起動時: YUiから話しかける
    if restored == 0:
        greeting_prompt = (
            "[SYSTEM] これはあなたとユーザーの初めての出会いです。"
            "YUIとして自己紹介をして、ユーザーの名前を聞いてください。"
            "短く、温かく、YUIらしく。"
        )
    else:
        greeting_prompt = (
            "[SYSTEM] ユーザーが戻ってきました。"
            "過去の会話の記憶をもとに、おかえりなさいの挨拶をしてください。"
            "短く、温かく、YUIらしく。"
        )

    try:
        result = run_with_status(agent, greeting_prompt)
        if result[0]:
            print_yui(result[0], result[1])
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}\n")

    # メインループ
    while True:
        user_input = read_multiline()

        # Ctrl+C / Ctrl+D
        if user_input is None:
            console.print("\n[dim]bye.[/dim]")
            break

        # 空入力
        if not user_input:
            continue

        # コマンド
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]bye.[/dim]")
            break
        if user_input.lower() == "/reset":
            agent.reset()
            console.print("[dim]conversation reset.[/dim]\n")
            continue
        if user_input.lower() == "/refresh":
            agent.context_builder.refresh_memory()
            console.print("[dim]memory refreshed.[/dim]\n")
            continue

        console.print()

        try:
            result = run_with_status(agent, user_input)
            if result[0]:
                print_yui(result[0], result[1])
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            console.print()


if __name__ == "__main__":
    main()
