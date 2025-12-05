"""
SpecView Routes - API route handlers for SpecGraph Viewer.

This package contains all FastAPI routers for different views:
- home: Home page with navigation guide
- hierarchy: Tree structure view (Product -> Domain -> Feature -> Component)
- design: Design/Substrate knowledge view
- relation: Dependency relationship view
- search: Full-text search functionality

Component: comp_specview_routes
"""

from devspec.specview.routes.home import router as home_router
from devspec.specview.routes.hierarchy import router as hierarchy_router
from devspec.specview.routes.design import router as design_router
from devspec.specview.routes.relation import router as relation_router
from devspec.specview.routes.search import router as search_router

__all__ = [
    "home_router",
    "hierarchy_router",
    "design_router",
    "relation_router",
    "search_router",
]
