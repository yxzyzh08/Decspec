"""
SpecView Server - FastAPI server core for SpecGraph Viewer.

This module provides the main FastAPI application factory and server startup
functionality for the SpecGraph Viewer web interface.

Component: comp_specview_server
Feature: feat_specview_dashboard_core
"""

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from devspec.core.graph_database import GraphDatabase


# =============================================================================
# Data Models
# =============================================================================

class NavItem(BaseModel):
    """Navigation guide item for home page."""

    view: str
    icon: str
    title: str
    purpose: str
    best_for: str
    url: str


# =============================================================================
# Constants
# =============================================================================

NAV_GUIDE: List[NavItem] = [
    NavItem(
        view="Hierarchy View",
        icon="tree",
        title="层级结构",
        purpose="从整体到细节理解产品架构",
        best_for="初次接触产品的用户",
        url="/hierarchy",
    ),
    NavItem(
        view="Design View",
        icon="lightbulb",
        title="设计知识",
        purpose="理解设计决策和执行规范",
        best_for="需要理解'为什么'和'怎么做'的用户",
        url="/design",
    ),
    NavItem(
        view="Relations View",
        icon="git-branch",
        title="依赖关系",
        purpose="理解节点间的依赖和实现关系",
        best_for="分析影响范围或追溯依赖链的用户",
        url="/relation",
    ),
    NavItem(
        view="Search",
        icon="search",
        title="全局搜索",
        purpose="快速定位特定节点",
        best_for="知道目标节点ID或名称的用户",
        url="/search",
    ),
]

# Template directory (relative to project root)
TEMPLATES_DIR = Path("templates")


# =============================================================================
# Global instances (set during app creation)
# =============================================================================

_db: Optional[GraphDatabase] = None
_templates: Optional[Jinja2Templates] = None


def get_db() -> GraphDatabase:
    """Get the global database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call create_app() first.")
    return _db


def get_templates() -> Jinja2Templates:
    """Get the global Jinja2Templates instance."""
    if _templates is None:
        raise RuntimeError("Templates not initialized. Call create_app() first.")
    return _templates


# =============================================================================
# Public API
# =============================================================================

def get_navigation_guide() -> List[NavItem]:
    """
    Get navigation guide items for home page.

    Returns:
        List of NavItem for the four main views (Hierarchy, Design, Relations, Search)
    """
    return NAV_GUIDE


def create_app(
    db_path: Optional[Path] = None,
    templates_dir: Optional[Path] = None,
) -> FastAPI:
    """
    Create and configure FastAPI application instance.

    Args:
        db_path: Path to SQLite database file. Defaults to .specgraph/.runtime/specgraph.db
        templates_dir: Path to Jinja2 templates directory. Defaults to templates/

    Returns:
        Configured FastAPI application
    """
    global _db, _templates

    # Initialize database
    _db = GraphDatabase(db_path)

    # Resolve templates directory
    if templates_dir is None:
        templates_dir = TEMPLATES_DIR

    # Ensure templates directory exists
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Jinja2 templates
    _templates = Jinja2Templates(directory=str(templates_dir))

    # Create FastAPI app
    app = FastAPI(
        title="SpecGraph Viewer",
        description="Web interface for browsing the SpecGraph knowledge base",
        version="0.1.0",
    )

    # Mount static files if directory exists
    static_dir = templates_dir / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Import and register routers
    from devspec.specview.routes import (
        home_router,
        hierarchy_router,
        design_router,
        relation_router,
        search_router,
    )

    app.include_router(home_router)
    app.include_router(hierarchy_router, prefix="/hierarchy")
    app.include_router(design_router, prefix="/design")
    app.include_router(relation_router, prefix="/relation")
    app.include_router(search_router, prefix="/search")

    return app


def serve(port: int = 8000, host: str = "127.0.0.1") -> None:
    """
    Start the local web server for SpecGraph viewing.

    Args:
        port: Server port number (default 8000)
        host: Server host address (default 127.0.0.1)
    """
    import uvicorn
    from rich.console import Console

    console = Console()

    # Check if templates directory exists
    if not TEMPLATES_DIR.exists():
        console.print(
            f"[yellow]Warning: Templates directory '{TEMPLATES_DIR}' not found. "
            "Creating with default templates...[/yellow]"
        )
        _create_default_templates(TEMPLATES_DIR)

    # Create app
    app = create_app()

    # Print startup message
    console.print(f"\n[bold green]SpecGraph Viewer[/bold green]")
    console.print(f"[dim]Starting server at[/dim] http://{host}:{port}")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            console.print(
                f"[red]Error: Port {port} is already in use. "
                f"Try a different port with --port option.[/red]"
            )
        else:
            raise


def _create_default_templates(templates_dir: Path) -> None:
    """Create default template files if they don't exist."""
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Create base.html
    base_html = templates_dir / "base.html"
    if not base_html.exists():
        base_html.write_text(_DEFAULT_BASE_TEMPLATE, encoding="utf-8")

    # Create home.html
    home_html = templates_dir / "home.html"
    if not home_html.exists():
        home_html.write_text(_DEFAULT_HOME_TEMPLATE, encoding="utf-8")

    # Create partials directory
    partials_dir = templates_dir / "partials"
    partials_dir.mkdir(exist_ok=True)


