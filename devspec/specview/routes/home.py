"""
Home Router - Home page with navigation guide and product overview.

Component: comp_specview_routes
Feature: feat_specview_dashboard_core
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from devspec.specview.server import get_db, get_templates, get_navigation_guide
from devspec.core.graph_database import NodeModel


router = APIRouter(tags=["home"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """
    Render home page with navigation guide and product overview.

    Returns:
        Rendered home.html template
    """
    templates = get_templates()
    db = get_db()

    # Get product info
    product_info = {
        "name": "DevSpec",
        "version": "0.3.0",
        "vision": None,
    }

    with db.get_session() as session:
        # Get product node
        product = session.exec(
            select(NodeModel).where(NodeModel.type == "product")
        ).first()

        if product:
            product_info["name"] = product.name
            product_info["vision"] = product.description

        # Count nodes by type for stats
        stats = {
            "domains": 0,
            "features": 0,
            "components": 0,
            "designs": 0,
        }

        all_nodes = session.exec(select(NodeModel)).all()
        for node in all_nodes:
            if node.type == "domain":
                stats["domains"] += 1
            elif node.type == "feature":
                stats["features"] += 1
            elif node.type == "component":
                stats["components"] += 1
            elif node.type in ("design", "substrate"):
                stats["designs"] += 1

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "product": product_info,
            "nav_guide": [nav.model_dump() for nav in get_navigation_guide()],
            "stats": stats,
        },
    )
