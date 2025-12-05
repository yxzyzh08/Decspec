"""
Hierarchy Router - Tree structure view for Product → Domain → Feature → Component.

Component: comp_specview_routes
Feature: feat_specview_hierarchy_view
"""

from typing import List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import select

from devspec.specview.server import get_db, get_templates
from devspec.core.graph_database import NodeModel, EdgeModel


router = APIRouter(tags=["hierarchy"])


class BreadcrumbItem(BaseModel):
    """Breadcrumb navigation item."""

    name: str
    url: Optional[str] = None


@router.get("/", response_class=HTMLResponse)
async def hierarchy_view(request: Request) -> HTMLResponse:
    """
    Render hierarchy view main page with domain list.

    Returns:
        Rendered hierarchy.html template
    """
    templates = get_templates()
    db = get_db()

    domains = []
    with db.get_session() as session:
        # Get all domain nodes
        domain_nodes = session.exec(
            select(NodeModel).where(NodeModel.type == "domain")
        ).all()

        for domain in domain_nodes:
            # Count features for this domain
            feature_count = session.exec(
                select(EdgeModel).where(
                    EdgeModel.source_id == domain.id,
                    EdgeModel.relation == "owns",
                )
            ).all()

            domains.append({
                "id": domain.id,
                "name": domain.name,
                "description": domain.description,
                "feature_count": len(feature_count),
            })

    return templates.TemplateResponse(
        "hierarchy.html",
        {
            "request": request,
            "domains": domains,
            "breadcrumbs": [{"name": "Hierarchy", "url": None}],
        },
    )


@router.get("/domain/{domain_id}/children", response_class=HTMLResponse)
async def get_domain_children(request: Request, domain_id: str) -> HTMLResponse:
    """
    Get features under a domain (htmx lazy-load endpoint).

    Args:
        domain_id: Domain node ID

    Returns:
        Rendered partial template with feature list
    """
    templates = get_templates()
    db = get_db()

    features = []
    with db.get_session() as session:
        # Get all features owned by this domain
        edges = session.exec(
            select(EdgeModel).where(
                EdgeModel.source_id == domain_id,
                EdgeModel.relation == "owns",
            )
        ).all()

        for edge in edges:
            feature = session.get(NodeModel, edge.target_id)
            if feature:
                # Count components for this feature
                comp_edges = session.exec(
                    select(EdgeModel).where(
                        EdgeModel.source_id == feature.id,
                        EdgeModel.relation == "realized_by",
                    )
                ).all()

                features.append({
                    "id": feature.id,
                    "name": feature.name or feature.id,
                    "intent": feature.intent,
                    "component_count": len(comp_edges),
                })

    return templates.TemplateResponse(
        "partials/feature_list.html",
        {
            "request": request,
            "features": features,
        },
    )


@router.get("/feature/{feature_id}/children", response_class=HTMLResponse)
async def get_feature_children(request: Request, feature_id: str) -> HTMLResponse:
    """
    Get components under a feature (htmx lazy-load endpoint).

    Args:
        feature_id: Feature node ID

    Returns:
        Rendered partial template with component list
    """
    templates = get_templates()
    db = get_db()

    components = []
    with db.get_session() as session:
        # Get all components realized by this feature
        edges = session.exec(
            select(EdgeModel).where(
                EdgeModel.source_id == feature_id,
                EdgeModel.relation == "realized_by",
            )
        ).all()

        for edge in edges:
            component = session.get(NodeModel, edge.target_id)
            if component:
                components.append({
                    "id": component.id,
                    "name": component.name or component.id,
                    "desc": component.description,
                    "file_path": component.file_path,
                })

    return templates.TemplateResponse(
        "partials/component_list.html",
        {
            "request": request,
            "components": components,
        },
    )


