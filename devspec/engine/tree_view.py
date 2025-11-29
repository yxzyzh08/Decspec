"""
全景视图模块 - 生成项目结构树。

提供 devspec tree 命令的核心逻辑。
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.tree import Tree
from sqlmodel import Session, select

from .db_models import Node, get_session
from .loader import get_spec_paths, load_yaml

console = Console(force_terminal=True)

# 状态图标映射
STATUS_ICONS = {
    "DONE": "[green]OK[/green]",
    "IN_PROGRESS": "[yellow]WIP[/yellow]",
    "PLANNED": "[dim]PLAN[/dim]",
    "DRAFT": "[dim]DRAFT[/dim]",
    "ARCHIVED": "[dim]ARCH[/dim]",
    "BOOTSTRAPPING": "[cyan]BOOT[/cyan]",
}


def get_status_icon(status: str) -> str:
    """获取状态对应的图标。"""
    return STATUS_ICONS.get(status, f"[dim]{status}[/dim]")


def load_product_info(spec_root: Path) -> dict[str, Any]:
    """加载产品信息。"""
    product_path = spec_root / "product.yaml"
    return load_yaml(product_path)


def query_features_by_domain(session: Session) -> dict[str, list[dict]]:
    """
    查询所有 Feature 并按 domain 分组。

    Returns:
        dict: {domain_id: [feature_info, ...]}
    """
    stmt = select(Node).where(Node.type == "Feature")
    features = session.exec(stmt).all()

    grouped: dict[str, list[dict]] = {}
    for feat in features:
        content = feat.get_content()
        domain = content.get("meta", {}).get("domain", "unknown")
        status = content.get("meta", {}).get("status", "UNKNOWN")
        priority = content.get("meta", {}).get("priority", "")

        if domain not in grouped:
            grouped[domain] = []

        grouped[domain].append({
            "id": feat.id,
            "status": status,
            "priority": priority,
            "summary": content.get("intent", {}).get("summary", ""),
        })

    # 按 priority 和 id 排序
    for domain in grouped:
        grouped[domain].sort(key=lambda x: (x.get("priority", "P9"), x["id"]))

    return grouped


def query_components_by_domain(session: Session) -> dict[str, list[dict]]:
    """
    查询所有 Component 并按 domain 分组。

    Returns:
        dict: {domain_id: [component_info, ...]}
    """
    stmt = select(Node).where(Node.type == "Component")
    components = session.exec(stmt).all()

    grouped: dict[str, list[dict]] = {}
    for comp in components:
        content = comp.get_content()
        domain = content.get("meta", {}).get("domain", "unknown")
        status = content.get("meta", {}).get("status", "UNKNOWN")

        if domain not in grouped:
            grouped[domain] = []

        grouped[domain].append({
            "id": comp.id,
            "status": status,
            "name": content.get("info", {}).get("name", comp.id),
        })

    return grouped


def build_tree(root_dir: Path, show_components: bool = False) -> Tree:
    """
    构建项目结构树。

    Args:
        root_dir: 项目根目录
        show_components: 是否显示 Component

    Returns:
        rich.tree.Tree 对象
    """
    paths = get_spec_paths(root_dir)
    spec_root = paths["root"]

    # 加载产品信息
    product = load_product_info(spec_root)
    product_name = product.get("info", {}).get("name", "Unknown Project")
    product_version = product.get("meta", {}).get("version", "0.0.0")
    product_status = product.get("meta", {}).get("status", "")

    # 构建根节点
    status_str = f" ({product_status})" if product_status else ""
    tree = Tree(f"[bold]{product_name}[/bold] v{product_version}{status_str}")

    # 获取 domain 列表
    domains = product.get("domains", [])

    # 查询 Features
    session = get_session(spec_root)
    features_by_domain = query_features_by_domain(session)
    components_by_domain = query_components_by_domain(session) if show_components else {}

    # 统计
    total_features = sum(len(f) for f in features_by_domain.values())
    done_features = sum(
        1 for feats in features_by_domain.values()
        for f in feats if f["status"] == "DONE"
    )

    # 构建 domain 分支
    for domain in domains:
        domain_id = domain.get("id", "")
        domain_name = domain.get("name", domain_id)

        # 计算 domain 完成度
        domain_features = features_by_domain.get(domain_id, [])
        domain_done = sum(1 for f in domain_features if f["status"] == "DONE")
        domain_total = len(domain_features)

        if domain_total > 0:
            progress = f" [{domain_done}/{domain_total}]"
        else:
            progress = ""

        domain_branch = tree.add(f"[blue]{domain_name}[/blue]{progress}")

        # 添加 Features
        if domain_features:
            for feat in domain_features:
                status_icon = get_status_icon(feat["status"])
                feat_line = f"{feat['id']} {status_icon}"
                domain_branch.add(feat_line)
        else:
            domain_branch.add("[dim](no features)[/dim]")

        # 添加 Components (可选)
        if show_components:
            domain_comps = components_by_domain.get(domain_id, [])
            if domain_comps:
                comp_branch = domain_branch.add("[dim]components:[/dim]")
                for comp in domain_comps:
                    status_icon = get_status_icon(comp["status"])
                    comp_branch.add(f"[dim]{comp['id']}[/dim] {status_icon}")

    session.close()

    # 添加统计摘要
    tree.add(f"\n[dim]Total: {done_features}/{total_features} features done[/dim]")

    return tree


def print_tree(root_dir: Path, show_components: bool = False) -> None:
    """打印项目结构树。"""
    tree = build_tree(root_dir, show_components)
    console.print(tree)
