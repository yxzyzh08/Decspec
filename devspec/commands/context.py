"""
Context Command - Output phase-specific context for AI agents.

This module provides the `devspec context` CLI command that outputs
Markdown-formatted context for each phase of the requirement collection flow.

Component: comp_cli_context
Feature: feat_context_assembler, feat_requirement_collector
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from devspec.core.graph_database import GraphDatabase
from devspec.core.graph_sync import GraphSync
from devspec.core.graph_query import GraphQuery
from devspec.core.context_assembler import ContextAssembler, PHASES

# Console for error output (context output goes to stdout directly)
console = Console(stderr=True)

# Phases that require --focus parameter
PHASES_REQUIRING_FOCUS = ["evaluating", "planning", "coding"]


def context(
    phase: str = typer.Argument(
        ...,
        help=f"Phase name: {', '.join(PHASES)}",
    ),
    focus: Optional[str] = typer.Option(
        None,
        "--focus",
        "-f",
        help="Focus node ID (required for evaluating/planning/coding phases)",
    ),
) -> None:
    """
    Output phase-specific context for AI agents.

    This command outputs Markdown-formatted context based on the specified phase.
    The output is designed to be consumed by AI agents during requirement collection.

    Examples:
        devspec context understanding
        devspec context locating
        devspec context evaluating --focus feat_consistency_monitor
        devspec context planning --focus feat_context_assembler
        devspec context coding --focus comp_graph_query
    """
    # Validate phase
    if phase not in PHASES:
        console.print(f"[red]Error:[/red] Invalid phase '{phase}'")
        console.print(f"Valid phases: {', '.join(PHASES)}")
        raise typer.Exit(1)

    # Validate focus requirement
    if phase in PHASES_REQUIRING_FOCUS and not focus:
        console.print(f"[red]Error:[/red] Phase '{phase}' requires --focus parameter")
        console.print(f"Example: devspec context {phase} --focus <node_id>")
        console.print("Run 'devspec monitor' to see available node IDs")
        raise typer.Exit(1)

    # Initialize database and sync
    root_path = Path(".")
    spec_dir = root_path / ".specgraph"
    if not spec_dir.exists():
        console.print("[red]Error:[/red] .specgraph directory not found")
        console.print("Run 'devspec init' first to initialize the project")
        raise typer.Exit(1)

    db_path = spec_dir / ".runtime" / "specgraph.db"
    db = GraphDatabase(db_path)

    # Sync to ensure latest data
    try:
        sync = GraphSync(db, root_path)
        sync.sync_all()
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Database sync failed: {e}")
        console.print("Continuing with existing data...")

    # Initialize query and assembler
    query = GraphQuery(db)
    assembler = ContextAssembler(query)

    # Assemble and output context
    try:
        result = assembler.assemble(phase, focus)
        # Output directly to stdout (no Rich formatting, pure Markdown for AI consumption)
        print(result)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        if "not found" in str(e).lower():
            console.print("Run 'devspec monitor' to see available node IDs")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to assemble context: {e}")
        raise typer.Exit(1)
