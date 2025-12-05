"""
Frontend Component Library - Usage Statistics
Part of comp_frontend_component_library
"""

import re
from pathlib import Path
from typing import Dict, List

from .component_index import ComponentIndex

# Jinja2 include 模式: {% include "components/..." %}
INCLUDE_PATTERN = re.compile(r'{%\s*include\s*["\']components/([^"\']+)["\']\s*%}')


class UsageStatistics:
    """组件使用统计"""

    def __init__(self, index: ComponentIndex, templates_path: Path) -> None:
        """初始化统计器

        Args:
            index: 组件索引实例
            templates_path: 模板文件根目录
        """
        self.index = index
        self.templates_path = templates_path

    def analyze(self) -> Dict[str, int]:
        """分析所有模板文件，统计组件使用次数

        Returns:
            组件 ID 到使用次数的映射
        """
        # 初始化 usage_count，所有已注册组件初始为 0
        usage_count: Dict[str, int] = {}
        for comp in self.index.list_components():
            usage_count[comp.id] = 0

        # 建立 path -> id 的映射，用于从 include 路径查找组件 ID
        path_to_id: Dict[str, str] = {}
        for comp in self.index.list_components():
            path_to_id[comp.path] = comp.id

        # 遍历所有 .html 文件
        if not self.templates_path.exists():
            return usage_count

        for html_file in self.templates_path.rglob("*.html"):
            # 跳过 components 目录下的文件（组件本身）
            try:
                html_file.relative_to(self.templates_path / "components")
                continue
            except ValueError:
                pass  # 不在 components 目录下，继续处理

            try:
                content = html_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # 查找所有 include 语句
            for match in INCLUDE_PATTERN.finditer(content):
                component_path = match.group(1)
                if component_path in path_to_id:
                    comp_id = path_to_id[component_path]
                    usage_count[comp_id] = usage_count.get(comp_id, 0) + 1

        return usage_count

    def get_unused(self) -> List[str]:
        """获取未使用的组件列表

        Returns:
            未使用的组件 ID 列表
        """
        usage_count = self.analyze()
        return [comp_id for comp_id, count in usage_count.items() if count == 0]
