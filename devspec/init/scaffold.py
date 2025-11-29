"""
目录结构创建器。

创建 .specgraph 目录结构和相关文件。
"""

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from devspec.init.collector import ProjectInfo

console = Console(force_terminal=True)

# 需要创建的目录列表
SPECGRAPH_DIRS = [
    "design",
    "substrate",
    "features",
    "apis",
    "components",
    "datamodels",
    ".runtime",
]


def create_directory_structure(root_dir: Path) -> Path:
    """
    创建 .specgraph 目录结构。

    Args:
        root_dir: 项目根目录

    Returns:
        Path: .specgraph 目录路径
    """
    spec_root = root_dir / ".specgraph"
    spec_root.mkdir(exist_ok=True)

    for dirname in SPECGRAPH_DIRS:
        dir_path = spec_root / dirname
        dir_path.mkdir(exist_ok=True)
        console.print(f"  [green]Created:[/green] .specgraph/{dirname}/")

    return spec_root


def write_project_files(
    root_dir: Path,
    spec_root: Path,
    info: "ProjectInfo",
    force: bool = False,
) -> dict[str, bool]:
    """
    写入项目文件（product.yaml, AGENT.md, CLAUDE.md/GEMINI.md）。

    Args:
        root_dir: 项目根目录
        spec_root: .specgraph 目录路径
        info: 项目信息
        force: 是否强制覆盖

    Returns:
        dict: 文件名到是否写入的映射
    """
    from devspec.init.collector import confirm_overwrite
    from devspec.init.generator import (
        generate_agent_md,
        generate_cli_md,
        generate_product_yaml,
        get_cli_filename,
    )

    results: dict[str, bool] = {}

    # 1. product.yaml
    product_path = spec_root / "product.yaml"
    if not product_path.exists() or force or confirm_overwrite("product.yaml"):
        product_content = generate_product_yaml(info)
        product_path.write_text(product_content, encoding="utf-8")
        console.print(f"  [green]Created:[/green] .specgraph/product.yaml")
        results["product.yaml"] = True
    else:
        console.print(f"  [yellow]Skipped:[/yellow] .specgraph/product.yaml (exists)")
        results["product.yaml"] = False

    # 2. AGENT.md
    agent_path = spec_root / "AGENT.md"
    if not agent_path.exists() or force or confirm_overwrite("AGENT.md"):
        agent_content = generate_agent_md(info)
        agent_path.write_text(agent_content, encoding="utf-8")
        console.print(f"  [green]Created:[/green] .specgraph/AGENT.md")
        results["AGENT.md"] = True
    else:
        console.print(f"  [yellow]Skipped:[/yellow] .specgraph/AGENT.md (exists)")
        results["AGENT.md"] = False

    # 3. CLAUDE.md 或 GEMINI.md（项目根目录）
    cli_filename = get_cli_filename(info)
    cli_path = root_dir / cli_filename
    if not cli_path.exists() or force or confirm_overwrite(cli_filename):
        cli_content = generate_cli_md(info)
        cli_path.write_text(cli_content, encoding="utf-8")
        console.print(f"  [green]Created:[/green] {cli_filename}")
        results[cli_filename] = True
    else:
        console.print(f"  [yellow]Skipped:[/yellow] {cli_filename} (exists)")
        results[cli_filename] = False

    return results


def check_already_initialized(root_dir: Path) -> bool:
    """
    检查项目是否已经初始化。

    Args:
        root_dir: 项目根目录

    Returns:
        bool: 是否已初始化（product.yaml 存在）
    """
    spec_root = root_dir / ".specgraph"
    product_path = spec_root / "product.yaml"
    return product_path.exists()
