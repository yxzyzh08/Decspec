"""
Graph Renderer - Mermaid graph generation with SVG caching.

This module provides the GraphRenderer class for generating Mermaid
dependency graphs and rendering them to SVG (with caching support).

Component: comp_specview_graph_renderer
Feature: feat_specview_relation_view
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlmodel import select

from devspec.core.graph_database import GraphDatabase, NodeModel, EdgeModel


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class GraphNode:
    """Graph node data."""

    id: str
    label: str
    type: str  # feature, component, domain, design


@dataclass
class GraphEdge:
    """Graph edge data."""

    source: str
    target: str
    relation: str  # depends_on, realized_by


@dataclass
class RelationGraph:
    """Relation graph data structure."""

    center_node: str
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)


# =============================================================================
# Constants
# =============================================================================

NODE_STYLES = {
    "feature": {"fill": "#3B82F6", "stroke": "#1D4ED8"},  # blue-500
    "component": {"fill": "#10B981", "stroke": "#047857"},  # green-500
    "domain": {"fill": "#8B5CF6", "stroke": "#6D28D9"},  # purple-500
    "design": {"fill": "#F59E0B", "stroke": "#D97706"},  # amber-500
    "substrate": {"fill": "#6B7280", "stroke": "#4B5563"},  # gray-500
}

EDGE_ARROWS = {
    "depends_on": "-->",  # solid arrow
    "realized_by": "-.->",  # dashed arrow
}


# =============================================================================
# GraphRenderer Class
# =============================================================================

class GraphRenderer:
    """
    Mermaid graph renderer with SVG caching.

    Generates Mermaid graph definitions from SpecGraph relationships
    and renders them to SVG with caching support.
    """

    def __init__(self, db: GraphDatabase) -> None:
        """
        Initialize renderer with database dependency.

        Args:
            db: SpecGraph database instance
        """
        self.db = db
        self._svg_cache: Dict[str, str] = {}

    def get_node_relations(self, node_id: str, depth: int = 2) -> RelationGraph:
        """
        Get relationship data for a node using BFS traversal.

        Args:
            node_id: Node ID (feat_xxx, comp_xxx)
            depth: Traversal depth (default 2 levels)

        Returns:
            RelationGraph with nodes and edges
        """
        visited: set = set()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # BFS queue: (node_id, current_depth)
        queue = [(node_id, 0)]

        with self.db.get_session() as session:
            while queue:
                current_id, current_depth = queue.pop(0)

                if current_id in visited or current_depth > depth:
                    continue

                visited.add(current_id)
                node = session.get(NodeModel, current_id)

                if not node:
                    continue

                # Add node
                nodes.append(GraphNode(
                    id=node.id,
                    label=node.name or node.id,
                    type=node.type,
                ))

                # Get outgoing edges
                out_edges = session.exec(
                    select(EdgeModel).where(EdgeModel.source_id == current_id)
                ).all()

                for edge in out_edges:
                    if edge.relation in ("depends_on", "realized_by"):
                        edges.append(GraphEdge(
                            source=current_id,
                            target=edge.target_id,
                            relation=edge.relation,
                        ))
                        queue.append((edge.target_id, current_depth + 1))

                # Get incoming edges (for reverse relations)
                in_edges = session.exec(
                    select(EdgeModel).where(EdgeModel.target_id == current_id)
                ).all()

                for edge in in_edges:
                    if edge.relation == "depends_on":
                        # Add reverse edge (depended_by)
                        edges.append(GraphEdge(
                            source=edge.source_id,
                            target=current_id,
                            relation="depends_on",
                        ))
                        queue.append((edge.source_id, current_depth + 1))

        return RelationGraph(
            center_node=node_id,
            nodes=nodes,
            edges=edges,
        )

    def generate_mermaid(self, node_id: str, depth: int = 2) -> str:
        """
        Generate Mermaid graph definition string.

        Args:
            node_id: Center node ID
            depth: Traversal depth

        Returns:
            Mermaid graph definition (graph LR ...)
        """
        graph = self.get_node_relations(node_id, depth)

        lines = ["graph LR"]

        # Add node definitions
        for node in graph.nodes:
            # Sanitize ID for Mermaid (replace hyphens)
            safe_id = node.id.replace("-", "_")
            lines.append(f'  {safe_id}["{node.label}"]')

            # Add style
            style = NODE_STYLES.get(node.type, NODE_STYLES["design"])
            lines.append(f"  style {safe_id} fill:{style['fill']},color:#fff")

        # Add edge definitions (deduplicate)
        seen_edges: set = set()
        for edge in graph.edges:
            edge_key = (edge.source, edge.target, edge.relation)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)

                source = edge.source.replace("-", "_")
                target = edge.target.replace("-", "_")
                arrow = EDGE_ARROWS.get(edge.relation, "-->")

                lines.append(f"  {source} {arrow} {target}")

        return "\n".join(lines)

    def render_svg(self, mermaid_code: str) -> str:
        """
        Render Mermaid code to SVG string.

        Note: This is a placeholder that returns a Mermaid code block
        for client-side rendering via mermaid.js CDN.
        For true server-side rendering, integrate mermaid-py or mermaid-cli.

        Args:
            mermaid_code: Mermaid graph definition

        Returns:
            SVG string or Mermaid code block for client-side rendering
        """
        # For now, return a div that mermaid.js will render client-side
        # This avoids the complexity of server-side Mermaid rendering
        return f'''<div class="mermaid">
{mermaid_code}
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true}});</script>'''

    def get_cached_svg(self, node_id: str, depth: int = 2) -> Optional[str]:
        """
        Get cached SVG for a node.

        Args:
            node_id: Node ID
            depth: Traversal depth

        Returns:
            Cached SVG string or None if not cached
        """
        cache_key = f"{node_id}:{depth}"
        return self._svg_cache.get(cache_key)

    def render_and_cache(self, node_id: str, depth: int = 2) -> str:
        """
        Generate Mermaid, render to SVG, and cache.

        Args:
            node_id: Node ID
            depth: Traversal depth

        Returns:
            SVG string (from cache or freshly rendered)
        """
        # Check cache first
        cached = self.get_cached_svg(node_id, depth)
        if cached:
            return cached

        # Generate and render
        mermaid_code = self.generate_mermaid(node_id, depth)
        svg = self.render_svg(mermaid_code)

        # Cache result
        cache_key = f"{node_id}:{depth}"
        self._svg_cache[cache_key] = svg

        return svg

    def invalidate_cache(self, node_id: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            node_id: Specific node to invalidate, or None to clear all
        """
        if node_id is None:
            self._svg_cache.clear()
        else:
            # Remove all cache entries for this node (any depth)
            keys_to_delete = [
                k for k in self._svg_cache
                if k.startswith(f"{node_id}:")
            ]
            for key in keys_to_delete:
                del self._svg_cache[key]
