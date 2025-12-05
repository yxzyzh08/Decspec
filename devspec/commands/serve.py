"""
Serve Command - Start the SpecGraph Viewer web server.

This command starts a local FastAPI server for browsing the SpecGraph
knowledge base through a web interface.

Component: comp_cli_app
Feature: feat_specview_dashboard_core
"""

from typing import Optional

import typer
from rich.console import Console


console = Console()


def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Server port number"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host address"),
) -> None:
    """
    Start the SpecGraph Viewer web server.

    Opens a local web interface for browsing the product specification graph.
    Access the viewer at http://localhost:8000 (or your specified port).

    Examples:
        devspec serve              # Start on default port 8000
        devspec serve --port 3000  # Start on port 3000
    """
    try:
        from devspec.specview import serve as start_server
        start_server(port=port, host=host)
    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for serve command.[/red]")
        console.print(f"[dim]Install with: uv pip install fastapi uvicorn jinja2[/dim]")
        console.print(f"[dim]Details: {e}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        raise typer.Exit(1)
