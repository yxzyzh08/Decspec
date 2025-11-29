"""
DevSpec Loader - YAML 文件加载与扫描模块。

负责安全读取 YAML 文件，扫描目录并合并内容块。
"""

from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

console = Console(force_terminal=True)


def load_yaml(path: Path) -> dict[str, Any]:
    """
    安全读取单个 YAML 文件。

    Args:
        path: YAML 文件的路径

    Returns:
        解析后的字典，如果文件不存在或解析失败则返回空字典
    """
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to read {path.name}: {e}[/yellow]")
        return {}


def scan_directory(dir_path: Path) -> str:
    """
    扫描目录下的所有 YAML 文件，合并为文本块。

    Args:
        dir_path: 要扫描的目录路径

    Returns:
        合并后的文本内容，每个文件以标题分隔
    """
    if not dir_path.exists():
        return "(No files found)"

    content_blocks = []
    for f in sorted(dir_path.rglob("*.yaml")):
        data = load_yaml(f)
        block_title = f"📄 File: {f.name}"
        block_content = yaml.dump(data, allow_unicode=True, sort_keys=False)
        content_blocks.append(f"{block_title}\n{block_content}")

    return "\n\n".join(content_blocks)


def get_spec_paths(root_dir: Path) -> dict[str, Path]:
    """
    获取 SpecGraph 目录结构的路径映射。

    Args:
        root_dir: 项目根目录

    Returns:
        核心目录路径的字典映射
    """
    spec_dir = root_dir / ".specgraph"
    return {
        "root": spec_dir,
        "product": spec_dir / "product.yaml",
        "design": spec_dir / "design",
        "substrate": spec_dir / "substrate",
        "features": spec_dir / "features",
        "apis": spec_dir / "apis",
        "components": spec_dir / "components",
        "data_models": spec_dir / "datamodels",
    }
