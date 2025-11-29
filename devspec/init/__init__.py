"""
DevSpec Init Module - 项目初始化功能。

提供交互式项目初始化，生成 SpecGraph 目录结构和 AI 协议文件。
"""

from devspec.init.collector import collect_project_info
from devspec.init.generator import generate_agent_md, generate_cli_md, generate_product_yaml
from devspec.init.scaffold import create_directory_structure

__all__ = [
    "collect_project_info",
    "create_directory_structure",
    "generate_product_yaml",
    "generate_agent_md",
    "generate_cli_md",
]
