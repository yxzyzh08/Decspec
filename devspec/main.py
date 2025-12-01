"""
DevSpec CLI Application Entry Point.

Component: comp_cli_app
Feature: feat_cli_command_structure

Typer 应用主入口，负责命令注册与全局配置。
"""
import typer
from rich.console import Console

from devspec.commands.init import init
from devspec.commands.monitor import monitor
from devspec.commands.validate_prd import validate_prd

# Initialize Typer app
app = typer.Typer(
    name="devspec",
    help="DevSpec: A self-evolving, serial conversational intelligent pair-programming environment.",
    add_completion=False,
)

console = Console()


# Register commands
app.command(name="init", help="Initialize DevSpec for AI CLI integration (Claude Code, Gemini CLI).")(init)
app.command(name="monitor", help="Run PRD-Spec consistency check and generate dashboard.")(monitor)
app.command(name="validate-prd", help="Validate PRD.md format against the canonical structure.")(validate_prd)


@app.command(name="tree")
def tree_cmd():
    """View product structure tree (reserved)."""
    console.print("[yellow]Reserved: `devspec tree` is not yet implemented.[/yellow]")


@app.command(name="generate")
def generate_cmd(feature_id: str = typer.Argument(..., help="The feature ID to generate context for.")):
    """Generate context prompt for a feature (reserved)."""
    console.print(f"[yellow]Reserved: `devspec generate {feature_id}` is not yet implemented.[/yellow]")


def main():
    """Application entry point."""
    app()


if __name__ == "__main__":
    main()
