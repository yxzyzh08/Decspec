"""
Relation Router - Dependency relationship view with Mermaid graph.

Component: comp_specview_routes
Feature: feat_specview_relation_view
"""

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from devspec.specview.server import get_db, get_templates
from devspec.core.graph_database import NodeModel, EdgeModel


router = APIRouter(tags=["relation"])


# Relation type descriptions for tooltips
RELATION_DESCRIPTIONS = {
    "depends_on": "当前节点依赖的其他节点 (上游依赖)",
    "realized_by": "实现当前 Feature 的 Component 列表",
    "owns": "Domain 拥有的 Feature 列表",
    "contains": "Product 包含的 Domain 列表",
}


@router.get("/", response_class=HTMLResponse)
async def relation_index(request: Request) -> HTMLResponse:
    """
    Render relation view index - list of nodes to explore.

    Returns:
        Rendered relation_index.html template
    """
    templates = get_templates()
    db = get_db()

    nodes = []
    with db.get_session() as session:
        all_nodes = session.exec(
            select(NodeModel).where(NodeModel.type.in_(["feature", "component"]))
        ).all()

        for node in all_nodes:
            # Count relations
            out_count = len(session.exec(
                select(EdgeModel).where(EdgeModel.source_id == node.id)
            ).all())
            in_count = len(session.exec(
                select(EdgeModel).where(EdgeModel.target_id == node.id)
            ).all())

            nodes.append({
                "id": node.id,
                "name": node.name or node.id,
                "type": node.type,
                "relation_count": out_count + in_count,
            })

    # Sort by relation count (most connected first)
    nodes.sort(key=lambda x: x["relation_count"], reverse=True)

    return templates.TemplateResponse(
        "relation_index.html",
        {
            "request": request,
            "nodes": nodes,
            "breadcrumbs": [{"name": "Relations", "url": None}],
        },
    )


@router.get("/node/{node_id}", response_class=HTMLResponse)
async def relation_view(request: Request, node_id: str) -> HTMLResponse:
    """
    Render node relationship page with dependency lists and Mermaid graph.

    Args:
        node_id: Node ID to show relations for

    Returns:
        Rendered relation.html template
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

        # Collect relations
        relations = {
            "depends_on": [],  # Nodes this node depends on
            "depended_by": [],  # Nodes that depend on this node
            "realized_by": [],  # Components that realize this feature
            "realizes": [],  # Features this component realizes
        }

        # Outgoing edges
        out_edges = session.exec(
            select(EdgeModel).where(EdgeModel.source_id == node_id)
        ).all()

        for edge in out_edges:
            target = session.get(NodeModel, edge.target_id)
            if target:
                if edge.relation == "depends_on":
                    relations["depends_on"].append({
                        "id": target.id,
                        "name": target.name or target.id,
                        "type": target.type,
                    })
                elif edge.relation == "realized_by":
                    relations["realized_by"].append({
                        "id": target.id,
                        "name": target.name or target.id,
                        "type": target.type,
                    })

        # Incoming edges
        in_edges = session.exec(
            select(EdgeModel).where(EdgeModel.target_id == node_id)
        ).all()

        for edge in in_edges:
            source = session.get(NodeModel, edge.source_id)
            if source:
                if edge.relation == "depends_on":
                    relations["depended_by"].append({
                        "id": source.id,
                        "name": source.name or source.id,
                        "type": source.type,
                    })
                elif edge.relation == "realized_by":
                    relations["realizes"].append({
                        "id": source.id,
                        "name": source.name or source.id,
                        "type": source.type,
                    })

        # Generate Mermaid graph
        mermaid_code = _generate_mermaid_graph(session, node_id, depth=2)

        breadcrumbs = [
            {"name": "Relations", "url": "/relation"},
            {"name": node.name or node.id, "url": None},
        ]

        return templates.TemplateResponse(
            "relation.html",
            {
                "request": request,
                "node": {
                    "id": node.id,
                    "name": node.name or node.id,
                    "type": node.type,
                },
                "relations": relations,
                "relation_descriptions": RELATION_DESCRIPTIONS,
                "mermaid_code": mermaid_code,
                "breadcrumbs": breadcrumbs,
            },
        )


@router.get("/graph/{node_id}", response_class=HTMLResponse)
async def get_relation_graph(
    request: Request,
    node_id: str,
    depth: int = 2,
) -> HTMLResponse:
    """
    Get Mermaid dependency graph (htmx endpoint).

    Args:
        node_id: Center node ID
        depth: Traversal depth (default 2)

    Returns:
        Rendered partial with Mermaid graph code
    """
    templates = get_templates()
    db = get_db()

    with db.get_session() as session:
        mermaid_code = _generate_mermaid_graph(session, node_id, depth)

    return templates.TemplateResponse(
        "partials/relation_graph.html",
        {
            "request": request,
            "mermaid_code": mermaid_code,
        },
    )


def _generate_mermaid_graph(session, center_node_id: str, depth: int = 2) -> str:
    """
    Generate Mermaid graph definition for a node's relationships.

    Args:
        session: Database session
        center_node_id: Center node ID
        depth: Traversal depth

    Returns:
        Mermaid graph definition string
    """
    # BFS to collect nodes and edges
    visited = set()
    nodes = []
    edges = []
    queue = [(center_node_id, 0)]

    while queue:
        current_id, current_depth = queue.pop(0)

        if current_id in visited or current_depth > depth:
            continue

        visited.add(current_id)
        node = session.get(NodeModel, current_id)

        if not node:
            continue

        nodes.append({
            "id": current_id,
            "label": node.name or current_id,
            "type": node.type,
        })

        # Get outgoing edges
        out_edges = session.exec(
            select(EdgeModel).where(EdgeModel.source_id == current_id)
        ).all()

        for edge in out_edges:
            if edge.relation in ("depends_on", "realized_by"):
                edges.append({
                    "source": current_id,
                    "target": edge.target_id,
                    "relation": edge.relation,
                })
                queue.append((edge.target_id, current_depth + 1))

        # Get incoming edges (for depended_by)
        in_edges = session.exec(
            select(EdgeModel).where(EdgeModel.target_id == current_id)
        ).all()

        for edge in in_edges:
            if edge.relation == "depends_on":
                edges.append({
                    "source": edge.source_id,
                    "target": current_id,
                    "relation": edge.relation,
                })
                queue.append((edge.source_id, current_depth + 1))

    # Generate Mermaid code
    lines = ["graph LR"]

    # Node styles
    node_styles = {
        "feature": "#3B82F6",  # blue
        "component": "#10B981",  # green
        "domain": "#8B5CF6",  # purple
        "design": "#F59E0B",  # amber
    }

    # Add nodes
    for node in nodes:
        safe_id = node["id"].replace("-", "_")
        lines.append(f'  {safe_id}["{node["label"]}"]')

        color = node_styles.get(node["type"], "#6B7280")
        lines.append(f"  style {safe_id} fill:{color},color:#fff")

    # Add edges
    edge_arrows = {
        "depends_on": "-->",
        "realized_by": "-.->",
    }

    seen_edges = set()
    for edge in edges:
        edge_key = (edge["source"], edge["target"], edge["relation"])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            source = edge["source"].replace("-", "_")
            target = edge["target"].replace("-", "_")
            arrow = edge_arrows.get(edge["relation"], "-->")
            lines.append(f"  {source} {arrow} {target}")

    return "\n".join(lines)
