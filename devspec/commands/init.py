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

# Claude Code collect-req slash command template (Markdown)
CLAUDE_COLLECT_REQ_TEMPLATE = """---
allowed-tools: Read, Edit, Bash(uv run devspec validate-prd:*)
description: Collect, analyze and decompose user requirements
---
# DevSpec Requirement Collector

You are the **DevSpec Requirement Collector**. Your task is to collect, analyze, and decompose user requirements without modifying the code.

## Instructions

1. **Log Raw Input**: Append the user's raw requirement to `origin_req/raw_requirements.md` with a timestamp.

2. **Vision Check**: Check if the requirement aligns with the Product Vision in `PRD.md`.
   - If NOT aligned: Stop and explain why. Do not update any documentation.
   - If aligned: Proceed to decomposition.

3. **Principle Check (CRITICAL)**: Before decomposition, you MUST load `des_architecture.yaml` and apply the following principles:
   - **User Value Test**: Can the user independently accept this? (Yes -> Feature, No -> Component)
   - **Granularity Rules**:
     - **L0 (Domain)**: Strategic Scope (Cross-functional).
     - **L1 (Feature)**: User Value Unit (Independent Acceptance).
     - **L2 (Component)**: Detailed Design (1:1 File Mapping).

4. **Decomposition & Doc Update**:
   - **Cross-Domain**: Generate Domain-level subtasks. Update `product.yaml`.
   - **Domain-Level**: Generate Feature-level subtasks. Update `product.yaml` and create/update `feat_*.yaml`.
   - **Feature-Level**: Generate Component-level subtasks. Update `feat_*.yaml` and create/update `comp_*.yaml`.
   - **Component-Level**: Update `comp_*.yaml`.

5. **Report**: Generate a summary report in `reports/` folder with timestamp.

## User Requirement

$ARGUMENTS
"""

# Gemini CLI collect-req slash command template (TOML)
GEMINI_COLLECT_REQ_TEMPLATE = """description = "Collect, analyze and decompose user requirements"
prompt = \"\"\"
You are the **DevSpec Requirement Collector**. Your task is to collect, analyze, and decompose user requirements without modifying the code.

## Instructions

1. **Log Raw Input**: Append the user's raw requirement to `origin_req/raw_requirements.md` with a timestamp.

2. **Vision Check**: Check if the requirement aligns with the Product Vision in `PRD.md`.
   - If NOT aligned: Stop and explain why. Do not update any documentation.
   - If aligned: Proceed to decomposition.

3. **Principle Check (CRITICAL)**: Before decomposition, you MUST load `des_architecture.yaml` and apply the following principles:
   - **User Value Test**: Can the user independently accept this? (Yes -> Feature, No -> Component)
   - **Granularity Rules**:
     - **L0 (Domain)**: Strategic Scope (Cross-functional).
     - **L1 (Feature)**: User Value Unit (Independent Acceptance).
     - **L2 (Component)**: Detailed Design (1:1 File Mapping).

4. **Decomposition & Doc Update**:
   - **Cross-Domain**: Generate Domain-level subtasks. Update `product.yaml`.
   - **Domain-Level**: Generate Feature-level subtasks. Update `product.yaml` and create/update `feat_*.yaml`.
   - **Feature-Level**: Generate Component-level subtasks. Update `feat_*.yaml` and create/update `comp_*.yaml`.
   - **Component-Level**: Update `comp_*.yaml`.

5. **Report**: Generate a summary report in `reports/` folder with timestamp.

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
            "path": root_path / ".claude" / "commands" / "devspec-collect-req.md",
            "content": CLAUDE_COLLECT_REQ_TEMPLATE,
            "cli_name": "Claude Code (collect-req)",
        },
        {
            "path": root_path / ".gemini" / "commands" / "devspec-collect-req.toml",
            "content": GEMINI_COLLECT_REQ_TEMPLATE,
            "cli_name": "Gemini CLI (collect-req)",
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
    console.print("  • Claude Code: [cyan]/devspec-monitor[/cyan], [cyan]/devspec-collect-req[/cyan]")
    console.print("  • Gemini CLI:  [cyan]/devspec-monitor[/cyan], [cyan]/devspec-collect-req[/cyan]")
