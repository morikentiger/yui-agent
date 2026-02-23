"""
YUi Safe CLI - セキュアな対話インターフェース

Dockerコンテナ内での安全な実行用
"""

import argparse
import time

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from yui.agent.loop import AgentLoop
from yui.tools.safe_registry import safe_registry


console = Console()


def print_banner():
    banner = Text()
    banner.append("Y", style="bold cyan")
    banner.append("U", style="bold magenta")
    banner.append("i", style="bold yellow")
    banner.append("  [SAFE MODE]", style="dim green")

    console.print()
    console.print(Panel(
        banner, 
        subtitle="Secure sandbox environment / Enter twice to send / 'quit' to exit", 
        border_style="green"
    ))
    console.print()


def print_yui(response: str, elapsed: float | None = None):
    """YUiの応答を表示"""
    subtitle = f"[dim]{elapsed:.1f}s[/dim]" if elapsed else None
    console.print(Panel(
        Markdown(response),
        title="[bold magenta]YUi[/bold magenta] [green][SAFE][/green]",
        subtitle=subtitle,
        border_style="magenta",
        padding=(1, 2),
    ))
    console.print()


def read_multiline() -> str | None:
    """複数行入力を読む"""
    try:
        first_line = console.input("[bold cyan]you>[/bold cyan] ")
    except (EOFError, KeyboardInterrupt):
        return None

    stripped = first_line.strip()
    if stripped.lower() in ("quit", "exit", "q", "/reset", "/refresh"):
        return stripped

    lines = [first_line]

    if stripped:
        while True:
            try:
                next_line = console.input("[dim]  ...[/dim] ")
            except (EOFError, KeyboardInterrupt):
                break

            if next_line.strip() == "":
                break

            lines.append(next_line)

    result = "\n".join(lines).strip()
    return result if result else ""


def run_with_status(agent: AgentLoop, message: str):
    """agent.run()をスピナー付きで実行"""
    status = console.status(
        "[bold magenta]  考え中...[/bold magenta]",
        spinner="dots",
        spinner_style="magenta",
    )

    def on_status(kind: str, text: str):
        if kind == "thinking":
            status.update(f"[bold magenta]  {text}[/bold magenta]")
        elif kind == "tool":
            status.update(f"[bold yellow]  🔧 {text} [green](safe)[/green][/bold yellow]")

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/app/workspace", help="Workspace directory")
    args = parser.parse_args()

    print_banner()
    
    # セーフモードでエージェントを初期化
    agent = AgentLoop(
        tool_registry=safe_registry,
        workspace_path=args.workspace
    )

    console.print("[dim green]🛡️  安全なサンドボックス環境で動作中[/dim green]\n")
    console.print(f"[dim]ワークスペース: {args.workspace}[/dim]\n")
    
    # 利用可能なツールを表示
    tools = safe_registry.list_tools()
    console.print(f"[dim]利用可能なツール: {', '.join(tools)}[/dim]\n")

    while True:
        user_input = read_multiline()
        
        if user_input is None:
            break

        if user_input.lower() in ("quit", "exit", "q"):
            break

        if not user_input.strip():
            continue

        result = run_with_status(agent, user_input)
        if result:
            response, elapsed = result
            print_yui(response, elapsed)

    console.print("\n[dim]またお会いしましょう！[/dim]")


if __name__ == "__main__":
    main()