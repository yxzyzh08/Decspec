"""
DevSpec CLI Application Entry Point.

Component: comp_cli_app
Feature: feat_cli_command_structure

Typer 应用主入口，负责命令注册与全局配置。
"""
import os
from pathlib import Path

import typer
from rich.console import Console

from devspec.commands.init import init
from devspec.commands.monitor import monitor
from devspec.commands.validate_prd import validate_prd
from devspec.commands.context import context
from devspec.commands.sync import sync
from devspec.commands.serve import serve
from devspec.frontend import frontend_app
from devspec.infra.cli_debug_logger import debug_command
from devspec.infra.config import load_env_file, get_config
from devspec.infra.logger import configure_logging

# Initialize Typer app
app = typer.Typer(
    name="devspec",
    help="DevSpec: A self-evolving, serial conversational intelligent pair-programming environment.",
    add_completion=False,
)

console = Console()


# === Global Options Callback ===


@app.callback()
def global_options(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode (logs command execution details to logs/devspec_cli_debug.log)."
    )
) -> None:
    """Global options callback for --debug flag."""
    if debug:
        os.environ['DEBUG'] = 'true'


# === Register Commands with Debug Decorator ===

app.command(name="init", help="Initialize DevSpec for AI CLI integration (Claude Code, Gemini CLI).")(debug_command(init))
app.command(name="monitor", help="Run PRD-Spec consistency check and generate dashboard.")(debug_command(monitor))
app.command(name="validate-prd", help="Validate PRD.md format against the canonical structure.")(debug_command(validate_prd))
app.command(name="context", help="Output phase-specific context for AI agents.")(debug_command(context))
app.command(name="sync", help="Synchronize all YAML spec files to the database.")(debug_command(sync))

# Register subcommand groups
app.add_typer(frontend_app, name="frontend")


app.command(name="serve", help="Start the SpecGraph Viewer web server.")(debug_command(serve))


@app.command(name="generate")
@debug_command
def generate_cmd(feature_id: str = typer.Argument(..., help="The feature ID to generate context for.")):
    """Generate context prompt for a feature (reserved)."""
    console.print(f"[yellow]Reserved: `devspec generate {feature_id}` is not yet implemented.[/yellow]")


def main():
    """Application entry point.

    Performs one-time initialization before starting the Typer app:
    1. Load .env file (if exists)
    2. Configure global logging based on config
    3. Start Typer application
    """
    # Load .env file (if exists)
    load_env_file()

    # Configure global logging from config
    log_level = get_config('logging.level', 'INFO')
    log_format = get_config('logging.format', 'rich')
    configure_logging(level=log_level, format=log_format)

    # Start Typer application
    app()


if __name__ == "__main__":
    main()
