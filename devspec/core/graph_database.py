"""
SpecGraph Database - SQLite database model and connection management.

This module provides the core data models (NodeModel, EdgeModel, DomainAPIModel)
and database operations (CRUD) for the SpecGraph knowledge graph persistence.

Component: comp_graph_database
Feature: feat_specgraph_database
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlmodel import SQLModel, Field, Session, create_engine, select


# =============================================================================
# Constants
# =============================================================================

DEFAULT_DB_PATH = ".specgraph/.runtime/specgraph.db"

RELATION_TYPES = [
    "contains",      # Product -> Domain
    "owns",          # Domain -> Feature (via Feature.domain field)
    "depends_on",    # Feature -> Feature, Component -> Component
    "realized_by",   # Feature -> Component
    "binds_to",      # Component -> CodeFile
    "exports",       # Domain -> DomainAPI
    "consumes",      # Feature -> DomainAPI
    "references",    # Design/Substrate cross-references
]


# =============================================================================
# Data Models
# =============================================================================

class NodeModel(SQLModel, table=True):
    """SQLModel for nodes table."""

    __tablename__ = "nodes"

    id: str = Field(primary_key=True, description="Node ID (e.g., feat_xxx, comp_xxx)")
    type: str = Field(index=True, description="Node type (product, domain, feature, component, design, substrate)")
    name: str = Field(description="Human-readable name")
    description: Optional[str] = Field(default=None, description="Node description")
    source_file: Optional[str] = Field(default=None, description="Source YAML file path")
    source_anchor: Optional[str] = Field(default=None, description="PRD anchor reference")
    intent: Optional[str] = Field(default=None, description="Purpose/intent of the node")
    file_path: Optional[str] = Field(default=None, description="Physical file path (for components)")
    content_hash: Optional[str] = Field(default=None, index=True, description="Hash of YAML content for change detection")
    raw_yaml: Optional[str] = Field(default=None, description="Original YAML content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class EdgeModel(SQLModel, table=True):
    """SQLModel for edges table."""

    __tablename__ = "edges"

    id: Optional[int] = Field(default=None, primary_key=True, description="Auto-increment primary key")
    source_id: str = Field(index=True, description="Source node ID")
    target_id: str = Field(index=True, description="Target node ID")
    relation: str = Field(index=True, description="Relation type (contains, owns, depends_on, etc.)")
    edge_metadata: Optional[str] = Field(default=None, description="JSON-encoded metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class DomainAPIModel(SQLModel, table=True):
    """SQLModel for domain_apis table."""

    __tablename__ = "domain_apis"

    id: Optional[int] = Field(default=None, primary_key=True, description="Auto-increment primary key")
    domain_id: str = Field(index=True, description="Domain node ID")
    api_name: str = Field(description="API function name")
    signature: str = Field(description="Function signature")
    description: Optional[str] = Field(default=None, description="API description")


# =============================================================================
# Database Manager
# =============================================================================

class GraphDatabase:
    """Main database manager class for SpecGraph persistence."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to .specgraph/.runtime/specgraph.db
        """
        if db_path is None:
            db_path = Path(DEFAULT_DB_PATH)

        self.db_path = Path(db_path)

        # Create parent directory if not exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create SQLite engine
        self.engine = create_engine(f"sqlite:///{self.db_path}")

    def create_tables(self) -> None:
        """Create all required tables if they don't exist."""
        SQLModel.metadata.create_all(self.engine)

    def close(self) -> None:
        """Close the database connection and dispose of the engine."""
        self.engine.dispose()

    def get_session(self) -> Session:
        """
        Get a database session for transactions.

        Returns:
            SQLModel Session object
        """
        return Session(self.engine)

    def upsert_node(self, node: NodeModel) -> None:
        """
        Insert or update a node in the database.

        Args:
            node: NodeModel to upsert
        """
        with self.get_session() as session:
            # Update timestamp
            node.updated_at = datetime.utcnow()
            session.merge(node)
            session.commit()

    def upsert_edge(self, edge: EdgeModel) -> None:
        """
        Insert or update an edge in the database.

        Args:
            edge: EdgeModel to upsert
        """
        with self.get_session() as session:
            # Check if edge already exists
            statement = select(EdgeModel).where(
                EdgeModel.source_id == edge.source_id,
                EdgeModel.target_id == edge.target_id,
                EdgeModel.relation == edge.relation
            )
            existing = session.exec(statement).first()

            if existing:
                # Update metadata if edge exists
                existing.edge_metadata = edge.edge_metadata
                session.add(existing)
            else:
                # Insert new edge
                session.add(edge)

            session.commit()

    def delete_node(self, node_id: str) -> None:
        """
        Delete a node and its related edges.

        Args:
            node_id: ID of node to delete
        """
        with self.get_session() as session:
            # Delete all edges where this node is source or target
            statement = select(EdgeModel).where(
                (EdgeModel.source_id == node_id) | (EdgeModel.target_id == node_id)
            )
            edges = session.exec(statement).all()
            for edge in edges:
                session.delete(edge)

            # Delete the node itself
            node = session.get(NodeModel, node_id)
            if node:
                session.delete(node)

            session.commit()

    def get_node(self, node_id: str) -> Optional[NodeModel]:
        """
        Retrieve a node by ID.

        Args:
            node_id: Node ID to retrieve

        Returns:
            NodeModel or None if not found
        """
        with self.get_session() as session:
            return session.get(NodeModel, node_id)

    def get_all_nodes(self) -> List[NodeModel]:
        """
        Retrieve all nodes from database.

        Returns:
            List of all NodeModel
        """
        with self.get_session() as session:
            statement = select(NodeModel)
            return list(session.exec(statement).all())

    def get_all_edges(self) -> List[EdgeModel]:
        """
        Retrieve all edges from database.

        Returns:
            List of all EdgeModel
        """
        with self.get_session() as session:
            statement = select(EdgeModel)
            return list(session.exec(statement).all())

    def upsert_domain_api(self, api: DomainAPIModel) -> None:
        """
        Insert or update a domain API.

        Args:
            api: DomainAPIModel to upsert
        """
        with self.get_session() as session:
            # Check if API already exists
            statement = select(DomainAPIModel).where(
                DomainAPIModel.domain_id == api.domain_id,
                DomainAPIModel.api_name == api.api_name
            )
            existing = session.exec(statement).first()

            if existing:
                existing.signature = api.signature
                existing.description = api.description
                session.add(existing)
            else:
                session.add(api)

            session.commit()

    def delete_domain_apis(self, domain_id: str) -> None:
        """
        Delete all APIs for a domain.

        Args:
            domain_id: Domain ID whose APIs to delete
        """
        with self.get_session() as session:
            statement = select(DomainAPIModel).where(
                DomainAPIModel.domain_id == domain_id
            )
            apis = session.exec(statement).all()
            for api in apis:
                session.delete(api)
            session.commit()

    def get_domain_apis(self, domain_id: str) -> List[DomainAPIModel]:
        """
        Get all APIs for a domain.

        Args:
            domain_id: Domain ID to query

        Returns:
            List of DomainAPIModel
        """
        with self.get_session() as session:
            statement = select(DomainAPIModel).where(
                DomainAPIModel.domain_id == domain_id
            )
            return list(session.exec(statement).all())

    def clear_all(self) -> None:
        """
        Clear all data from the database (nodes, edges, and domain_apis).

        Used for full synchronization to start fresh.
        """
        with self.get_session() as session:
            # Delete all edges
            edges = session.exec(select(EdgeModel)).all()
            for edge in edges:
                session.delete(edge)

            # Delete all domain APIs
            apis = session.exec(select(DomainAPIModel)).all()
            for api in apis:
                session.delete(api)

            # Delete all nodes
            nodes = session.exec(select(NodeModel)).all()
            for node in nodes:
                session.delete(node)

            session.commit()
