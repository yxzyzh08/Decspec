"""
DevSpec Init Command.

Component: comp_cli_init
Feature: feat_cli_command_structure

为 Claude Code 和 Gemini CLI 生成 slash command 文件，使 AI CLI 可直接调用 DevSpec 命令。
"""
from pathlib import Path

from rich.console import Console

console = Console()

# Claude Code slash command template
CLAUDE_MONITOR_TEMPLATE = """---
allowed-tools: Bash(uv run devspec monitor:*)
description: Run DevSpec consistency monitor and generate dashboard
---

# DevSpec Monitor

执行 DevSpec 一致性检查，比对 PRD 与 SpecGraph，生成分层 Dashboard。

! uv run devspec monitor $ARGUMENTS
"""

# Gemini CLI slash command template (same format)
GEMINI_MONITOR_TEMPLATE = """---
description: Run DevSpec consistency monitor and generate dashboard
---

# DevSpec Monitor

执行 DevSpec 一致性检查，比对 PRD 与 SpecGraph，生成分层 Dashboard。

! uv run devspec monitor $ARGUMENTS
"""


def init():
    """
    Initialize DevSpec for AI CLI integration.

    Generates slash command files for Claude Code and Gemini CLI,
    enabling direct invocation of DevSpec commands from AI assistants.
    """
    root_path = Path(".")

    # Define command files to generate
    commands = [
        {
            "path": root_path / ".claude" / "commands" / "devspec-monitor.md",
            "content": CLAUDE_MONITOR_TEMPLATE,
            "cli_name": "Claude Code",
        },
        {
            "path": root_path / ".gemini" / "commands" / "devspec-monitor.md",
            "content": GEMINI_MONITOR_TEMPLATE,
            "cli_name": "Gemini CLI",
        },
    ]

    console.print("[bold blue]DevSpec Init: Generating AI CLI slash commands...[/bold blue]\n")

    for cmd in commands:
        path: Path = cmd["path"]
        content: str = cmd["content"]
        cli_name: str = cmd["cli_name"]

        # Create directory if not exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write command file
        path.write_text(content.strip() + "\n", encoding="utf-8")

        console.print(f"[green]✓[/green] {cli_name}: {path}")

    console.print("\n[bold green]Done![/bold green] You can now use:")
    console.print("  • Claude Code: [cyan]/devspec-monitor[/cyan]")
    console.print("  • Gemini CLI:  [cyan]/devspec-monitor[/cyan]")
