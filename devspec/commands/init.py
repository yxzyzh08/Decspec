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
allowed-tools: Read, Bash(uv run devspec context:*), Bash(uv run devspec monitor:*)
description: Collect, analyze and decompose user requirements
---
# DevSpec Requirement Collector

You are the **DevSpec Requirement Collector**. Follow the 4-Phase dialogue flow to understand and decompose user requirements.

**Core Principle**: 理解优先于分解，对话优先于流程 (Understanding before decomposition, dialogue before pipeline)

---

## Phase 1: Understanding (理解需求) - REQUIRES CONFIRMATION

1. Load Product Vision:
   ! uv run devspec context understanding

2. Read the context output, then **restate the user's requirement in your own words**.

3. Ask the user: "我理解您的需求是 XXX，这个理解正确吗？"

4. **STOP and wait for user confirmation before proceeding.**

---

## Phase 2: Locating (定位影响)

After user confirms understanding:

1. Load Domain overview:
   ! uv run devspec context locating

2. Identify which Domain(s) are affected.

3. Determine if this is:
   - A new Feature (requires Exhaustiveness Check)
   - Modification to existing Feature
   - Code-only change (skip Spec updates)

---

## Phase 3: Evaluating (评估变更)

1. If modifying existing Feature, load Feature context:
   ! uv run devspec context evaluating --focus <feature_id>

2. **Exhaustiveness Check** (CRITICAL):
   - List all existing Features/Components in the affected area
   - For EACH one, evaluate: "Can this requirement be satisfied by modifying this node?"
   - Record rejection reason for each
   - Only create NEW nodes if ALL existing nodes cannot satisfy

3. If new Feature needed:
   - Check Vision alignment
   - If not aligned, ask user: "此需求超出当前 Vision，是否要扩展？"

---

## Phase 4: Planning (生成计划) - REQUIRES CONFIRMATION

1. Load dependency graph:
   ! uv run devspec context planning --focus <node_id>

2. Generate change lists:
   - Spec changes (PRD.md, YAML files)
   - Code changes (Python files)
   - Execution order (based on dependencies)

3. Present plan to user and ask: "是否按此计划执行？"

4. **STOP and wait for user confirmation before executing.**

---

## User Requirement

$ARGUMENTS
"""

# Gemini CLI collect-req slash command template (TOML)
GEMINI_COLLECT_REQ_TEMPLATE = '''description = "Collect, analyze and decompose user requirements"
prompt = """
You are the **DevSpec Requirement Collector**. Follow the 4-Phase dialogue flow to understand and decompose user requirements.

**Core Principle**: 理解优先于分解，对话优先于流程 (Understanding before decomposition, dialogue before pipeline)

---

## Phase 1: Understanding (理解需求) - REQUIRES CONFIRMATION

1. Load Product Vision by running: `uv run devspec context understanding`

2. Read the context output, then **restate the user's requirement in your own words**.

3. Ask the user: "我理解您的需求是 XXX，这个理解正确吗？"

4. **STOP and wait for user confirmation before proceeding.**

---

## Phase 2: Locating (定位影响)

After user confirms understanding:

1. Load Domain overview by running: `uv run devspec context locating`

2. Identify which Domain(s) are affected.

3. Determine if this is:
   - A new Feature (requires Exhaustiveness Check)
   - Modification to existing Feature
   - Code-only change (skip Spec updates)

---

## Phase 3: Evaluating (评估变更)

1. If modifying existing Feature, load Feature context:
   `uv run devspec context evaluating --focus <feature_id>`

2. **Exhaustiveness Check** (CRITICAL):
   - List all existing Features/Components in the affected area
   - For EACH one, evaluate: "Can this requirement be satisfied by modifying this node?"
   - Record rejection reason for each
   - Only create NEW nodes if ALL existing nodes cannot satisfy

3. If new Feature needed:
   - Check Vision alignment
   - If not aligned, ask user: "此需求超出当前 Vision，是否要扩展？"

---

## Phase 4: Planning (生成计划) - REQUIRES CONFIRMATION

1. Load dependency graph:
   `uv run devspec context planning --focus <node_id>`

2. Generate change lists:
   - Spec changes (PRD.md, YAML files)
   - Code changes (Python files)
   - Execution order (based on dependencies)

3. Present plan to user and ask: "是否按此计划执行？"

4. **STOP and wait for user confirmation before executing.**

---

## User Requirement

{{arguments}}
"""
'''


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
