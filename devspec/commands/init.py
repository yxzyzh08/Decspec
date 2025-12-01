"""
DevSpec Init Command.

Component: comp_cli_init
Feature: feat_cli_command_structure

为 Claude Code 和 Gemini CLI 生成 slash command 文件，使 AI CLI 可直接调用 DevSpec 命令。
"""
from pathlib import Path

from rich.console import Console

console = Console()

# Claude Code slash command template (Markdown)
CLAUDE_MONITOR_TEMPLATE = """---
allowed-tools: Bash(uv run devspec monitor:*)
description: Run DevSpec consistency monitor and generate dashboard
---
# DevSpec Monitor

Run the consistency check to verify alignment between PRD (Markdown) and SpecGraph (YAML).

**Usage**
! uv run devspec monitor $ARGUMENTS
"""

# Gemini CLI slash command template (TOML)
GEMINI_MONITOR_TEMPLATE = """description = "Run DevSpec consistency monitor and generate dashboard"
prompt = \"\"\"
Run the DevSpec consistency monitor to check alignment between PRD and SpecGraph.
Command: `uv run devspec monitor`
\"\"\"
"""

# Claude Code write-prd slash command template (Markdown)
CLAUDE_WRITE_PRD_TEMPLATE = """---
allowed-tools: Read, Edit, Bash(uv run devspec validate-prd:*)
description: Create or update PRD.md based on user requirements
---
# DevSpec Write PRD

You are the **DevSpec PRD Architect**. Your task is to create or update `PRD.md` based on user requirements.

## Instructions

1. **Read the PRD writing rules**: Load `.specgraph/design/des_prompt_prd_writer.md` to understand the canonical structure and rules.

2. **Read current PRD**: Load `PRD.md` to understand the current state.

3. **Apply changes**: Based on the user's requirement below, create or modify `PRD.md` following the rules strictly.

4. **Validate**: After modification, run `uv run devspec validate-prd` to verify the format.

5. **Report**: If validation passes, confirm success. If validation fails, fix the issues and re-validate.

## User Requirement

$ARGUMENTS
"""

# Gemini CLI write-prd slash command template (TOML)
GEMINI_WRITE_PRD_TEMPLATE = """description = "Create or update PRD.md based on user requirements"
prompt = \"\"\"
You are the **DevSpec PRD Architect**. Your task is to create or update `PRD.md` based on user requirements.

## Instructions

1. **Read the PRD writing rules**: Load `.specgraph/design/des_prompt_prd_writer.md` to understand the canonical structure and rules.

2. **Read current PRD**: Load `PRD.md` to understand the current state.

3. **Apply changes**: Based on the user's requirement, create or modify `PRD.md` following the rules strictly.

4. **Validate**: After modification, run `uv run devspec validate-prd` to verify the format.

5. **Report**: If validation passes, confirm success. If validation fails, fix the issues and re-validate.

## User Requirement

{{arguments}}
\"\"\"
"""


def init() -> None:
    """
    Generate AI CLI slash command files.

    Creates slash command files for Claude Code and Gemini CLI,
    enabling direct invocation of DevSpec commands from AI assistants.
    Skips files that already exist.
    """
    root_path = Path(".")

    # Define command files to generate
    commands = [
        {
            "path": root_path / ".claude" / "commands" / "devspec-monitor.md",
            "content": CLAUDE_MONITOR_TEMPLATE,
            "cli_name": "Claude Code (monitor)",
        },
        {
            "path": root_path / ".gemini" / "commands" / "devspec-monitor.toml",
            "content": GEMINI_MONITOR_TEMPLATE,
            "cli_name": "Gemini CLI (monitor)",
        },
        {
            "path": root_path / ".claude" / "commands" / "devspec-write-prd.md",
            "content": CLAUDE_WRITE_PRD_TEMPLATE,
            "cli_name": "Claude Code (write-prd)",
        },
        {
            "path": root_path / ".gemini" / "commands" / "devspec-write-prd.toml",
            "content": GEMINI_WRITE_PRD_TEMPLATE,
            "cli_name": "Gemini CLI (write-prd)",
        },
    ]

    console.print("[bold blue]DevSpec Init: Generating AI CLI slash commands...[/bold blue]\n")

    for cmd in commands:
        path: Path = cmd["path"]
        content: str = cmd["content"]
        cli_name: str = cmd["cli_name"]

        # Check if file already exists
        if path.exists():
            console.print(f"[yellow]⚠ {cli_name}: {path} already exists, skipping.[/yellow]")
            continue

        # Create parent directory if not exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write command file
        path.write_text(content.strip() + "\n", encoding="utf-8")

        console.print(f"[green]✓[/green] {cli_name}: {path}")

    console.print("\n[bold green]Done![/bold green] You can now use:")
    console.print("  • Claude Code: [cyan]/devspec-monitor[/cyan], [cyan]/devspec-write-prd[/cyan]")
    console.print("  • Gemini CLI:  [cyan]/devspec-monitor[/cyan], [cyan]/devspec-write-prd[/cyan]")
