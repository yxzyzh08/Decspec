"""
Frontend Component Library - Component Validator
Part of comp_frontend_component_library

验证逻辑：
1. 索引验证：检查 _index.yaml 格式和必填字段
2. 组件验证：
   - 检查 MD 文档是否存在 (Truth)
   - 检查 HTML 文件是否存在 (status != registered)
   - 检查 HTML 中使用的参数是否在 MD 中定义
   - 检查 HTML 中的 CSS 类是否符合 sub_frontend_style.yaml
"""

import re
from pathlib import Path
from typing import List, Set

import yaml

from .component_index import INDEX_FILE, ComponentIndex
from .models import ComponentInfo, ValidationResult

# 组件 ID 命名规范: comp_{category}_{name}
COMPONENT_ID_PATTERN = re.compile(r"^comp_[a-z]+_[a-z_]+$")

# Jinja2 变量提取正则：{{ variable }} 或 {{ variable.attr }}
JINJA2_VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)")

# HTML class 属性提取正则
HTML_CLASS_PATTERN = re.compile(r'class\s*=\s*["\']([^"\']+)["\']')

# sub_frontend_style.yaml 允许的颜色和前缀
ALLOWED_COLOR_NAMES = {
    "blue", "gray", "green", "yellow", "red", "white",
    "primary", "secondary", "success", "warning", "error"
}
CUSTOM_CLASS_PREFIX = "ds-"


