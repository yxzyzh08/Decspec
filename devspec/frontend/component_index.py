"""
Frontend Component Library - Component Index
Part of comp_frontend_component_library
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import ComponentInfo, ParamInfo

INDEX_FILE = "_index.yaml"


class ComponentIndexError(Exception):
    """组件索引错误"""

    pass


class ComponentIndex:
    """组件索引管理类"""

    def __init__(self, root_path: Path) -> None:
        """初始化组件索引，加载 _index.yaml

        Args:
            root_path: 组件库根目录 (templates/components/)
        """
        self.root_path = root_path
        self.components: Dict[str, ComponentInfo] = {}
        self.load()

    def load(self) -> None:
        """加载或重新加载组件索引"""
        index_file = self.root_path / INDEX_FILE

        if not index_file.exists():
            self.components = {}
            return

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ComponentIndexError(f"索引文件 YAML 格式错误: {e}")

        if not data or "components" not in data:
            self.components = {}
            return

        self.components = {}
        for item in data.get("components", []):
            params = []
            for p in item.get("params", []):
                params.append(
                    ParamInfo(
                        name=p.get("name", ""),
                        type=p.get("type", ""),
                        desc=p.get("desc", ""),
                    )
                )

            comp = ComponentInfo(
                id=item.get("id", ""),
                category=item.get("category", ""),
                name=item.get("name", ""),
                desc=item.get("desc", ""),
                md_path=item.get("md_path", ""),
                html_path=item.get("html_path", item.get("path", "")),
                status=item.get("status", "registered"),
                params=params,
                example=item.get("example"),
            )
            self.components[comp.id] = comp

    def list_components(self) -> List[ComponentInfo]:
        """列出所有已注册的组件

        Returns:
            组件信息列表
        """
        return list(self.components.values())

    def get_component(self, component_id: str) -> Optional[ComponentInfo]:
        """根据 ID 获取组件信息

        Args:
            component_id: 组件 ID

        Returns:
            组件信息，不存在则返回 None
        """
        return self.components.get(component_id)

    def search(self, keyword: str) -> List[ComponentInfo]:
        """按关键词搜索组件 (搜索 id, desc, params)

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的组件列表
        """
        keyword_lower = keyword.lower()
        results = []

        for comp in self.components.values():
            # 搜索 id
            if keyword_lower in comp.id.lower():
                results.append(comp)
                continue

            # 搜索 desc
            if keyword_lower in comp.desc.lower():
                results.append(comp)
                continue

            # 搜索 params
            for param in comp.params:
                if (
                    keyword_lower in param.name.lower()
                    or keyword_lower in param.desc.lower()
                ):
                    results.append(comp)
                    break

        return results
