"""
YAML Schema Validator - Validates YAML files against sub_meta_schema.yaml definitions.

This module provides validation for all SpecGraph YAML files (Product, Feature,
Component, Design, Substrate) to ensure they conform to the schema definitions.

Component: comp_yaml_schema_validator
Feature: feat_consistency_monitor
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml


# =============================================================================
# Constants
# =============================================================================

EXCLUDED_FILES = ["sub_meta_schema.yaml"]
EXCLUDED_DIRS = [".runtime", "__pycache__"]

NODE_TYPE_PREFIXES = {
    "prod_": "product",
    "feat_": "feature",
    "comp_": "component",
    "des_": "design",
    "sub_": "substrate",
}

REQUIRED_FIELDS = {
    "product": ["id", "name", "version", "description", "domains"],
    "feature": ["id", "domain", "source_anchor", "intent"],
    "component": ["id", "type", "desc", "file_path", "design"],
    "design": ["id", "type", "name", "intent"],
    "substrate": ["id", "type", "name"],
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ValidationError:
    """验证错误信息."""

    file_path: str
    field: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    """单个文件的验证结果."""

    file_path: str
    node_type: str
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)


@dataclass
class SchemaValidationReport:
    """完整验证报告."""

    total_files: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    warning_count: int = 0
    results: List[ValidationResult] = field(default_factory=list)


# =============================================================================
# YAML Schema Validator
# =============================================================================

class YAMLSchemaValidator:
    """YAML Schema 验证器."""

    def __init__(self, spec_dir: Path) -> None:
        """
        初始化验证器.

        Args:
            spec_dir: .specgraph 目录路径
        """
        self.spec_dir = Path(spec_dir)
        self.valid_domains: List[str] = []
        self._load_valid_domains()

    def _load_valid_domains(self) -> None:
        """加载 product.yaml 中的有效 domain ID 列表."""
        product_path = self.spec_dir / "product.yaml"
        if product_path.exists():
            try:
                content = product_path.read_text(encoding="utf-8")
                data = yaml.safe_load(content)
                if isinstance(data, dict) and "domains" in data:
                    for domain in data.get("domains", []):
                        if isinstance(domain, dict) and "id" in domain:
                            self.valid_domains.append(domain["id"])
            except Exception:
                pass

    def validate_all(self) -> SchemaValidationReport:
        """
        验证所有 YAML 文件.

        Returns:
            SchemaValidationReport: 完整验证报告
        """
        report = SchemaValidationReport()
        yaml_files = self._get_yaml_files()

        for file_path in yaml_files:
            result = self.validate_file(file_path)
            report.results.append(result)
            report.total_files += 1

            if result.is_valid:
                report.valid_count += 1
            else:
                report.invalid_count += 1

            if result.warnings:
                report.warning_count += 1

        return report

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        验证单个 YAML 文件.

        Args:
            file_path: YAML 文件路径

        Returns:
            ValidationResult: 验证结果
        """
        rel_path = str(file_path.relative_to(self.spec_dir.parent))

        try:
            content = file_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)

            if not isinstance(data, dict):
                return ValidationResult(
                    file_path=rel_path,
                    node_type="unknown",
                    is_valid=False,
                    errors=[
                        ValidationError(
                            file_path=rel_path,
                            field="",
                            message="YAML content is not a dictionary",
                        )
                    ],
                )

            node_type = self._detect_node_type(file_path, data)

            if node_type == "unknown":
                return ValidationResult(
                    file_path=rel_path,
                    node_type="unknown",
                    is_valid=False,
                    errors=[
                        ValidationError(
                            file_path=rel_path,
                            field="id",
                            message="Cannot determine node type from ID prefix or file path",
                        )
                    ],
                )

            # 根据类型调用对应的验证方法
            if node_type == "product":
                return self._validate_product(data, rel_path)
            elif node_type == "feature":
                return self._validate_feature(data, rel_path)
            elif node_type == "component":
                return self._validate_component(data, rel_path)
            elif node_type == "design":
                return self._validate_design(data, rel_path)
            elif node_type == "substrate":
                return self._validate_substrate(data, rel_path)
            else:
                return ValidationResult(
                    file_path=rel_path,
                    node_type=node_type,
                    is_valid=True,
                )

        except yaml.YAMLError as e:
            return ValidationResult(
                file_path=rel_path,
                node_type="unknown",
                is_valid=False,
                errors=[
                    ValidationError(
                        file_path=rel_path,
                        field="",
                        message=f"YAML parse error: {e}",
                    )
                ],
            )
        except Exception as e:
            return ValidationResult(
                file_path=rel_path,
                node_type="unknown",
                is_valid=False,
                errors=[
                    ValidationError(
                        file_path=rel_path,
                        field="",
                        message=f"Error reading file: {e}",
                    )
                ],
            )

    def _get_yaml_files(self) -> List[Path]:
        """获取所有需要验证的 YAML 文件."""
        yaml_files = []
        for file_path in self.spec_dir.rglob("*.yaml"):
            # 检查是否在排除目录中
            skip = False
            for skip_dir in EXCLUDED_DIRS:
                if skip_dir in file_path.parts:
                    skip = True
                    break

            # 检查是否是排除文件
            if file_path.name in EXCLUDED_FILES:
                skip = True

            if not skip:
                yaml_files.append(file_path)

        return yaml_files

    def _detect_node_type(self, file_path: Path, data: Dict[str, Any]) -> str:
        """
        检测节点类型.

        优先从 ID 前缀判断，其次从文件路径判断.
        """
        # 从 ID 前缀判断
        node_id = data.get("id", "")
        if isinstance(node_id, str):
            for prefix, node_type in NODE_TYPE_PREFIXES.items():
                if node_id.startswith(prefix):
                    return node_type

        # 从文件路径判断
        path_str = str(file_path)
        if "features" in path_str or "/features/" in path_str or "\\features\\" in path_str:
            return "feature"
        elif "components" in path_str or "/components/" in path_str or "\\components\\" in path_str:
            return "component"
        elif "design" in path_str or "/design/" in path_str or "\\design\\" in path_str:
            return "design"
        elif "substrate" in path_str or "/substrate/" in path_str or "\\substrate\\" in path_str:
            return "substrate"
        elif file_path.name == "product.yaml":
            return "product"

        return "unknown"

    def _validate_product(self, data: Dict[str, Any], file_path: str) -> ValidationResult:
        """验证 Product YAML."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # 检查必填字段
        for field_name in REQUIRED_FIELDS["product"]:
            if field_name not in data:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field=field_name,
                        message=f"Missing required field: {field_name}",
                    )
                )

        # 检查 id 格式
        node_id = data.get("id", "")
        if node_id and not node_id.startswith("prod_"):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="id",
                    message=f"Product ID must start with 'prod_', got: {node_id}",
                )
            )

        # 检查 domains 结构
        domains = data.get("domains", [])
        if not isinstance(domains, list):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="domains",
                    message="domains must be a list",
                )
            )
        else:
            for i, domain in enumerate(domains):
                if not isinstance(domain, dict):
                    errors.append(
                        ValidationError(
                            file_path=file_path,
                            field=f"domains[{i}]",
                            message="Each domain must be a dictionary",
                        )
                    )
                else:
                    for req_field in ["id", "name", "description"]:
                        if req_field not in domain:
                            errors.append(
                                ValidationError(
                                    file_path=file_path,
                                    field=f"domains[{i}].{req_field}",
                                    message=f"Domain missing required field: {req_field}",
                                )
                            )

        return ValidationResult(
            file_path=file_path,
            node_type="product",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_feature(self, data: Dict[str, Any], file_path: str) -> ValidationResult:
        """验证 Feature YAML."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # 检查必填字段
        for field_name in REQUIRED_FIELDS["feature"]:
            if field_name not in data:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field=field_name,
                        message=f"Missing required field: {field_name}",
                    )
                )

        # 检查 id 格式
        node_id = data.get("id", "")
        if node_id and not node_id.startswith("feat_"):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="id",
                    message=f"Feature ID must start with 'feat_', got: {node_id}",
                )
            )

        # 检查 domain 引用
        domain = data.get("domain", "")
        if domain and self.valid_domains and domain not in self.valid_domains:
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="domain",
                    message=f"Domain '{domain}' not found in product.yaml. Valid domains: {self.valid_domains}",
                )
            )

        # 检查 source_anchor 格式
        source_anchor = data.get("source_anchor", "")
        if source_anchor and not source_anchor.startswith("PRD.md#"):
            warnings.append(
                ValidationError(
                    file_path=file_path,
                    field="source_anchor",
                    message=f"source_anchor should start with 'PRD.md#', got: {source_anchor}",
                    severity="warning",
                )
            )

        # 警告: realized_by 为空
        realized_by = data.get("realized_by", [])
        if not realized_by:
            warnings.append(
                ValidationError(
                    file_path=file_path,
                    field="realized_by",
                    message="No components assigned (realized_by is empty)",
                    severity="warning",
                )
            )

        return ValidationResult(
            file_path=file_path,
            node_type="feature",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_component(self, data: Dict[str, Any], file_path: str) -> ValidationResult:
        """验证 Component YAML."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # 检查必填字段
        for field_name in REQUIRED_FIELDS["component"]:
            if field_name not in data:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field=field_name,
                        message=f"Missing required field: {field_name}",
                    )
                )

        # 检查 id 格式
        node_id = data.get("id", "")
        if node_id and not node_id.startswith("comp_"):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="id",
                    message=f"Component ID must start with 'comp_', got: {node_id}",
                )
            )

        # 检查 type 值
        type_value = data.get("type", "")
        if type_value and type_value != "module":
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="type",
                    message=f"Component type must be 'module', got: {type_value}",
                )
            )

        # 检查 design 结构
        design = data.get("design", {})
        if not isinstance(design, dict):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="design",
                    message="design must be a dictionary",
                )
            )
        else:
            if "api" not in design:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field="design.api",
                        message="design must contain 'api' field",
                    )
                )
            if "logic" not in design:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field="design.logic",
                        message="design must contain 'logic' field",
                    )
                )

        # 警告: file_path 指向的文件不存在
        code_path = data.get("file_path", "")
        if code_path:
            # 相对于项目根目录
            full_path = self.spec_dir.parent / code_path
            if not full_path.exists() and not code_path.endswith("/"):
                warnings.append(
                    ValidationError(
                        file_path=file_path,
                        field="file_path",
                        message=f"Code file does not exist: {code_path}",
                        severity="warning",
                    )
                )

        return ValidationResult(
            file_path=file_path,
            node_type="component",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_design(self, data: Dict[str, Any], file_path: str) -> ValidationResult:
        """验证 Design YAML."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # 检查必填字段
        for field_name in REQUIRED_FIELDS["design"]:
            if field_name not in data:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field=field_name,
                        message=f"Missing required field: {field_name}",
                    )
                )

        # 检查 id 格式
        node_id = data.get("id", "")
        if node_id and not node_id.startswith("des_"):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="id",
                    message=f"Design ID must start with 'des_', got: {node_id}",
                )
            )

        # 检查 type 值
        type_value = data.get("type", "")
        if type_value and type_value != "design":
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="type",
                    message=f"Design type must be 'design', got: {type_value}",
                )
            )

        return ValidationResult(
            file_path=file_path,
            node_type="design",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_substrate(self, data: Dict[str, Any], file_path: str) -> ValidationResult:
        """验证 Substrate YAML."""
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # 检查必填字段
        for field_name in REQUIRED_FIELDS["substrate"]:
            if field_name not in data:
                errors.append(
                    ValidationError(
                        file_path=file_path,
                        field=field_name,
                        message=f"Missing required field: {field_name}",
                    )
                )

        # 检查 id 格式
        node_id = data.get("id", "")
        if node_id and not node_id.startswith("sub_"):
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="id",
                    message=f"Substrate ID must start with 'sub_', got: {node_id}",
                )
            )

        # 检查 type 值
        type_value = data.get("type", "")
        if type_value and type_value != "substrate":
            errors.append(
                ValidationError(
                    file_path=file_path,
                    field="type",
                    message=f"Substrate type must be 'substrate', got: {type_value}",
                )
            )

        return ValidationResult(
            file_path=file_path,
            node_type="substrate",
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
