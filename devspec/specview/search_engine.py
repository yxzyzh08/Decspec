"""
Search Engine - Full-text search with SQLite FTS5.

This module provides the SearchEngine class for full-text search
across SpecGraph nodes using SQLite FTS5 virtual tables.

Component: comp_specview_search_engine
Feature: feat_specview_search
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re

from sqlmodel import select, text

from devspec.core.graph_database import GraphDatabase, NodeModel


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class SearchSuggestion:
    """Search suggestion for empty state."""

    text: str
    action: str  # try_shorter, try_prefix, link_to_hierarchy
    example: Optional[str] = None
    url: Optional[str] = None


@dataclass
class SearchResultItem:
    """Single search result item."""

    node_id: str
    node_type: str
    title: str
    snippet: str
    score: float
    url: str


@dataclass
class SearchResult:
    """Search result container."""

    query: str
    total_count: int
    items: List[SearchResultItem] = field(default_factory=list)
    suggestions: List[SearchSuggestion] = field(default_factory=list)


# =============================================================================
# Constants
# =============================================================================

MIN_QUERY_LENGTH = 2
MAX_SUGGESTIONS = 10
SNIPPET_CONTEXT_CHARS = 50
MAX_SEARCH_RESULTS = 50

# FTS5 SQL statements
FTS5_CREATE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    node_id,
    node_type,
    name,
    content,
    tokenize='unicode61'
)
"""

FTS5_REBUILD_SQL = """
INSERT INTO nodes_fts(node_id, node_type, name, content)
SELECT id, type, name,
       COALESCE(intent, '') || ' ' || COALESCE(description, '') || ' ' || COALESCE(raw_yaml, '')
FROM nodes
"""

FTS5_SEARCH_SQL = """
SELECT n.*, bm25(nodes_fts) as score
FROM nodes_fts
JOIN nodes n ON nodes_fts.node_id = n.id
WHERE nodes_fts MATCH ?
ORDER BY score
LIMIT ?
"""

EMPTY_STATE_SUGGESTIONS = [
    SearchSuggestion(
        text="尝试更短的关键词",
        example="搜索 'core' 而非 'core engine module'",
        action="try_shorter",
    ),
    SearchSuggestion(
        text="尝试搜索 ID 前缀",
        example="feat_, comp_, dom_, des_, sub_",
        action="try_prefix",
    ),
    SearchSuggestion(
        text="浏览层级结构找到目标",
        action="link_to_hierarchy",
        url="/hierarchy",
    ),
]

SEARCH_HINTS = {
    "empty_input": "输入关键词开始搜索，支持 ID、名称、描述",
    "single_char": "请输入至少 2 个字符",
    "id_prefix": "检测到 ID 前缀，将优先匹配节点 ID",
}


# =============================================================================
# SearchEngine Class
# =============================================================================

