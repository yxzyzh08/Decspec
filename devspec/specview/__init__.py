"""
SpecGraph Viewer - Web interface for browsing the SpecGraph knowledge base.

This package provides a FastAPI-based web server with Jinja2 templates
for human users to explore the product specification graph.

Domain: dom_specview
"""

from devspec.specview.server import create_app, serve, get_navigation_guide

__all__ = [
    "create_app",
    "serve",
    "get_navigation_guide",
]