class ComponentValidator:
    """组件验证器"""

    def __init__(self, index: ComponentIndex, root_path: Path) -> None:
        """初始化验证器

        Args:
            index: 组件索引实例
            root_path: 组件库根目录
        """
        self.index = index
        self.root_path = root_path

    def validate_index(self) -> ValidationResult:
        """验证索引文件格式是否正确

        Returns:
            验证结果，包含错误和警告列表
        """
        result = ValidationResult()
        index_file = self.root_path / INDEX_FILE

        # 检查索引文件是否存在
        if not index_file.exists():
            result.add_warning(f"索引文件不存在: {index_file}")
            return result

        # 检查组件列表
        components = self.index.list_components()
        if not components:
            result.add_warning("组件索引为空")
            return result

        # 检查每个组件的必填字段和命名规范
        for comp in components:
            # 检查必填字段
            if not comp.id:
                result.add_error("组件缺少 id 字段")
            if not comp.path:
                result.add_error(f"组件 {comp.id} 缺少 path 字段")
            if not comp.desc:
                result.add_warning(f"组件 {comp.id} 缺少 desc 字段")

            # 检查 ID 命名规范
            if comp.id and not COMPONENT_ID_PATTERN.match(comp.id):
                result.add_warning(
                    f"组件 ID '{comp.id}' 不符合命名规范 (comp_{{category}}_{{name}})"
                )

        return result

    def validate_component(self, component_id: str) -> ValidationResult:
        """验证单个组件是否符合规范

        Args:
            component_id: 组件 ID

        Returns:
            验证结果
        """
        result = ValidationResult()

        comp = self.index.get_component(component_id)
        if not comp:
            result.add_error(f"组件 '{component_id}' 不存在于索引中")
            return result

        # 1. 检查 MD 文档是否存在 (Truth)
        # 兼容旧格式：如果 md_path 为空，从 html_path 推导
        md_path = comp.md_path
        if not md_path and comp.html_path:
            md_path = comp.html_path.replace(".html", ".md")

        if not md_path:
            result.add_warning(f"组件 '{comp.id}' 缺少 md_path 定义")
            return result

        md_file = self.root_path / md_path
        if not md_file.exists():
            # 对于旧格式组件，MD 不存在是警告而非错误
            if not comp.md_path:
                result.add_warning(
                    f"旧格式组件 '{comp.id}' 缺少 MD 文档，建议重新注册"
                )
            else:
                result.add_error(f"MD 文档不存在 (Truth 缺失): {md_file}")
            return result

        # 2. 检查文件命名是否符合 snake_case
        filename = Path(md_path).stem
        if not re.match(r"^[a-z][a-z0-9_]*$", filename):
            result.add_warning(f"组件文件名 '{filename}' 不符合 snake_case 规范")

        # 3. 如果 status != registered，检查 HTML 是否存在
        html_file = self.root_path / comp.html_path
        if comp.status != "registered":
            if not html_file.exists():
                result.add_warning(
                    f"组件状态为 '{comp.status}'，但 HTML 文件不存在: {html_file}"
                )
        else:
            # registered 状态不需要 HTML，跳过 HTML 相关检查
            return result

        # 4. 如果 HTML 存在，进行 MD-HTML 一致性检查
        if html_file.exists():
            html_result = self._validate_html_consistency(comp, md_file, html_file)
            result = result.merge(html_result)

        return result

    def _validate_html_consistency(
        self, comp: ComponentInfo, md_file: Path, html_file: Path
    ) -> ValidationResult:
        """验证 HTML 与 MD 的一致性

        检查内容：
        1. HTML 中使用的参数是否在 MD 中定义
        2. HTML 中的 CSS 类是否符合 sub_frontend_style.yaml

        Args:
            comp: 组件信息
            md_file: MD 文档路径
            html_file: HTML 文件路径

        Returns:
            验证结果
        """
        result = ValidationResult()

        # 读取 HTML 内容
        html_content = html_file.read_text(encoding="utf-8")

        # 读取 MD 内容，提取参数定义
        md_content = md_file.read_text(encoding="utf-8")
        md_params = self._extract_params_from_md(md_content)

        # 从索引获取参数（如果 MD 解析失败则使用索引）
        index_params = {p.name for p in comp.params}
        defined_params = md_params if md_params else index_params

        # 1. 检查 HTML 中使用的参数是否在 MD 中定义
        html_variables = self._extract_variables_from_html(html_content)
        # 过滤掉 Jinja2 内置变量和循环变量
        builtin_vars = {"loop", "range", "true", "false", "none", "self"}
        html_variables = html_variables - builtin_vars

        undefined_vars = html_variables - defined_params
        if undefined_vars:
            for var in undefined_vars:
                result.add_warning(
                    f"[{comp.id}] HTML 使用了未在 MD 中定义的参数: '{var}'"
                )

        # 2. 检查 HTML 中的 CSS 类是否符合 sub_frontend_style.yaml
        css_result = self._validate_css_classes(comp.id, html_content)
        result = result.merge(css_result)

        return result

    def _extract_params_from_md(self, md_content: str) -> Set[str]:
        """从 MD 文档中提取参数名

        Args:
            md_content: MD 文档内容

        Returns:
            参数名集合
        """
        params = set()

        # 查找参数表格部分
        # 格式: | 名称 | 类型 | 必填 | 描述 |
        lines = md_content.split("\n")
        in_params_section = False

        for line in lines:
            if "## 参数" in line:
                in_params_section = True
                continue

            if in_params_section:
                # 遇到下一个章节则停止
                if line.startswith("## "):
                    break

                # 解析表格行
                if line.startswith("|") and "---" not in line and "名称" not in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2 and parts[1]:
                        param_name = parts[1]
                        if param_name and param_name != "(无参数)":
                            params.add(param_name)

        return params

    def _extract_variables_from_html(self, html_content: str) -> Set[str]:
        """从 HTML 模板中提取 Jinja2 变量名

        Args:
            html_content: HTML 内容

        Returns:
            变量名集合
        """
        return set(JINJA2_VARIABLE_PATTERN.findall(html_content))

    def _validate_css_classes(
        self, component_id: str, html_content: str
    ) -> ValidationResult:
        """验证 HTML 中的 CSS 类是否符合规范

        规范来源: sub_frontend_style.yaml
        - 使用 Tailwind CSS 类
        - 自定义类必须使用 ds- 前缀
        - 颜色类必须使用规范定义的颜色

        Args:
            component_id: 组件 ID
            html_content: HTML 内容

        Returns:
            验证结果
        """
        result = ValidationResult()

        # 提取所有 class 属性值
        class_matches = HTML_CLASS_PATTERN.findall(html_content)
        all_classes: Set[str] = set()
        for match in class_matches:
            all_classes.update(match.split())

        for css_class in all_classes:
            # 跳过 Tailwind 标准类（常见模式）
            if self._is_tailwind_class(css_class):
                # 检查颜色类是否使用规范颜色
                color_warning = self._check_color_compliance(css_class)
                if color_warning:
                    result.add_warning(f"[{component_id}] {color_warning}")
                continue

            # 检查自定义类是否使用 ds- 前缀
            if not css_class.startswith(CUSTOM_CLASS_PREFIX):
                # 可能是不规范的自定义类
                result.add_warning(
                    f"[{component_id}] 自定义 CSS 类 '{css_class}' 应使用 '{CUSTOM_CLASS_PREFIX}' 前缀"
                )

        return result

    def _is_tailwind_class(self, css_class: str) -> bool:
        """判断是否为 Tailwind CSS 类

        Args:
            css_class: CSS 类名

        Returns:
            是否为 Tailwind 类
        """
        # Tailwind 类的常见前缀
        tailwind_prefixes = (
            "p-", "m-", "px-", "py-", "mx-", "my-", "pt-", "pb-", "pl-", "pr-",
            "mt-", "mb-", "ml-", "mr-",
            "w-", "h-", "min-w-", "min-h-", "max-w-", "max-h-",
            "text-", "font-", "leading-", "tracking-",
            "bg-", "border-", "rounded-", "shadow-",
            "flex", "grid", "block", "inline", "hidden",
            "items-", "justify-", "gap-", "space-",
            "absolute", "relative", "fixed", "sticky",
            "top-", "bottom-", "left-", "right-",
            "z-", "overflow-", "cursor-",
            "opacity-", "transition", "duration-", "ease-",
            "hover:", "focus:", "active:", "disabled:",
            "sm:", "md:", "lg:", "xl:", "2xl:",
            "dark:",
        )

        return any(css_class.startswith(prefix) for prefix in tailwind_prefixes)

    def _check_color_compliance(self, css_class: str) -> str:
        """检查颜色类是否使用规范颜色

        Args:
            css_class: CSS 类名

        Returns:
            警告信息，如果合规则返回空字符串
        """
        # 提取颜色名（如 bg-red-500 中的 red）
        color_patterns = [
            (r"^(?:text|bg|border)-([a-z]+)-\d+$", "颜色"),
        ]

        for pattern, color_type in color_patterns:
            match = re.match(pattern, css_class)
            if match:
                color_name = match.group(1)
                if color_name not in ALLOWED_COLOR_NAMES:
                    return (
                        f"CSS 类 '{css_class}' 使用了非规范{color_type} '{color_name}'，"
                        f"建议使用: {', '.join(sorted(ALLOWED_COLOR_NAMES))}"
                    )

        return ""

    def validate_all(self) -> ValidationResult:
        """验证所有组件

        Returns:
            汇总验证结果
        """
        result = self.validate_index()

        for comp in self.index.list_components():
            comp_result = self.validate_component(comp.id)
            result = result.merge(comp_result)

        return result
