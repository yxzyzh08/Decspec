"""
DevSpec Context Builder - Prompt 构建模块。

负责根据 Feature 构建完整的 AI Context Prompt。
"""

from pathlib import Path
from typing import Any

import yaml

from devspec.engine.loader import get_spec_paths, load_yaml, scan_directory


def build_related_context(feature_data: dict[str, Any], paths: dict[str, Path]) -> str:
    """
    构建相关组件的上下文信息。

    Args:
        feature_data: Feature 的 YAML 数据
        paths: SpecGraph 路径映射

    Returns:
        相关组件的文本描述
    """
    related_context = ""

    if "realized_by" in feature_data:
        related_context += "\n## Related Components (Implementation)\n"
        for comp_id in feature_data["realized_by"]:
            comp_path = paths["components"] / f"{comp_id}.yaml"
            if comp_path.exists():
                comp_data = load_yaml(comp_path)
                related_context += f"- {comp_id}: {comp_data.get('intent', 'No summary')}\n"

    return related_context


def build_prompt(
    product_data: dict[str, Any],
    design_text: str,
    substrate_text: str,
    feature_data: dict[str, Any],
    related_context: str,
) -> str:
    """
    组装完整的 AI Context Prompt。

    Args:
        product_data: Product 定义数据
        design_text: Design 文档内容
        substrate_text: Substrate 规范内容
        feature_data: 当前 Feature 数据
        related_context: 相关组件上下文

    Returns:
        完整的 Prompt 文本
    """
    info = product_data.get("info", {})
    meta = product_data.get("meta", {})
    feature_meta = feature_data.get("meta", {})
    intent = feature_data.get("intent", {})
    contract = feature_data.get("contract", {})
    workflow = feature_data.get("workflow", [])

    prompt = f"""
# ROLE definition
You are the AI Engine for a self-bootstrapping system called "{info.get('name')}".
We are currently in Phase 0 (Manual Bootstrapping).
Your goal is to write production-ready Python code based on the specs provided below.

# 1. GLOBAL CONTEXT (The Product)
Name: {info.get('name')} (v{meta.get('version')})
Vision: {info.get('vision')}
Domains:
{yaml.dump(product_data.get('domains', []), allow_unicode=True)}

# 2. DESIGN PHILOSOPHY (The "Why")
{design_text}

# 3. TECH STACK & RULES (The "How" / Substrate)
{substrate_text}

# 4. CURRENT TASK (The Feature)
ID: {feature_meta.get('id')}
Summary: {intent.get('summary')}
User Story: {intent.get('user_story')}

## Contract (I/O)
Input: {contract.get('input')}
Output: {contract.get('output')}

## Workflow (Logic)
{yaml.dump(workflow, allow_unicode=True)}
{related_context}

# 5. INSTRUCTION
Based on the above, please write/update the code.
- Follow the Tech Stack strictly (Typer, Pathlib, Pydantic).
- Keep code modular.
- If the feature requires creating new files, please verify the paths against `.specgraph` structure.
"""
    return prompt


def generate_context(root_dir: Path, feature_id: str) -> tuple[str, dict[str, Any]]:
    """
    为指定 Feature 生成完整的 AI Context。

    Args:
        root_dir: 项目根目录
        feature_id: Feature 的 ID

    Returns:
        (prompt, feature_data) 元组

    Raises:
        FileNotFoundError: 当 Feature 文件不存在时
    """
    paths = get_spec_paths(root_dir)

    # 加载全局视图
    product_data = load_yaml(paths["product"])
    design_text = scan_directory(paths["design"])
    substrate_text = scan_directory(paths["substrate"])

    # 处理 .yaml 后缀
    fname = feature_id if feature_id.endswith(".yaml") else f"{feature_id}.yaml"
    
    # 递归查找 Feature 文件
    found_files = list(paths["features"].rglob(fname))
    
    if not found_files:
        available = []
        if paths["features"].exists():
            available = [f.stem for f in paths["features"].rglob("*.yaml")]
        raise FileNotFoundError(
            f"Feature file not found: {fname} in {paths['features']}\n"
            f"Available features: {', '.join(available)}"
        )
    
    feature_path = found_files[0]

    feature_data = load_yaml(feature_path)
    related_context = build_related_context(feature_data, paths)

    prompt = build_prompt(
        product_data=product_data,
        design_text=design_text,
        substrate_text=substrate_text,
        feature_data=feature_data,
        related_context=related_context,
    )

    return prompt, feature_data
