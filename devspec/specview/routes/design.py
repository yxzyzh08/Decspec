"""
Design Router - Design/Substrate knowledge view.

Component: comp_specview_routes
Feature: feat_specview_design_view
"""

from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from devspec.specview.server import get_db, get_templates
from devspec.core.graph_database import NodeModel


router = APIRouter(tags=["design"])


# Knowledge type guide - helps users understand when to read Design vs Substrate
KNOWLEDGE_TYPE_GUIDE = [
    {
        "type": "Design (des_*)",
        "icon": "lightbulb",
        "color": "blue",
        "question": "为什么这样设计？",
        "when_to_read": "当你想理解决策背后的原因时",
        "typical_content": ["设计原则", "架构决策", "权衡取舍"],
    },
    {
        "type": "Substrate (sub_*)",
        "icon": "ruler",
        "color": "green",
        "question": "怎么执行？有什么约束？",
        "when_to_read": "当你要写代码或创建文件时",
        "typical_content": ["格式规范", "命名约定", "验证规则"],
    },
]


@router.get("/", response_class=HTMLResponse)
async def design_view(request: Request) -> HTMLResponse:
    """
    Render design view with Design and Substrate node lists.

    Returns:
        Rendered design.html template
    """
    templates = get_templates()
    db = get_db()

    designs = []
    substrates = []

    with db.get_session() as session:
        all_nodes = session.exec(select(NodeModel)).all()

        for node in all_nodes:
            node_info = {
                "id": node.id,
                "name": node.name,
                "description": node.description,
                "intent": node.intent,
            }

            if node.type == "design":
                designs.append(node_info)
            elif node.type == "substrate":
                substrates.append(node_info)

    return templates.TemplateResponse(
        "design.html",
        {
            "request": request,
            "designs": designs,
            "substrates": substrates,
            "knowledge_guide": KNOWLEDGE_TYPE_GUIDE,
            "breadcrumbs": [{"name": "Design", "url": None}],
        },
    )


@router.get("/design/{design_id}", response_class=HTMLResponse)
async def design_detail(request: Request, design_id: str) -> HTMLResponse:
    """
    Render Design node detail page.

    Args:
        design_id: Design node ID (e.g., des_philosophy)

    Returns:
        Rendered design_detail.html template
    """
    templates = get_templates()
    db = get_db()

    with db.get_session() as session:
        node = session.get(NodeModel, design_id)

        if not node or node.type != "design":
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Design node not found: {design_id}",
                },
                status_code=404,
            )

        # Parse raw_yaml if available to get additional fields
        content = {}
        if node.raw_yaml:
            import yaml
            try:
                content = yaml.safe_load(node.raw_yaml)
            except yaml.YAMLError:
                pass

        breadcrumbs = [
            {"name": "Design", "url": "/design"},
            {"name": node.name, "url": None},
        ]

        return templates.TemplateResponse(
            "design_detail.html",
            {
                "request": request,
                "node": {
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "description": node.description,
                    "intent": node.intent,
                },
                "content": content,
                "breadcrumbs": breadcrumbs,
            },
        )


@router.get("/substrate/{substrate_id}", response_class=HTMLResponse)
async def substrate_detail(request: Request, substrate_id: str) -> HTMLResponse:
    """
    Render Substrate node detail page.

    Args:
        substrate_id: Substrate node ID (e.g., sub_tech_stack)

    Returns:
        Rendered substrate_detail.html template
    """
    templates = get_templates()
    db = get_db()

    with db.get_session() as session:
        node = session.get(NodeModel, substrate_id)

        if not node or node.type != "substrate":
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Substrate node not found: {substrate_id}",
                },
                status_code=404,
            )

        # Parse raw_yaml if available
        content = {}
        if node.raw_yaml:
            import yaml
            try:
                content = yaml.safe_load(node.raw_yaml)
            except yaml.YAMLError:
                pass

        breadcrumbs = [
            {"name": "Design", "url": "/design"},
            {"name": node.name, "url": None},
        ]

        return templates.TemplateResponse(
            "substrate_detail.html",
            {
                "request": request,
                "node": {
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "description": node.description,
                },
                "content": content,
                "breadcrumbs": breadcrumbs,
            },
        )