# =============================================================================
# Default Templates
# =============================================================================

_DEFAULT_BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}SpecGraph Viewer{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <style>
    .node-feature { border-left-color: #3B82F6; }
    .node-component { border-left-color: #10B981; }
    .node-design { border-left-color: #8B5CF6; }
    .node-domain { border-left-color: #F59E0B; }
  </style>
</head>
<body class="bg-gray-50 min-h-screen">
  <header class="bg-gray-800 text-white p-4 shadow-lg">
    <div class="container mx-auto flex justify-between items-center">
      <a href="/" class="text-xl font-bold hover:text-blue-300">DevSpec</a>
      <nav class="flex gap-6">
        <a href="/" class="hover:text-blue-300">Home</a>
        <a href="/hierarchy" class="hover:text-blue-300">Hierarchy</a>
        <a href="/design" class="hover:text-blue-300">Design</a>
        <a href="/relation" class="hover:text-blue-300">Relations</a>
      </nav>
      <form action="/search" method="get" class="flex">
        <input type="search" name="q" placeholder="搜索节点..."
               class="px-3 py-1 rounded-l text-black focus:outline-none focus:ring-2 focus:ring-blue-500">
        <button type="submit" class="bg-blue-600 px-3 py-1 rounded-r hover:bg-blue-700">
          搜索
        </button>
      </form>
    </div>
  </header>

  <nav id="breadcrumb" class="bg-gray-100 px-4 py-2 text-sm border-b">
    <div class="container mx-auto">
      {% block breadcrumb %}
      <a href="/" class="text-blue-600 hover:underline">DevSpec</a>
      {% endblock %}
    </div>
  </nav>

  <main id="main-content" class="container mx-auto py-6 px-4">
    {% block content %}{% endblock %}
  </main>

  <footer class="bg-gray-800 text-gray-400 text-center py-4 mt-8">
    <p>SpecGraph Viewer - Powered by DevSpec</p>
  </footer>
</body>
</html>
'''

_DEFAULT_HOME_TEMPLATE = '''{% extends "base.html" %}

{% block title %}SpecGraph Viewer - Home{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
  <!-- Product Overview -->
  <section class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-2">{{ product.name }}</h1>
    <p class="text-gray-500 mb-4">Version {{ product.version }}</p>
    {% if product.vision %}
    <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
      <h2 class="font-semibold text-blue-800 mb-2">Product Vision</h2>
      <p class="text-gray-700 whitespace-pre-line">{{ product.vision }}</p>
    </div>
    {% endif %}
  </section>

  <!-- Navigation Guide -->
  <section class="mb-8">
    <h2 class="text-xl font-semibold text-gray-800 mb-4">选择探索路径</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {% for nav in nav_guide %}
      <a href="{{ nav.url }}" class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-l-4 border-blue-500">
        <div class="flex items-center mb-2">
          <span class="text-2xl mr-3">
            {% if nav.icon == 'tree' %}🌳
            {% elif nav.icon == 'lightbulb' %}💡
            {% elif nav.icon == 'git-branch' %}🔗
            {% elif nav.icon == 'search' %}🔍
            {% endif %}
          </span>
          <h3 class="text-lg font-semibold text-gray-800">{{ nav.title }}</h3>
        </div>
        <p class="text-gray-600 mb-2">{{ nav.purpose }}</p>
        <p class="text-sm text-gray-500">适合: {{ nav.best_for }}</p>
      </a>
      {% endfor %}
    </div>
  </section>

  <!-- Quick Stats -->
  <section class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-semibold text-gray-800 mb-4">知识库概览</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
      <div class="bg-purple-50 rounded-lg p-4">
        <div class="text-3xl font-bold text-purple-600">{{ stats.domains }}</div>
        <div class="text-gray-600">Domains</div>
      </div>
      <div class="bg-blue-50 rounded-lg p-4">
        <div class="text-3xl font-bold text-blue-600">{{ stats.features }}</div>
        <div class="text-gray-600">Features</div>
      </div>
      <div class="bg-green-50 rounded-lg p-4">
        <div class="text-3xl font-bold text-green-600">{{ stats.components }}</div>
        <div class="text-gray-600">Components</div>
      </div>
      <div class="bg-amber-50 rounded-lg p-4">
        <div class="text-3xl font-bold text-amber-600">{{ stats.designs }}</div>
        <div class="text-gray-600">Design/Substrate</div>
      </div>
    </div>
  </section>
</div>
{% endblock %}
'''
