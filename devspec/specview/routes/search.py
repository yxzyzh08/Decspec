"""
Search Router - Full-text search functionality.

Component: comp_specview_routes
Feature: feat_specview_search
"""

from typing import List, Optional
import re

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import select

from devspec.specview.server import get_db, get_templates
from devspec.core.graph_database import NodeModel


router = APIRouter(tags=["search"])


# Constants
MIN_QUERY_LENGTH = 2
MAX_SEARCH_RESULTS = 50
SNIPPET_CONTEXT_CHARS = 50

# Empty state suggestions
EMPTY_STATE_SUGGESTIONS = [
    {
        "text": "尝试更短的关键词",
        "example": "搜索 'core' 而非 'core engine module'",
        "action": "try_shorter",
    },
    {
        "text": "尝试搜索 ID 前缀",
        "example": "feat_, comp_, dom_, des_, sub_",
        "action": "try_prefix",
    },
    {
        "text": "浏览层级结构找到目标",
        "action": "link_to_hierarchy",
        "url": "/hierarchy",
    },
]

# Search hints
SEARCH_HINTS = {
    "empty_input": "输入关键词开始搜索，支持 ID、名称、描述",
    "single_char": "请输入至少 2 个字符",
    "id_prefix": "检测到 ID 前缀，将优先匹配节点 ID",
}


class SearchResultItem(BaseModel):
    """Single search result item."""

    node_id: str
    node_type: str
    title: str
    snippet: str
    score: float
    url: str


class SearchResult(BaseModel):
    """Search result container."""

    query: str
    total_count: int
    items: List[SearchResultItem]
    suggestions: List[dict]
    hint: Optional[str] = None


@router.get("/", response_class=HTMLResponse)
async def search_view(
    request: Request,
    q: str = Query(default="", description="Search query"),
    type_filter: Optional[str] = Query(default=None, description="Filter by type"),
) -> HTMLResponse:
    """
    Render search page with results.

    Args:
        q: Search query string
        type_filter: Optional type filter (feature, component, etc.)

    Returns:
        Rendered search.html template
    """
    templates = get_templates()

    # Process search
    result = await _perform_search(q, type_filter)

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "query": q,
            "type_filter": type_filter,
            "result": result.model_dump(),
            "breadcrumbs": [{"name": "Search", "url": None}],
        },
    )


@router.get("/results", response_class=HTMLResponse)
async def search_results(
    request: Request,
    q: str = Query(default="", description="Search query"),
    type_filter: Optional[str] = Query(default=None, description="Filter by type"),
) -> HTMLResponse:
    """
    Search results partial (htmx endpoint for live search).

    Args:
        q: Search query string
        type_filter: Optional type filter

    Returns:
        Rendered partial template with search results
    """
    templates = get_templates()

    result = await _perform_search(q, type_filter)

    return templates.TemplateResponse(
        "partials/search_results.html",
        {
            "request": request,
            "result": result.model_dump(),
        },
    )


async def _perform_search(query: str, type_filter: Optional[str] = None) -> SearchResult:
    """
    Perform search and return results.

    Args:
        query: Search query string
        type_filter: Optional type filter

    Returns:
        SearchResult with items and suggestions
    """
    # Handle empty or short query
    if not query:
        return SearchResult(
            query=query,
            total_count=0,
            items=[],
            suggestions=[],
            hint=SEARCH_HINTS["empty_input"],
        )

    if len(query) < MIN_QUERY_LENGTH:
        return SearchResult(
            query=query,
            total_count=0,
            items=[],
            suggestions=[],
            hint=SEARCH_HINTS["single_char"],
        )

    db = get_db()
    items = []

    # Detect query type
    is_id_prefix = query.startswith(("feat_", "comp_", "des_", "sub_", "dom_", "prod_"))
    hint = SEARCH_HINTS["id_prefix"] if is_id_prefix else None

    with db.get_session() as session:
        if is_id_prefix:
            # ID prefix search - exact match on ID
            nodes = session.exec(
                select(NodeModel).where(NodeModel.id.startswith(query))
            ).all()
        else:
            # Full-text search on name, description, intent
            query_lower = query.lower()
            all_nodes = session.exec(select(NodeModel)).all()

            nodes = []
            for node in all_nodes:
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
                    nodes.append((node, score))

            # Sort by score and take top results
            nodes.sort(key=lambda x: x[1], reverse=True)
            nodes = [n[0] for n in nodes[:MAX_SEARCH_RESULTS]]

        # Apply type filter
        if type_filter:
            nodes = [n for n in nodes if n.type == type_filter]

        # Build result items
        for node in nodes:
            # Generate snippet
            content = node.description or node.intent or ""
            snippet = _extract_snippet(content, query, SNIPPET_CONTEXT_CHARS)
            snippet = _highlight_keywords(snippet, query)

            # Determine URL based on node type
            if node.type in ("feature", "component", "domain"):
                url = f"/hierarchy/node/{node.type}/{node.id}"
            elif node.type == "design":
                url = f"/design/design/{node.id}"
            elif node.type == "substrate":
                url = f"/design/substrate/{node.id}"
            else:
                url = f"/hierarchy/node/{node.type}/{node.id}"

            items.append(SearchResultItem(
                node_id=node.id,
                node_type=node.type,
                title=node.name or node.id,
                snippet=snippet,
                score=1.0,  # Simple scoring for now
                url=url,
            ))

    # Generate suggestions if no results
    suggestions = EMPTY_STATE_SUGGESTIONS if not items else []

    return SearchResult(
        query=query,
        total_count=len(items),
        items=items,
        suggestions=suggestions,
        hint=hint,
    )


def _extract_snippet(content: str, query: str, context_chars: int) -> str:
    """
    Extract a snippet around the query match.

    Args:
        content: Full content string
        query: Search query
        context_chars: Number of characters to show before/after match

    Returns:
        Snippet with ellipsis if truncated
    """
    if not content:
        return ""

    # Find query position (case-insensitive)
    query_lower = query.lower()
    content_lower = content.lower()
    pos = content_lower.find(query_lower)

    if pos == -1:
        # Query not found, return beginning of content
        if len(content) <= context_chars * 2:
            return content
        return content[:context_chars * 2] + "..."

    # Extract snippet around match
    start = max(0, pos - context_chars)
    end = min(len(content), pos + len(query) + context_chars)

    snippet = content[start:end]

    # Add ellipsis if truncated
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    return snippet


def _highlight_keywords(text: str, query: str) -> str:
    """
    Highlight query keywords in text with <mark> tags.

    Args:
        text: Text to highlight
        query: Search query (may contain multiple words)

    Returns:
        Text with <mark> tags around matches
    """
    if not text or not query:
        return text

    # Split query into words
    words = query.split()

    for word in words:
        if len(word) < 2:
            continue

        # Case-insensitive replacement with mark tags
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        text = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", text)

    return text