class SearchEngine:
    """
    SpecGraph search engine using SQLite FTS5.

    Provides full-text search across node IDs, names, and content
    with BM25 ranking and snippet generation.
    """

    def __init__(self, db: GraphDatabase) -> None:
        """
        Initialize search engine with database dependency.

        Args:
            db: SpecGraph database instance
        """
        self.db = db
        self._fts_initialized = False

    def ensure_fts_index(self) -> None:
        """
        Ensure FTS5 virtual table exists and is populated.

        Creates the FTS5 table if it doesn't exist and rebuilds
        the index if the table is empty.
        """
        if self._fts_initialized:
            return

        with self.db.get_session() as session:
            # Check if FTS table exists
            result = session.exec(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes_fts'")
            ).first()

            if not result:
                # Create FTS5 table
                session.exec(text(FTS5_CREATE_SQL))
                session.commit()
                self.rebuild_fts_index()
            else:
                # Check if table has data
                count_result = session.exec(text("SELECT COUNT(*) FROM nodes_fts")).first()
                if count_result and count_result[0] == 0:
                    self.rebuild_fts_index()

        self._fts_initialized = True

    def rebuild_fts_index(self) -> None:
        """
        Rebuild FTS5 index from nodes table.

        Clears existing index and repopulates from current node data.
        Call this after sync operations.
        """
        with self.db.get_session() as session:
            # Clear existing index
            session.exec(text("DELETE FROM nodes_fts"))

            # Populate from nodes table
            session.exec(text(FTS5_REBUILD_SQL))

            # Optimize index
            session.exec(text("INSERT INTO nodes_fts(nodes_fts) VALUES('optimize')"))

            session.commit()

    def search_nodes(
        self,
        query: str,
        type_filter: Optional[str] = None,
    ) -> SearchResult:
        """
        Search nodes by ID, name, or content.

        Args:
            query: Search query string
            type_filter: Optional filter by node type (feature, component, etc.)

        Returns:
            SearchResult with items and suggestions
        """
        # Validate query length
        if len(query) < MIN_QUERY_LENGTH:
            return SearchResult(
                query=query,
                total_count=0,
                items=[],
                suggestions=EMPTY_STATE_SUGGESTIONS,
            )

        # Detect query type
        is_id_prefix = query.startswith(("feat_", "comp_", "des_", "sub_", "dom_", "prod_"))

        items: List[SearchResultItem] = []

        with self.db.get_session() as session:
            if is_id_prefix:
                # ID prefix search - use simple LIKE
                nodes = session.exec(
                    select(NodeModel).where(NodeModel.id.startswith(query))
                ).all()

                for node in nodes:
                    if type_filter and node.type != type_filter:
                        continue

                    items.append(self._node_to_result_item(node, query))

            else:
                # Try FTS5 search first, fall back to simple search
                try:
                    self.ensure_fts_index()
                    items = self._fts_search(session, query, type_filter)
                except Exception:
                    # Fall back to simple search if FTS fails
                    items = self._simple_search(session, query, type_filter)

        # Generate suggestions if no results
        suggestions = EMPTY_STATE_SUGGESTIONS if not items else []

        return SearchResult(
            query=query,
            total_count=len(items),
            items=items,
            suggestions=suggestions,
        )

    def _fts_search(
        self,
        session,
        query: str,
        type_filter: Optional[str],
    ) -> List[SearchResultItem]:
        """Perform FTS5 search."""
        # Convert query to FTS5 syntax (OR between words)
        fts_query = " OR ".join(query.split())

        results = session.exec(
            text(FTS5_SEARCH_SQL),
            {"query": fts_query, "limit": MAX_SEARCH_RESULTS},
        ).all()

        items = []
        for row in results:
            node = session.get(NodeModel, row.id)
            if node:
                if type_filter and node.type != type_filter:
                    continue
                items.append(self._node_to_result_item(node, query, row.score))

        return items

    def _simple_search(
        self,
        session,
        query: str,
        type_filter: Optional[str],
    ) -> List[SearchResultItem]:
        """Perform simple text search (fallback)."""
        query_lower = query.lower()
        all_nodes = session.exec(select(NodeModel)).all()

        scored_nodes = []
        for node in all_nodes:
            if type_filter and node.type != type_filter:
                continue

            score = 0

            # Check ID
            if query_lower in node.id.lower():
                score += 3

            # Check name
            if node.name and query_lower in node.name.lower():
                score += 2

            # Check description
            if node.description and query_lower in node.description.lower():
                score += 1

            # Check intent
            if node.intent and query_lower in node.intent.lower():
                score += 1

            if score > 0:
                scored_nodes.append((node, score))

        # Sort by score and take top results
        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        items = []
        for node, score in scored_nodes[:MAX_SEARCH_RESULTS]:
            items.append(self._node_to_result_item(node, query, float(score)))

        return items

    def _node_to_result_item(
        self,
        node: NodeModel,
        query: str,
        score: float = 1.0,
    ) -> SearchResultItem:
        """Convert node to search result item."""
        # Generate snippet
        content = node.description or node.intent or ""
        snippet = self._extract_snippet(content, query, SNIPPET_CONTEXT_CHARS)
        snippet = self._highlight_keywords(snippet, query)

        # Determine URL based on node type
        if node.type in ("feature", "component", "domain"):
            url = f"/hierarchy/node/{node.type}/{node.id}"
        elif node.type == "design":
            url = f"/design/design/{node.id}"
        elif node.type == "substrate":
            url = f"/design/substrate/{node.id}"
        else:
            url = f"/hierarchy/node/{node.type}/{node.id}"

        return SearchResultItem(
            node_id=node.id,
            node_type=node.type,
            title=node.name or node.id,
            snippet=snippet,
            score=score,
            url=url,
        )

    def _extract_snippet(self, content: str, query: str, context_chars: int) -> str:
        """Extract snippet around query match."""
        if not content:
            return ""

        query_lower = query.lower()
        content_lower = content.lower()
        pos = content_lower.find(query_lower)

        if pos == -1:
            # Query not found, return beginning
            if len(content) <= context_chars * 2:
                return content
            return content[:context_chars * 2] + "..."

        # Extract around match
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)

        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _highlight_keywords(self, text: str, query: str) -> str:
        """Highlight keywords with <mark> tags."""
        if not text or not query:
            return text

        words = query.split()
        for word in words:
            if len(word) < 2:
                continue
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            text = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", text)

        return text

    def get_search_suggestions(self, prefix: str) -> List[str]:
        """
        Get search suggestions for autocomplete.

        Args:
            prefix: Input prefix

        Returns:
            List of matching node IDs
        """
        if len(prefix) < MIN_QUERY_LENGTH:
            return []

        suggestions = []
        with self.db.get_session() as session:
            nodes = session.exec(
                select(NodeModel).where(NodeModel.id.startswith(prefix))
            ).all()

            for node in nodes[:MAX_SUGGESTIONS]:
                suggestions.append(node.id)

        return suggestions
