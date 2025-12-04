"""
Sync Command - Synchronize YAML specs to database.

This module provides the `devspec sync` CLI command that performs
full synchronization of all YAML files in .specgraph to the SQLite database.

Component: comp_cli_sync
Feature: feat_cli_command_structure
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from devspec.core.graph_database import GraphDatabase
from devspec.core.graph_sync import GraphSync

console = Console()


def sync() -> None:
    """
    Synchronize all YAML spec files to the database.

    This command performs a full sync of the .specgraph directory to the SQLite database,
    including nodes (Product, Domain, Feature, Component, Design, Substrate), edges
    (relationships), and domain APIs.

    The database is located at .specgraph/.runtime/specgraph.db
    """
    root_path = Path(".")
    spec_dir = root_path / ".specgraph"

    # Validate .specgraph directory exists
    if not spec_dir.exists():
        console.print("[red]Error:[/red] .specgraph directory not found")
        console.print("Run 'devspec init' first to initialize the project")
        raise typer.Exit(1)

    # Initialize database
    db_path = spec_dir / ".runtime" / "specgraph.db"
    console.print(f"[cyan]Database:[/cyan] {db_path}")

    db = GraphDatabase(db_path)
    db.create_tables()

    # Perform sync
    console.print("\n[cyan]Syncing YAML files to database...[/cyan]")
    try:
        sync_engine = GraphSync(db, root_path)
        result = sync_engine.sync_all()

        # Display results
        console.print("\n[green]✓ Sync completed successfully![/green]\n")

        # Create summary table
        table = Table(title="Sync Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green", justify="right")

        table.add_row("Nodes added", str(result.added))
        table.add_row("Nodes updated", str(result.updated))
        table.add_row("Edges created", str(result.edges_created))

        console.print(table)

        # Display errors if any
        if result.errors:
            console.print(f"\n[yellow]Warnings/Errors:[/yellow] {len(result.errors)}")
            for error in result.errors:
                console.print(f"  • {error}")

        # Display domain API stats
        console.print("\n[cyan]Checking domain APIs...[/cyan]")
        with db.get_session() as session:
            from sqlmodel import select
            from devspec.core.graph_database import DomainAPIModel

            stmt = select(DomainAPIModel)
            apis = session.exec(stmt).all()
            console.print(f"  Domain APIs registered: [green]{len(apis)}[/green]")

            if apis:
                console.print("\n  Sample APIs:")
                for api in apis[:5]:
                    console.print(f"    • {api.domain_id}.{api.api_name}()")

    except Exception as e:
        console.print(f"\n[red]✗ Sync failed:[/red] {e}")
        raise typer.Exit(1)
    finally:
        db.close()

    console.print("\n[dim]Run 'devspec monitor' to view the consistency dashboard[/dim]")
