"""
Graph Sync - YAML to database full synchronization engine.

This module provides full synchronization between YAML spec files and the SQLite database.

Component: comp_graph_sync
Feature: feat_specgraph_database
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml

from devspec.core.graph_database import (
    GraphDatabase,
    NodeModel,
    EdgeModel,
    DomainAPIModel,
)


# =============================================================================
# Constants
# =============================================================================

SKIP_DIRS = [".runtime", "__pycache__"]

VALID_NODE_TYPES = [
    "product",
    "domain",
    "feature",
    "component",
    "design",
    "substrate",
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class SyncResult:
    """Result of sync operation."""

    added: int = 0
    updated: int = 0
    deleted: int = 0
    edges_created: int = 0
    errors: List[str] = field(default_factory=list)


# =============================================================================
# Graph Sync Engine
# =============================================================================

class GraphSync:
    """Synchronization engine for YAML to database sync."""

    def __init__(self, db: GraphDatabase, root_path: Path) -> None:
        """
        Initialize sync engine with database and project root.

        Args:
            db: GraphDatabase instance
            root_path: Project root path
        """
        self.db = db
        self.root_path = Path(root_path)
        self.spec_dir = self.root_path / ".specgraph"

    def sync_all(self) -> SyncResult:
        """
        Full sync of all YAML files to database.

        This performs a complete synchronization by clearing all existing data
        and rebuilding from YAML files.

        Returns:
            SyncResult with sync statistics
        """
        result = SyncResult()
        nodes_dict: Dict[str, Dict[str, Any]] = {}

        if not self.spec_dir.exists():
            result.errors.append(f"Spec directory not found: {self.spec_dir}")
            return result

        # 1. Clear all existing data (full sync)
        self.db.clear_all()

        # 2. Get all YAML files
        yaml_files = self._get_yaml_files()

        # 3. Sync each file
        for file_path in yaml_files:
            node_data, error = self._sync_yaml_file(file_path)
            if error:
                result.errors.append(error)
            elif node_data:
                nodes_dict[node_data["id"]] = node_data
                result.added += 1

        # 4. Extract virtual Domain nodes from product.yaml
        product_path = self.spec_dir / "product.yaml"
        if product_path.exists():
            domain_nodes = self._extract_domain_nodes(product_path)
            for domain_data in domain_nodes:
                nodes_dict[domain_data["id"]] = domain_data
                # Upsert domain node
                node = self._dict_to_node(domain_data, str(product_path.relative_to(self.root_path)))
                if node:
                    self.db.upsert_node(node)

        # 5. Build and sync edges
        edges_created = self._build_and_sync_edges(nodes_dict)
        result.edges_created = edges_created

        return result

    def sync_file(self, file_path: Path) -> SyncResult:
        """
        Sync a single YAML file to database.

        Args:
            file_path: Path to YAML file

        Returns:
            SyncResult for this file
        """
        result = SyncResult()
        node_data, error = self._sync_yaml_file(file_path)

        if error:
            result.errors.append(error)
        elif node_data:
            result.added = 1

        return result

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _get_yaml_files(self) -> List[Path]:
        """Get all YAML files, excluding skip directories."""
        yaml_files = []
        for file_path in self.spec_dir.rglob("*.yaml"):
            # Skip directories in SKIP_DIRS
            skip = False
            for skip_dir in SKIP_DIRS:
                if skip_dir in file_path.parts:
                    skip = True
                    break
            if not skip:
                yaml_files.append(file_path)
        return yaml_files

    def _sync_yaml_file(
        self, file_path: Path
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Sync a single YAML file to database.

        Returns:
            (node_data, error_message)
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse YAML
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return None, f"Invalid YAML structure in {file_path}"

            if "id" not in data:
                return None, f"Missing 'id' field in {file_path}"

            # Build and upsert node
            rel_path = str(file_path.relative_to(self.root_path))
            node = self._dict_to_node(data, rel_path, raw_yaml=content)
            if node:
                self.db.upsert_node(node)
                return data, None

            return None, f"Failed to create node from {file_path}"

        except yaml.YAMLError as e:
            return None, f"YAML parse error in {file_path}: {e}"
        except Exception as e:
            return None, f"Error processing {file_path}: {e}"

    def _dict_to_node(
        self,
        data: Dict[str, Any],
        source_file: str,
        raw_yaml: Optional[str] = None,
    ) -> Optional[NodeModel]:
        """Convert a YAML dict to NodeModel."""
        node_id = data.get("id")
        if not node_id:
            return None

        # Determine node type from id prefix (preferred) or explicit type field
        # ID prefix takes precedence because Component YAML uses type: module
        if node_id.startswith("prod_"):
            node_type = "product"
        elif node_id.startswith("dom_"):
            node_type = "domain"
        elif node_id.startswith("feat_"):
            node_type = "feature"
        elif node_id.startswith("comp_"):
            node_type = "component"
        elif node_id.startswith("des_"):
            node_type = "design"
        elif node_id.startswith("sub_"):
            node_type = "substrate"
        else:
            # Fall back to explicit type field
            node_type = data.get("type", "unknown")

        return NodeModel(
            id=node_id,
            type=node_type,
            name=data.get("name", node_id),
            description=data.get("description") or data.get("desc"),
            source_file=source_file,
            source_anchor=data.get("source_anchor"),
            intent=data.get("intent"),
            file_path=data.get("file_path"),
            raw_yaml=raw_yaml,
        )

    def _extract_domain_nodes(self, product_path: Path) -> List[Dict[str, Any]]:
        """Extract virtual Domain nodes from product.yaml."""
        domain_nodes = []
        try:
            content = product_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            if isinstance(data, dict) and "domains" in data:
                for domain in data.get("domains", []):
                    if isinstance(domain, dict) and "id" in domain:
                        domain_data = {
                            "id": domain["id"],
                            "type": "domain",
                            "name": domain.get("name", domain["id"]),
                            "description": domain.get("description"),
                            "exports": domain.get("exports", []),  # Preserve exports field for domain_apis
                            "_is_virtual": True,
                        }
                        domain_nodes.append(domain_data)
        except Exception:
            pass
        return domain_nodes

    def _get_node_type_from_id(self, node_id: str) -> str:
        """Determine node type from ID prefix."""
        if node_id.startswith("prod_"):
            return "product"
        elif node_id.startswith("dom_"):
            return "domain"
        elif node_id.startswith("feat_"):
            return "feature"
        elif node_id.startswith("comp_"):
            return "component"
        elif node_id.startswith("des_"):
            return "design"
        elif node_id.startswith("sub_"):
            return "substrate"
        return "unknown"

    def _build_and_sync_edges(self, nodes_dict: Dict[str, Dict[str, Any]]) -> int:
        """Build and sync all edges from node relationships."""
        edges_created = 0

        for node_id, node_data in nodes_dict.items():
            # Determine node type from ID prefix (not from data dict)
            node_type = self._get_node_type_from_id(node_id)

            # Product -> Domain (contains)
            if node_type == "product" and "domains" in node_data:
                for domain in node_data.get("domains", []):
                    if isinstance(domain, dict) and "id" in domain:
                        edge = EdgeModel(
                            source_id=node_id,
                            target_id=domain["id"],
                            relation="contains",
                        )
                        self.db.upsert_edge(edge)
                        edges_created += 1

            # Feature -> Domain (owns, via Feature.domain field)
            if node_type == "feature" and "domain" in node_data:
                domain_id = node_data["domain"]
                edge = EdgeModel(
                    source_id=domain_id,
                    target_id=node_id,
                    relation="owns",
                )
                self.db.upsert_edge(edge)
                edges_created += 1

            # Feature -> Feature (depends_on)
            if node_type == "feature" and "depends_on" in node_data:
                for dep_id in node_data.get("depends_on", []):
                    edge = EdgeModel(
                        source_id=node_id,
                        target_id=dep_id,
                        relation="depends_on",
                    )
                    self.db.upsert_edge(edge)
                    edges_created += 1

            # Feature -> Component (realized_by)
            if node_type == "feature" and "realized_by" in node_data:
                for comp_id in node_data.get("realized_by", []):
                    edge = EdgeModel(
                        source_id=node_id,
                        target_id=comp_id,
                        relation="realized_by",
                    )
                    self.db.upsert_edge(edge)
                    edges_created += 1

            # Component -> Component (dependencies)
            if node_type == "component" and "dependencies" in node_data:
                for dep_id in node_data.get("dependencies", []):
                    edge = EdgeModel(
                        source_id=node_id,
                        target_id=dep_id,
                        relation="depends_on",
                    )
                    self.db.upsert_edge(edge)
                    edges_created += 1

            # Domain -> DomainAPI (exports)
            if node_type == "domain" and "exports" in node_data:
                for api in node_data.get("exports", []):
                    if isinstance(api, dict):
                        api_model = DomainAPIModel(
                            domain_id=node_id,
                            api_name=api.get("name", ""),
                            signature=api.get("signature", ""),
                            description=api.get("description"),
                        )
                        self.db.upsert_domain_api(api_model)

        return edges_created
