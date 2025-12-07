"""
Graph Query - Query interface for SpecGraph database.

This module provides query capabilities for the SpecGraph knowledge graph,
including node queries, relationship traversal, and path search.

Component: comp_graph_query
Feature: feat_specgraph_database
"""

from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

import yaml
from sqlmodel import select

from devspec.core.graph_database import (
    GraphDatabase,
    NodeModel,
    EdgeModel,
    DomainAPIModel,
)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class NodeGraph:
    """A node with its related nodes and edges."""

    root: NodeModel
    nodes: Dict[str, NodeModel] = field(default_factory=dict)
    edges: List[EdgeModel] = field(default_factory=list)


@dataclass
class FeatureContext:
    """Complete context for a feature."""

    feature: NodeModel
    domain: Optional[NodeModel] = None
    components: List[NodeModel] = field(default_factory=list)
    dependencies: List[NodeModel] = field(default_factory=list)
    consumed_apis: List[DomainAPIModel] = field(default_factory=list)


@dataclass
class ComponentContext:
    """Complete context for a component."""

    component: NodeModel
    feature: Optional[NodeModel] = None
    domain: Optional[NodeModel] = None
    dependencies: List[NodeModel] = field(default_factory=list)
    design: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Graph Query Engine
# =============================================================================

class GraphQuery:
    """Query interface for SpecGraph database."""

    def __init__(self, db: GraphDatabase) -> None:
        """
        Initialize query engine with database.

        Args:
            db: GraphDatabase instance
        """
        self.db = db

    def get_nodes_by_type(self, node_type: str) -> List[NodeModel]:
        """
        Get all nodes of a specific type.

        Args:
            node_type: Node type (product, domain, feature, component, design, substrate)

        Returns:
            List of matching nodes
        """
        with self.db.get_session() as session:
            statement = select(NodeModel).where(NodeModel.type == node_type)
            return list(session.exec(statement).all())

    def get_node_with_relations(self, node_id: str, depth: int = 1) -> Optional[NodeGraph]:
        """
        Get a node with its related nodes up to specified depth.

        Args:
            node_id: Node ID to start from
            depth: How many levels of relationships to include (default 1)

        Returns:
            NodeGraph with root node and related nodes/edges, or None if not found
        """
        root = self.db.get_node(node_id)
        if not root:
            return None

        graph = NodeGraph(root=root)
        graph.nodes[node_id] = root

        # BFS traversal
        visited = {node_id}
        visited_edges: set[tuple[str, str, str]] = set()  # (source, target, relation)
        queue = deque([(node_id, 0)])

        with self.db.get_session() as session:
            while queue:
                current_id, current_depth = queue.popleft()
                if current_depth >= depth:
                    continue

                # Get outgoing edges
                out_edges = session.exec(
                    select(EdgeModel).where(EdgeModel.source_id == current_id)
                ).all()

                for edge in out_edges:
                    edge_key = (edge.source_id, edge.target_id, edge.relation)
                    if edge_key not in visited_edges:
                        visited_edges.add(edge_key)
                        graph.edges.append(edge)
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        target_node = session.get(NodeModel, edge.target_id)
                        if target_node:
                            graph.nodes[edge.target_id] = target_node
                            queue.append((edge.target_id, current_depth + 1))

                # Get incoming edges
                in_edges = session.exec(
                    select(EdgeModel).where(EdgeModel.target_id == current_id)
                ).all()

                for edge in in_edges:
                    edge_key = (edge.source_id, edge.target_id, edge.relation)
                    if edge_key not in visited_edges:
                        visited_edges.add(edge_key)
                        graph.edges.append(edge)
                    if edge.source_id not in visited:
                        visited.add(edge.source_id)
                        source_node = session.get(NodeModel, edge.source_id)
                        if source_node:
                            graph.nodes[edge.source_id] = source_node
                            queue.append((edge.source_id, current_depth + 1))

        return graph

    def get_children(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[NodeModel]:
        """
        Get all child nodes (outgoing edges) of a node.

        Args:
            node_id: Parent node ID
            relation: Filter by relation type (optional)

        Returns:
            List of child nodes
        """
        with self.db.get_session() as session:
            statement = select(EdgeModel).where(EdgeModel.source_id == node_id)
            if relation:
                statement = statement.where(EdgeModel.relation == relation)

            edges = session.exec(statement).all()
            children = []
            for edge in edges:
                node = session.get(NodeModel, edge.target_id)
                if node:
                    children.append(node)
            return children

    def get_parents(
        self, node_id: str, relation: Optional[str] = None
    ) -> List[NodeModel]:
        """
        Get all parent nodes (incoming edges) of a node.

        Args:
            node_id: Child node ID
            relation: Filter by relation type (optional)

        Returns:
            List of parent nodes
        """
        with self.db.get_session() as session:
            statement = select(EdgeModel).where(EdgeModel.target_id == node_id)
            if relation:
                statement = statement.where(EdgeModel.relation == relation)

            edges = session.exec(statement).all()
            parents = []
            for edge in edges:
                node = session.get(NodeModel, edge.source_id)
                if node:
                    parents.append(node)
            return parents

    def get_feature_context(self, feature_id: str) -> Optional[FeatureContext]:
        """
        Get full context for a feature (domain, components, dependencies).

        Args:
            feature_id: Feature node ID

        Returns:
            FeatureContext or None if feature not found
        """
        feature = self.db.get_node(feature_id)
        if not feature:
            return None

        context = FeatureContext(feature=feature)

        # Get parent domain (owns relationship)
        domains = self.get_parents(feature_id, "owns")
        if domains:
            context.domain = domains[0]

        # Get implementing components (realized_by)
        context.components = self.get_children(feature_id, "realized_by")

        # Get dependent features (depends_on)
        context.dependencies = self.get_children(feature_id, "depends_on")

        # Get consumed APIs (consumes)
        # Note: This would require a consumes relationship to be set up
        # For now, leave as empty list

        return context

    def get_component_context(self, component_id: str) -> Optional[ComponentContext]:
        """
        Get full context for a component (feature, dependencies, file path).

        Args:
            component_id: Component node ID

        Returns:
            ComponentContext or None if component not found
        """
        component = self.db.get_node(component_id)
        if not component:
            return None

        context = ComponentContext(component=component)

        # Get parent feature (realized_by relationship - we're the target)
        features = self.get_parents(component_id, "realized_by")
        if features:
            context.feature = features[0]

            # Get parent domain through feature
            domains = self.get_parents(context.feature.id, "owns")
            if domains:
                context.domain = domains[0]

        # Get dependent components
        context.dependencies = self.get_children(component_id, "depends_on")

        # Parse design from raw_yaml
        if component.raw_yaml:
            try:
                data = yaml.safe_load(component.raw_yaml)
                if isinstance(data, dict) and "design" in data:
                    context.design = data["design"]
            except yaml.YAMLError:
                pass

        return context

    def get_domain_apis(self, domain_id: str) -> List[DomainAPIModel]:
        """
        Get all APIs exported by a domain.

        Args:
            domain_id: Domain node ID

        Returns:
            List of DomainAPIModel
        """
        return self.db.get_domain_apis(domain_id)

    def find_path(
        self, from_id: str, to_id: str
    ) -> Optional[List[EdgeModel]]:
        """
        Find shortest path between two nodes.

        Args:
            from_id: Start node ID
            to_id: End node ID

        Returns:
            List of edges forming the path, or None if no path exists
        """
        if from_id == to_id:
            return []

        # BFS to find shortest path
        visited = {from_id}
        queue = deque([(from_id, [])])  # (node_id, path_edges)

        with self.db.get_session() as session:
            while queue:
                current_id, path = queue.popleft()

                # Get all edges from current node (both directions)
                out_edges = session.exec(
                    select(EdgeModel).where(EdgeModel.source_id == current_id)
                ).all()

                in_edges = session.exec(
                    select(EdgeModel).where(EdgeModel.target_id == current_id)
                ).all()

                all_edges = list(out_edges) + list(in_edges)

                for edge in all_edges:
                    # Determine next node
                    if edge.source_id == current_id:
                        next_id = edge.target_id
                    else:
                        next_id = edge.source_id

                    if next_id == to_id:
                        return path + [edge]

                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, path + [edge]))

        return None

    def search_nodes(
        self, query: str, node_types: Optional[List[str]] = None
    ) -> List[NodeModel]:
        """
        Full-text search across node names and descriptions.

        Args:
            query: Search query string
            node_types: Filter by node types (optional)

        Returns:
            List of matching nodes
        """
        with self.db.get_session() as session:
            # Build search pattern
            pattern = f"%{query}%"

            statement = select(NodeModel).where(
                (NodeModel.name.like(pattern)) | (NodeModel.description.like(pattern))
            )

            if node_types:
                statement = statement.where(NodeModel.type.in_(node_types))

            return list(session.exec(statement).all())

    def get_features_by_domain(self, domain_id: str) -> List[NodeModel]:
        """
        Get all features belonging to a domain.

        Args:
            domain_id: Domain node ID

        Returns:
            List of feature nodes
        """
        return self.get_children(domain_id, "owns")

    def get_all_domains(self) -> List[NodeModel]:
        """
        Get all domain nodes.

        Returns:
            List of domain nodes
        """
        return self.get_nodes_by_type("domain")

    def get_all_features(self) -> List[NodeModel]:
        """
        Get all feature nodes.

        Returns:
            List of feature nodes
        """
        return self.get_nodes_by_type("feature")

    def get_all_components(self) -> List[NodeModel]:
        """
        Get all component nodes.

        Returns:
            List of component nodes
        """
        return self.get_nodes_by_type("component")
