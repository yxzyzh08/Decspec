"""
Context Assembler - Assemble minimal sufficient context for AI agents.

This module provides context assembly capabilities based on task phases,
generating Markdown-formatted context for AI consumption.

Component: comp_context_assembler
Feature: feat_context_assembler
"""

from typing import Optional, List
import yaml

from devspec.core.graph_query import GraphQuery, FeatureContext, ComponentContext
from devspec.core.graph_database import NodeModel


# =============================================================================
# Constants
# =============================================================================

PHASES = ["understanding", "locating", "evaluating", "planning", "coding"]


# =============================================================================
# Context Assembler
# =============================================================================

class ContextAssembler:
    """
    Context assembler for AI agents.

    Assembles Markdown-formatted context based on task phase and focus node,
    providing minimal sufficient context to prevent token waste.
    """

    def __init__(self, graph_query: GraphQuery) -> None:
        """
        Initialize the context assembler.

        Args:
            graph_query: GraphQuery instance for database queries
        """
        self.graph_query = graph_query

    def assemble(self, phase: str, focus_node_id: Optional[str] = None) -> str:
        """
        Assemble context based on phase and optional focus node.

        Args:
            phase: Task phase - 'understanding', 'locating', 'evaluating', 'planning', 'coding'
            focus_node_id: Focus node ID (required for evaluating/planning/coding phases)

        Returns:
            Markdown-formatted context string

        Raises:
            ValueError: If phase is unknown or focus_node_id is missing when required
        """
        if phase not in PHASES:
            raise ValueError(f"Unknown phase: {phase}. Valid phases: {PHASES}")

        if phase == "understanding":
            return self._assemble_understanding()
        elif phase == "locating":
            return self._assemble_locating()
        elif phase == "evaluating":
            return self._assemble_evaluating(focus_node_id)
        elif phase == "planning":
            return self._assemble_planning(focus_node_id)
        elif phase == "coding":
            return self._assemble_coding(focus_node_id)

        # Should never reach here due to phase check above
        raise ValueError(f"Unhandled phase: {phase}")

    # -------------------------------------------------------------------------
    # Phase 1: Understanding
    # -------------------------------------------------------------------------

    def _assemble_understanding(self) -> str:
        """
        Assemble Phase 1 context: Product Vision and Description.

        Returns:
            Markdown with product information
        """
        products = self.graph_query.get_nodes_by_type("product")
        if not products:
            return "# Product Context\n\n*No product information available.*\n"

        product = products[0]

        # Parse raw_yaml to get additional fields
        vision = ""
        description = product.description or ""

        if product.raw_yaml:
            try:
                data = yaml.safe_load(product.raw_yaml)
                if isinstance(data, dict):
                    vision = data.get("vision", "")
                    if not description:
                        description = data.get("description", "")
            except yaml.YAMLError:
                pass

        lines = [
            "# Product Context",
            "",
            f"**Name**: {product.name or 'N/A'}",
            "",
        ]

        if vision:
            lines.extend([
                "**Vision**:",
                f"> {vision}",
                "",
            ])

        if description:
            lines.extend([
                "**Description**:",
                description,
                "",
            ])

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Phase 2: Locating
    # -------------------------------------------------------------------------

    def _assemble_locating(self) -> str:
        """
        Assemble Phase 2 context: Domain list with their Features.

        Returns:
            Markdown with domain overview and feature lists
        """
        domains = self.graph_query.get_all_domains()

        if not domains:
            return "# Domain Overview\n\n*No domains defined.*\n"

        lines = ["# Domain Overview", ""]

        for domain in sorted(domains, key=lambda d: d.id):
            lines.append(f"## {domain.name or domain.id} (`{domain.id}`)")
            lines.append("")

            if domain.description:
                lines.append(f"{domain.description}")
                lines.append("")

            # Get features for this domain
            features = self.graph_query.get_features_by_domain(domain.id)

            if features:
                lines.append("**Features**:")
                lines.append("")
                for feat in sorted(features, key=lambda f: f.id):
                    intent = self._get_intent(feat)
                    lines.append(f"- `{feat.id}`: {intent}")
                lines.append("")
            else:
                lines.append("*No features defined.*")
                lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Phase 3: Evaluating
    # -------------------------------------------------------------------------

    def _assemble_evaluating(self, focus_node_id: Optional[str]) -> str:
        """
        Assemble Phase 3 context: Feature details with Components for exhaustiveness check.

        Args:
            focus_node_id: Feature ID to focus on

        Returns:
            Markdown with feature context and component list

        Raises:
            ValueError: If focus_node_id is missing or invalid
        """
        if not focus_node_id:
            raise ValueError("focus_node_id is required for phase 'evaluating'")

        # Validate node type
        node = self.graph_query.db.get_node(focus_node_id)
        if not node:
            raise ValueError(f"Node not found: {focus_node_id}")

        if node.type != "feature":
            raise ValueError(f"Expected feature node, got {node.type}")

        # Get feature context
        context = self.graph_query.get_feature_context(focus_node_id)
        if not context:
            raise ValueError(f"Failed to get context for feature: {focus_node_id}")

        return self._format_feature_context(context)

    def _format_feature_context(self, context: FeatureContext) -> str:
        """Format FeatureContext as Markdown."""
        feat = context.feature
        lines = [
            f"# Feature Context: {feat.name or feat.id}",
            "",
            f"**ID**: `{feat.id}`",
            "",
        ]

        # Intent
        intent = self._get_intent(feat)
        if intent:
            lines.extend([
                "**Intent**:",
                f"> {intent}",
                "",
            ])

        # Domain
        if context.domain:
            lines.append(f"**Domain**: `{context.domain.id}` ({context.domain.name or 'N/A'})")
            lines.append("")

        # User Stories (from raw_yaml)
        user_stories = self._get_user_stories(feat)
        if user_stories:
            lines.append("**User Stories**:")
            lines.append("")
            for story in user_stories:
                lines.append(f"- {story}")
            lines.append("")

        # Dependencies
        if context.dependencies:
            lines.append("**Dependencies**:")
            lines.append("")
            for dep in context.dependencies:
                lines.append(f"- `{dep.id}`: {dep.name or 'N/A'}")
            lines.append("")

        # Components (for exhaustiveness check)
        lines.append("## Existing Components (for Exhaustiveness Check)")
        lines.append("")

        if context.components:
            for comp in sorted(context.components, key=lambda c: c.id):
                lines.append(f"### `{comp.id}`")
                lines.append("")
                lines.append(f"**Description**: {comp.description or 'N/A'}")
                lines.append("")

                # Get component design
                comp_context = self.graph_query.get_component_context(comp.id)
                if comp_context and comp_context.design:
                    api = comp_context.design.get("api", [])
                    if api:
                        lines.append("**API**:")
                        lines.append("")
                        for item in api:
                            if isinstance(item, dict):
                                sig = item.get("signature", "")
                                desc = item.get("desc", "")
                                lines.append(f"- `{sig}`: {desc}")
                        lines.append("")
        else:
            lines.append("*No components assigned yet.*")
            lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Phase 4: Planning
    # -------------------------------------------------------------------------

    def _assemble_planning(self, focus_node_id: Optional[str]) -> str:
        """
        Assemble Phase 4 context: Dependency graph for execution planning.

        Args:
            focus_node_id: Node ID to focus on (Feature or Component)

        Returns:
            Markdown with dependency graph

        Raises:
            ValueError: If focus_node_id is missing or invalid
        """
        if not focus_node_id:
            raise ValueError("focus_node_id is required for phase 'planning'")

        # Get node with relations
        node_graph = self.graph_query.get_node_with_relations(focus_node_id, depth=2)
        if not node_graph:
            raise ValueError(f"Node not found: {focus_node_id}")

        return self._format_dependency_graph(node_graph)

    def _format_dependency_graph(self, node_graph) -> str:
        """Format NodeGraph as Markdown dependency graph."""
        root = node_graph.root
        lines = [
            "# Dependency Graph",
            "",
            f"**Root**: `{root.id}` ({root.type})",
            "",
        ]

        if root.name:
            lines.append(f"**Name**: {root.name}")
            lines.append("")

        # Categorize edges by relation type
        depends_on: List[str] = []
        realized_by: List[str] = []
        owns: List[str] = []
        other_relations: dict = {}

        for edge in node_graph.edges:
            if edge.source_id == root.id:
                # Outgoing edge
                target_node = node_graph.nodes.get(edge.target_id)
                target_name = target_node.name if target_node else edge.target_id

                if edge.relation == "depends_on":
                    depends_on.append(f"`{edge.target_id}` ({target_name})")
                elif edge.relation == "realized_by":
                    realized_by.append(f"`{edge.target_id}` ({target_name})")
                elif edge.relation == "owns":
                    owns.append(f"`{edge.target_id}` ({target_name})")
                else:
                    if edge.relation not in other_relations:
                        other_relations[edge.relation] = []
                    other_relations[edge.relation].append(f"`{edge.target_id}` ({target_name})")

        # Format sections
        if depends_on:
            lines.append("## Depends On")
            lines.append("")
            for item in depends_on:
                lines.append(f"- {item}")
            lines.append("")

        if realized_by:
            lines.append("## Realized By (Components)")
            lines.append("")
            for item in realized_by:
                lines.append(f"- {item}")
            lines.append("")

        if owns:
            lines.append("## Owns")
            lines.append("")
            for item in owns:
                lines.append(f"- {item}")
            lines.append("")

        for relation, items in other_relations.items():
            lines.append(f"## {relation.replace('_', ' ').title()}")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

        # Show incoming edges (what depends on this node)
        depended_by: List[str] = []
        for edge in node_graph.edges:
            if edge.target_id == root.id and edge.relation == "depends_on":
                source_node = node_graph.nodes.get(edge.source_id)
                source_name = source_node.name if source_node else edge.source_id
                depended_by.append(f"`{edge.source_id}` ({source_name})")

        if depended_by:
            lines.append("## Depended By")
            lines.append("")
            for item in depended_by:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Phase 5: Coding
    # -------------------------------------------------------------------------

    def _assemble_coding(self, focus_node_id: Optional[str]) -> str:
        """
        Assemble Coding context: Component design and Substrate constraints.

        Args:
            focus_node_id: Component ID to focus on

        Returns:
            Markdown with component design and constraints

        Raises:
            ValueError: If focus_node_id is missing or invalid
        """
        if not focus_node_id:
            raise ValueError("focus_node_id is required for phase 'coding'")

        # Validate node type
        node = self.graph_query.db.get_node(focus_node_id)
        if not node:
            raise ValueError(f"Node not found: {focus_node_id}")

        if node.type != "component":
            raise ValueError(f"Expected component node, got {node.type}")

        # Get component context
        context = self.graph_query.get_component_context(focus_node_id)
        if not context:
            raise ValueError(f"Failed to get context for component: {focus_node_id}")

        # Get substrates
        substrates = self.graph_query.get_nodes_by_type("substrate")

        return self._format_coding_context(context, substrates)

    def _format_coding_context(
        self, context: ComponentContext, substrates: List[NodeModel]
    ) -> str:
        """Format ComponentContext and Substrates as Markdown."""
        comp = context.component
        lines = [
            "# Coding Context",
            "",
            f"**Component**: `{comp.id}`",
            "",
        ]

        if comp.description:
            lines.append(f"**Description**: {comp.description}")
            lines.append("")

        if comp.file_path:
            lines.append(f"**File Path**: `{comp.file_path}`")
            lines.append("")

        # Parent feature and domain
        if context.feature:
            lines.append(f"**Feature**: `{context.feature.id}` ({context.feature.name or 'N/A'})")
            lines.append("")

        if context.domain:
            lines.append(f"**Domain**: `{context.domain.id}` ({context.domain.name or 'N/A'})")
            lines.append("")

        # Dependencies
        if context.dependencies:
            lines.append("**Dependencies**:")
            lines.append("")
            for dep in context.dependencies:
                lines.append(f"- `{dep.id}`: {dep.description or 'N/A'}")
            lines.append("")

        # Component Design (from raw_yaml)
        lines.append("## Component Design")
        lines.append("")

        if comp.raw_yaml:
            lines.append("```yaml")
            lines.append(comp.raw_yaml.strip())
            lines.append("```")
            lines.append("")
        else:
            lines.append("*No design specification available.*")
            lines.append("")

        # Substrate Constraints
        lines.append("## Constraints (Substrates)")
        lines.append("")

        if substrates:
            for sub in sorted(substrates, key=lambda s: s.id):
                lines.append(f"### `{sub.id}`: {sub.name or 'N/A'}")
                lines.append("")

                if sub.description:
                    lines.append(sub.description)
                    lines.append("")

                # Extract key content from raw_yaml
                if sub.raw_yaml:
                    try:
                        data = yaml.safe_load(sub.raw_yaml)
                        if isinstance(data, dict):
                            # Show relevant fields
                            for key in ["principles", "rules", "stack", "conventions"]:
                                if key in data:
                                    lines.append(f"**{key.title()}**:")
                                    lines.append("")
                                    value = data[key]
                                    if isinstance(value, list):
                                        for item in value:
                                            if isinstance(item, dict):
                                                name = item.get("name", item.get("id", str(item)))
                                                lines.append(f"- {name}")
                                            else:
                                                lines.append(f"- {item}")
                                    else:
                                        lines.append(str(value))
                                    lines.append("")
                    except yaml.YAMLError:
                        pass
        else:
            lines.append("*No substrate constraints defined.*")
            lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_intent(self, node: NodeModel) -> str:
        """Extract intent from node's raw_yaml."""
        if node.intent:
            return node.intent

        if node.raw_yaml:
            try:
                data = yaml.safe_load(node.raw_yaml)
                if isinstance(data, dict):
                    return data.get("intent", "")
            except yaml.YAMLError:
                pass

        return ""

    def _get_user_stories(self, node: NodeModel) -> List[str]:
        """Extract user_stories from node's raw_yaml."""
        if node.raw_yaml:
            try:
                data = yaml.safe_load(node.raw_yaml)
                if isinstance(data, dict):
                    stories = data.get("user_stories", [])
                    if isinstance(stories, list):
                        return stories
            except yaml.YAMLError:
                pass
        return []
