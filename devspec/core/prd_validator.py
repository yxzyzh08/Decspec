"""
PRD Format Validator.

Component: comp_prd_validator
Feature: feat_quality_prd_validator

PRD 格式校验核心逻辑，检查章节结构、锚点格式、命名规范。
基于 des_prompt_prd_writer.md 定义的规则。
"""
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """校验结果数据类。"""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PRDValidator:
    """PRD 格式校验器。"""

    # 锚点匹配正则
    ANCHOR_PATTERN = re.compile(r"<!--\s*id:\s*(\w+)\s*-->")

    # 有效的锚点前缀
    VALID_PREFIXES = ("prod_", "des_", "dom_", "feat_", "comp_", "sub_")

    # 必需章节
    MANDATORY_SECTIONS = ("Product Vision", "Design Principles", "Domain:")

    def __init__(self, prd_path: Path) -> None:
        """初始化 PRDValidator。

        Args:
            prd_path: PRD.md 文件路径
        """
        self.prd_path = prd_path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.content: str = ""
        self.lines: list[str] = []

    def validate(self) -> ValidationResult:
        """执行完整的 PRD 格式校验。

        Returns:
            ValidationResult: 校验结果，包含错误和警告列表
        """
        # 重置状态
        self.errors = []
        self.warnings = []

        # 读取文件
        if not self.prd_path.exists():
            return ValidationResult(
                is_valid=False, errors=["PRD.md not found"], warnings=[]
            )

        try:
            self.content = self.prd_path.read_text(encoding="utf-8")
            self.lines = self.content.splitlines()
        except UnicodeDecodeError:
            return ValidationResult(
                is_valid=False,
                errors=["Failed to read PRD.md: encoding error"],
                warnings=[],
            )

        # 执行各项检查
        self._check_mandatory_sections()
        self._check_anchor_format()
        self._check_anchor_naming()
        self._check_heading_hierarchy()

        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
        )

    def _check_mandatory_sections(self) -> None:
        """检查必需章节是否存在。"""
        for section in self.MANDATORY_SECTIONS:
            if section not in self.content:
                self.errors.append(f"Missing mandatory section: {section}")

    def _check_anchor_format(self) -> None:
        """检查锚点格式是否正确。"""
        for line_num, line in enumerate(self.lines, start=1):
            # 只检查行末尾的锚点（真正的锚点定义）
            # 忽略代码块、示例文本中的锚点格式说明
            stripped = line.strip()

            # 跳过代码块内容和格式说明
            if stripped.startswith("`") or ": `" in line:
                continue

            # 检查是否有锚点模式（在行末尾）
            if stripped.endswith("-->"):
                match = self.ANCHOR_PATTERN.search(line)
                if not match:
                    self.errors.append(
                        f"Invalid anchor format at line {line_num}: {stripped}"
                    )
                    continue

                # 检查锚点是否在标题行或列表项
                if not stripped.startswith("#") and not stripped.startswith("*"):
                    self.warnings.append(
                        f"Anchor at line {line_num} is not on a heading or list item"
                    )

    def _check_anchor_naming(self) -> None:
        """检查锚点命名是否符合规范。"""
        anchors = self.ANCHOR_PATTERN.findall(self.content)

        for anchor in anchors:
            # 检查是否使用有效前缀
            if not anchor.startswith(self.VALID_PREFIXES):
                self.warnings.append(
                    f"Anchor '{anchor}' does not use a valid prefix "
                    f"(expected: {', '.join(self.VALID_PREFIXES)})"
                )
                continue

            # 检查是否使用 snake_case
            if not re.match(r"^[a-z][a-z0-9_]*$", anchor):
                self.warnings.append(
                    f"Anchor '{anchor}' is not in snake_case format"
                )

    def _check_heading_hierarchy(self) -> None:
        """检查标题层级是否正确。"""
        h1_count = 0

        for line_num, line in enumerate(self.lines, start=1):
            stripped = line.strip()

            # 统计 H1
            if stripped.startswith("# ") and not stripped.startswith("## "):
                h1_count += 1
                if h1_count > 1:
                    self.warnings.append(
                        f"Multiple H1 headings found at line {line_num}"
                    )

            # 检查 Domain 是否是 H2
            if "Domain:" in stripped and stripped.startswith("#"):
                if not stripped.startswith("## "):
                    self.warnings.append(
                        f"Domain at line {line_num} should be H2 (##)"
                    )

            # 检查 Feature 是否是 H3
            if "Feature:" in stripped and stripped.startswith("#"):
                if not stripped.startswith("### "):
                    self.warnings.append(
                        f"Feature at line {line_num} should be H3 (###)"
                    )
