"""
Frontend Component Library - Component Registrar
Part of comp_frontend_component_library

遵循 Spec-First 原则：组件 = MD文档(Truth) + HTML代码(Projection)
必须先注册（创建 MD 文档）再编码（写 HTML）
"""

from pathlib import Path
from typing import List, Optional

import yaml

from .component_index import INDEX_FILE
from .models import ComponentInfo, ParamInfo


class ComponentRegistrarError(Exception):
    """组件注册错误"""

    pass


class ComponentRegistrar:
    """组件注册器 - 创建新组件的 MD 文档并更新索引"""

    def __init__(self, root_path: Path) -> None:
        """初始化注册器

        Args:
            root_path: 组件库根目录 (templates/components/)
        """
        self.root_path = root_path

    def register(
        self,
        category: str,
        name: str,
        desc: str,
        params: Optional[List[ParamInfo]] = None,
    ) -> Path:
        """注册新组件：创建 MD 文档模板，更新 _index.yaml

        Args:
            category: 组件分类 (如 cards, badges, forms)
            name: 组件名称 (如 domain, status)
            desc: 组件描述
            params: 组件参数列表

        Returns:
            创建的 MD 文档路径

        Raises:
            ComponentRegistrarError: 组件已存在或参数无效
        """
        # 验证参数
        if not category or not category.isalpha():
            raise ComponentRegistrarError(
                f"分类名 '{category}' 无效，必须是纯字母"
            )
        if not name or not name.replace("_", "").isalpha():
            raise ComponentRegistrarError(
                f"组件名 '{name}' 无效，只能包含字母和下划线"
            )

        component_id = f"comp_{category}_{name}"
        md_path = f"{category}/{name}.md"
        html_path = f"{category}/{name}.html"

        # 检查组件是否已存在
        index_file = self.root_path / INDEX_FILE
        existing_components = []
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                existing_components = data.get("components", [])
                for comp in existing_components:
                    if comp.get("id") == component_id:
                        raise ComponentRegistrarError(
                            f"组件 '{component_id}' 已存在"
                        )

        # 创建目录
        category_dir = self.root_path / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # 创建组件信息
        params = params or []
        component = ComponentInfo(
            id=component_id,
            category=category,
            name=name,
            desc=desc,
            md_path=md_path,
            html_path=html_path,
            status="registered",
            params=params,
            example=f'{{% include "components/{category}/{name}.html" with context %}}',
        )

        # 生成并写入 MD 文档
        md_content = self.generate_md_template(component)
        md_file = self.root_path / md_path
        md_file.write_text(md_content, encoding="utf-8")

        # 更新 _index.yaml
        self._update_index(component, existing_components)

        return md_file

    def generate_md_template(self, component: ComponentInfo) -> str:
        """生成组件 MD 文档模板内容

        Args:
            component: 组件信息

        Returns:
            MD 文档内容
        """
        # 生成参数表格
        params_table = "| 名称 | 类型 | 必填 | 描述 |\n|------|------|------|------|\n"
        if component.params:
            for param in component.params:
                params_table += f"| {param.name} | {param.type} | 是 | {param.desc} |\n"
        else:
            params_table += "| (无参数) | - | - | - |\n"

        return f"""# {component.id}

## 描述
{component.desc}

## 参数
{params_table}
## 样式规范
- 使用 Tailwind CSS 类
- 遵循 sub_frontend_style.yaml 定义的调色板
- 主色: blue-600, 次色: gray-600
- (待完善)

## 使用示例
```jinja2
{component.example}
```

## 设计备注
(待填写)
"""

    def _update_index(
        self, component: ComponentInfo, existing_components: List[dict]
    ) -> None:
        """更新 _index.yaml 索引文件

        Args:
            component: 新组件信息
            existing_components: 现有组件列表
        """
        # 构建新组件条目
        new_entry = {
            "id": component.id,
            "category": component.category,
            "name": component.name,
            "desc": component.desc,
            "md_path": component.md_path,
            "html_path": component.html_path,
            "status": component.status,
        }

        if component.params:
            new_entry["params"] = [
                {"name": p.name, "type": p.type, "desc": p.desc}
                for p in component.params
            ]

        if component.example:
            new_entry["example"] = component.example

        # 添加到列表
        existing_components.append(new_entry)

        # 写入文件
        index_file = self.root_path / INDEX_FILE
        index_data = {
            "_comment": "前端组件索引 (自动生成，请勿手动编辑)",
            "_note": "使用 devspec frontend register 添加新组件",
            "components": existing_components,
        }

        with open(index_file, "w", encoding="utf-8") as f:
            yaml.dump(
                index_data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
