"""
DevSpec Sync Engine - YAML 到 SQLite 同步模块。

负责遍历 .specgraph 目录，解析 YAML 文件并写入 SQLite 数据库。
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from sqlmodel import Session, select

from .db_models import Edge, EdgeType, Node, NodeType, get_db_path, init_database
from .loader import get_spec_paths, load_yaml

console = Console(force_terminal=True)


@dataclass
class SyncStats:
    """同步统计信息。"""
    nodes_created: int = 0
    nodes_updated: int = 0
    edges_created: int = 0
    errors: int = 0


def extract_search_text(data: dict[str, Any]) -> str:
    """
    从 YAML 数据中提取可搜索文本。

    Args:
        data: YAML 解析后的字典

    Returns:
        合并后的搜索文本
    """
    texts = []

    # 提取 meta 信息
    meta = data.get("meta", {})
    if meta.get("id"):
        texts.append(meta["id"])
    if meta.get("tags"):
        texts.extend(meta["tags"])

    # 提取 info 信息
    info = data.get("info", {})
    if info.get("title"):
        texts.append(info["title"])
    if info.get("name"):
        texts.append(info["name"])

    # 提取 intent 信息 (Feature)
    intent = data.get("intent", {})
    if intent.get("summary"):
        texts.append(intent["summary"])
    if intent.get("user_story"):
        texts.append(intent["user_story"])

    # 提取 content (Substrate/Design)
    if data.get("content"):
        texts.append(str(data["content"]))

    return " ".join(texts)


def infer_node_type(file_path: Path, data: dict[str, Any]) -> str:
    """
    推断节点类型。

    优先使用 YAML 中的 meta.type，否则根据目录推断。

    Args:
        file_path: 文件路径
        data: YAML 数据

    Returns:
        节点类型字符串
    """
    # 优先使用显式声明
    explicit_type = data.get("meta", {}).get("type")
    if explicit_type:
        return explicit_type

    # 根据目录推断
    parent_name = file_path.parent.name
    type_map = {
        "features": NodeType.FEATURE.value,
        "apis": NodeType.API.value,
        "components": NodeType.COMPONENT.value,
        "substrate": NodeType.SUBSTRATE.value,
        "design": NodeType.DESIGN.value,
        "data_models": NodeType.DATA_MODEL.value,
    }
    return type_map.get(parent_name, "Unknown")


def extract_edges(node_id: str, data: dict[str, Any]) -> list[tuple[str, str, str]]:
    """
    从 YAML 数据中提取边关系。

    Args:
        node_id: 当前节点 ID
        data: YAML 数据

    Returns:
        边列表 [(source_id, target_id, edge_type), ...]
    """
    edges = []

    # dependencies: 当前节点依赖其他节点
    dependencies = data.get("dependencies", [])
    for dep_id in dependencies:
        edges.append((node_id, dep_id, EdgeType.DEPENDS_ON.value))

    # realized_by: 当前节点被某组件实现
    realized_by = data.get("realized_by", [])
    for comp_id in realized_by:
        edges.append((node_id, comp_id, EdgeType.REALIZED_BY.value))

    # domain: 当前节点属于某领域
    domain = data.get("meta", {}).get("domain")
    if domain:
        edges.append((node_id, domain, EdgeType.BELONGS_TO.value))

    # references: 显式引用
    references = data.get("references", [])
    for ref_id in references:
        edges.append((node_id, ref_id, EdgeType.REFERENCES.value))

    return edges


def sync_yaml_file(
    session: Session,
    file_path: Path,
    spec_root: Path,
    stats: SyncStats,
) -> list[tuple[str, str, str]]:
    """
    同步单个 YAML 文件到数据库。

    Args:
        session: 数据库会话
        file_path: YAML 文件路径
        spec_root: .specgraph 根目录
        stats: 统计信息

    Returns:
        提取的边列表
    """
    data = load_yaml(file_path)
    if not data:
        stats.errors += 1
        return []

    # 获取节点 ID
    node_id = data.get("meta", {}).get("id")
    if not node_id:
        console.print(f"[yellow]Warning: No meta.id in {file_path.name}, skipping[/yellow]")
        stats.errors += 1
        return []

    # 计算相对路径
    relative_path = str(file_path.relative_to(spec_root))

    # 检查节点是否存在
    existing = session.get(Node, node_id)

    node = existing or Node(id=node_id)
    node.type = infer_node_type(file_path, data)
    node.domain = data.get("meta", {}).get("domain")
    node.file_path = relative_path
    node.set_content(data)
    node.search_text = extract_search_text(data)
    node.updated_at = datetime.now()

    if existing:
        stats.nodes_updated += 1
    else:
        stats.nodes_created += 1
        session.add(node)

    # 提取边关系
    edges = extract_edges(node_id, data)
    return edges


def sync_directory(
    session: Session,
    dir_path: Path,
    spec_root: Path,
    stats: SyncStats,
) -> list[tuple[str, str, str]]:
    """
    同步目录下所有 YAML 文件。

    Args:
        session: 数据库会话
        dir_path: 目录路径
        spec_root: .specgraph 根目录
        stats: 统计信息

    Returns:
        所有提取的边列表
    """
    all_edges = []

    if not dir_path.exists():
        return all_edges

    # 递归扫描所有 YAML 文件（包括子目录）
    for yaml_file in dir_path.rglob("*.yaml"):
        edges = sync_yaml_file(session, yaml_file, spec_root, stats)
        all_edges.extend(edges)

    return all_edges


def sync_edges(
    session: Session,
    edges: list[tuple[str, str, str]],
    stats: SyncStats,
) -> None:
    """
    同步边关系到数据库。

    仅创建目标节点存在的边。

    Args:
        session: 数据库会话
        edges: 边列表
        stats: 统计信息
    """
    for source_id, target_id, edge_type in edges:
        # 检查目标节点是否存在
        target = session.get(Node, target_id)
        if not target:
            # 目标不存在，跳过（可能是 domain ID 等未作为节点存储的引用）
            continue

        # 检查边是否已存在
        stmt = select(Edge).where(
            Edge.source_id == source_id,
            Edge.target_id == target_id,
            Edge.type == edge_type,
        )
        existing = session.exec(stmt).first()

        if not existing:
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                type=edge_type,
            )
            session.add(edge)
            stats.edges_created += 1


def run_sync(root_dir: Path, clean: bool = False) -> SyncStats:
    """
    执行完整的同步流程。

    Args:
        root_dir: 项目根目录
        clean: 是否清空现有数据

    Returns:
        同步统计信息
    """
    paths = get_spec_paths(root_dir)
    spec_root = paths["root"]
    stats = SyncStats()

    # 初始化数据库
    if clean:
        db_path = get_db_path(spec_root)
        if db_path.exists():
            db_path.unlink()
        console.print("[blue]Cleaned existing database.[/blue]")

    session = init_database(spec_root)
    all_edges: list[tuple[str, str, str]] = []

    try:
        # 1. 同步 product.yaml
        if paths["product"].exists():
            edges = sync_yaml_file(session, paths["product"], spec_root, stats)
            all_edges.extend(edges)

        # 2. 同步各目录
        directories = ["features", "apis", "components", "substrate", "design", "data_models"]
        for dirname in directories:
            dir_path = paths.get(dirname)
            if dir_path:
                edges = sync_directory(session, dir_path, spec_root, stats)
                all_edges.extend(edges)

        # 3. 提交节点
        session.commit()

        # 4. 同步边关系
        sync_edges(session, all_edges, stats)
        session.commit()

    finally:
        session.close()

    return stats
