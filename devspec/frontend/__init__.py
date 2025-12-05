"""
Frontend Component Library
Part of comp_frontend_component_library

提供前端组件库的管理能力，包括组件注册、索引读取、查询、验证、使用统计等功能。
遵循 Spec-First 原则：组件 = MD文档(Truth) + HTML代码(Projection)
"""

from .cli import frontend_app
from .component_index import ComponentIndex, ComponentIndexError
from .component_registrar import ComponentRegistrar, ComponentRegistrarError
from .component_validator import ComponentValidator
from .models import ComponentInfo, ParamInfo, ValidationResult
from .usage_statistics import UsageStatistics

__all__ = [
    "frontend_app",
    "ComponentIndex",
    "ComponentIndexError",
    "ComponentRegistrar",
    "ComponentRegistrarError",
    "ComponentValidator",
    "UsageStatistics",
    "ComponentInfo",
    "ParamInfo",
    "ValidationResult",
]
