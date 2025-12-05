"""
Frontend Component Library - Data Models
Part of comp_frontend_component_library
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParamInfo:
    """组件参数信息"""

    name: str
    type: str
    desc: str


@dataclass
class ValidationResult:
    """验证结果数据类"""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """合并另一个验证结果"""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )

    def add_error(self, msg: str) -> None:
        """添加错误"""
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        """添加警告"""
        self.warnings.append(msg)


@dataclass
class ComponentInfo:
    """组件信息数据类"""

    id: str
    category: str
    name: str
    desc: str
    md_path: str
    html_path: str
    status: str = "registered"  # registered | implemented | verified
    params: List[ParamInfo] = field(default_factory=list)
    example: Optional[str] = None

    @property
    def path(self) -> str:
        """兼容旧代码的 path 属性"""
        return self.html_path