@router.get("/node/{node_type}/{node_id}", response_class=HTMLResponse)
async def node_detail(request: Request, node_type: str, node_id: str) -> HTMLResponse:
    """
    Render node detail page with breadcrumb navigation.

    Args:
        node_type: Node type (domain, feature, component)
        node_id: Node ID

    Returns:
        Rendered node_detail.html template
    """
    templates = get_templates()
    db = get_db()

    with db.get_session() as session:
        node = session.get(NodeModel, node_id)

        if not node:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": f"Node not found: {node_id}",
                },
                status_code=404,
            )

        # Build breadcrumb
        breadcrumbs = _build_breadcrumb(session, node)

        # Get related nodes
        depends_on = []
        realized_by = []
        depended_by = []

        # Outgoing edges
        out_edges = session.exec(
            select(EdgeModel).where(EdgeModel.source_id == node_id)
        ).all()

        for edge in out_edges:
            target = session.get(NodeModel, edge.target_id)
            if target:
                if edge.relation == "depends_on":
                    depends_on.append({"id": target.id, "name": target.name})
                elif edge.relation == "realized_by":
                    realized_by.append({"id": target.id, "name": target.name})

        # Incoming edges
        in_edges = session.exec(
            select(EdgeModel).where(EdgeModel.target_id == node_id)
        ).all()

        for edge in in_edges:
            source = session.get(NodeModel, edge.source_id)
            if source and edge.relation == "depends_on":
                depended_by.append({"id": source.id, "name": source.name})

        # Parse sections for component
        sections = []
        if node.type == "component":
            sections = [
                {"title": "Summary", "default_state": "expanded", "always_visible": True},
                {"title": "File Path", "default_state": "expanded", "content": node.file_path},
                {"title": "Description", "default_state": "expanded", "content": node.description},
            ]

        return templates.TemplateResponse(
            "node_detail.html",
            {
                "request": request,
                "node": {
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "description": node.description,
                    "intent": node.intent,
                    "file_path": node.file_path,
                    "source_anchor": node.source_anchor,
                },
                "breadcrumbs": breadcrumbs,
                "depends_on": depends_on,
                "realized_by": realized_by,
                "depended_by": depended_by,
                "sections": sections,
            },
        )


def _build_breadcrumb(session, node: NodeModel) -> List[dict]:
    """Build breadcrumb navigation path for a node."""
    breadcrumbs = [{"name": "Hierarchy", "url": "/hierarchy"}]

    if node.type == "domain":
        breadcrumbs.append({"name": node.name, "url": None})

    elif node.type == "feature":
        # Find parent domain
        edge = session.exec(
            select(EdgeModel).where(
                EdgeModel.target_id == node.id,
                EdgeModel.relation == "owns",
            )
        ).first()

        if edge:
            domain = session.get(NodeModel, edge.source_id)
            if domain:
                breadcrumbs.append({
                    "name": domain.name,
                    "url": f"/hierarchy/node/domain/{domain.id}",
                })

        breadcrumbs.append({"name": node.name or node.id, "url": None})

    elif node.type == "component":
        # Find parent feature
        edge = session.exec(
            select(EdgeModel).where(
                EdgeModel.target_id == node.id,
                EdgeModel.relation == "realized_by",
            )
        ).first()

        if edge:
            feature = session.get(NodeModel, edge.source_id)
            if feature:
                # Find domain of feature
                domain_edge = session.exec(
                    select(EdgeModel).where(
                        EdgeModel.target_id == feature.id,
                        EdgeModel.relation == "owns",
                    )
                ).first()

                if domain_edge:
                    domain = session.get(NodeModel, domain_edge.source_id)
                    if domain:
                        breadcrumbs.append({
                            "name": domain.name,
                            "url": f"/hierarchy/node/domain/{domain.id}",
                        })

                breadcrumbs.append({
                    "name": feature.name or feature.id,
                    "url": f"/hierarchy/node/feature/{feature.id}",
                })

        breadcrumbs.append({"name": node.name or node.id, "url": None})

    return breadcrumbs
