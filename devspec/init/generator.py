"""
文件生成器。

生成 product.yaml、AGENT.md、CLAUDE.md/GEMINI.md 等文件。
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devspec.init.collector import ProjectInfo


def generate_product_yaml(info: "ProjectInfo") -> str:
    """
    生成 product.yaml 内容。

    Args:
        info: 项目信息

    Returns:
        str: YAML 文件内容
    """
    # 构建 domains 列表
    domains_yaml = ""
    for domain in info.domains:
        domain_id = f"dom_{domain}" if not domain.startswith("dom_") else domain
        domain_name = domain.replace("dom_", "").title()
        domains_yaml += (
            f'\n  - id: "{domain_id}"'
            f'\n    name: "{domain_name}"'
            f'\n    description: "{domain_name} domain."'
        )

    return f"""\
meta:
  id: "product_root"
  type: "Product"
  version: "0.1.0"
  status: "BOOTSTRAPPING"

info:
  name: "{info.name}"
  vision: "{info.vision}"

domains:{domains_yaml}
"""


def generate_agent_md(info: "ProjectInfo") -> str:
    """
    生成 AGENT.md 内容（完整的 AI 协议指南）。

    Args:
        info: 项目信息

    Returns:
        str: Markdown 文件内容
    """
    # 构建域列表
    domains_list = ""
    for domain in info.domains:
        domain_id = f"dom_{domain}" if not domain.startswith("dom_") else domain
        domain_name = domain.replace("dom_", "").title()
        domains_list += f"- **{domain_id}**: {domain_name} domain\n"

    return f"""\
# {info.name} - AI Agent Protocol

> **Identity**: You are the AI assistant for **{info.name}**.
> **Mission**: {info.vision}

---

## 1. Core Directives

1. **Read Before Write**:
   Before writing any code, read the relevant definitions in `.specgraph/`.
   **Code is the projection of Spec, Spec is the truth of code.**

2. **Ouroboros Loop**:
   If you create a new source file, you **MUST** create a corresponding Component YAML in `.specgraph/components/`.

3. **Tech Stack**:
   - Python 3.10+ (Type Hints Required)
   - **CLI**: `typer` + `rich`
   - **Data**: `pydantic` v2 + `sqlmodel` + `pyyaml`
   - **Path**: `pathlib.Path` (**NO `os.path`**)
   - **Env**: `uv`

---

## 2. The SpecGraph Map

All project knowledge is stored in `.specgraph/`. When assigned a task, retrieve context in this order:

1. **Global View**: `.specgraph/product.yaml` (project overview)
2. **Design Philosophy**: `.specgraph/design/*.yaml` (architecture principles)
3. **Coding Rules**: `.specgraph/substrate/*.yaml` (coding standards)
4. **The Task**: `.specgraph/features/{{feature_id}}.yaml` (task intent & workflow)
5. **Existing Tools**: `.specgraph/components/*.yaml` (existing components)

### Project Domains

{domains_list}

---

## 3. Workflow Protocol

### 🟢 Phase 1: Analyze
- If Feature is defined: Read the YAML, understand `intent`, `contract`, `workflow`.
- If Feature is not defined: Suggest creating a Feature YAML first.

### 🟡 Phase 2: Coding
- **Module Granularity**: One Component can contain multiple related `.py` files.
- **File Size**: Keep single files < 500 lines.
- **Documentation**: All public functions must have docstrings.

### 🔴 Phase 3: Register (CRITICAL)
After creating new code files:
1. **Create Component definition** in `.specgraph/components/`
2. **Create DataModel definition** if new models were added in `.specgraph/datamodels/`
3. **Update Feature** `realized_by` field

---

## 4. Available Commands

```bash
# Generate AI context prompt for a feature
devspec generate {{feature_id}}

# Sync YAML specs to SQLite database
devspec sync

# View project structure (if implemented)
devspec tree
```

---

## 5. Directory Structure

```
.specgraph/
├── product.yaml       # Product root definition
├── AGENT.md           # This file - AI protocol guide
├── design/            # Architecture & design philosophy
├── substrate/         # Global rules & standards
├── features/          # Feature specifications
├── apis/              # API contracts
├── components/        # Component specifications
├── datamodels/        # Data model definitions
└── .runtime/          # Runtime cache (git-ignored)
    └── index.db       # SQLite database
```
"""


def generate_cli_md(info: "ProjectInfo") -> str:
    """
    生成 CLAUDE.md 或 GEMINI.md 内容（简短指引）。

    Args:
        info: 项目信息

    Returns:
        str: Markdown 文件内容
    """
    return f"""\
<!-- DEVSPEC:START -->
# DevSpec Instructions

These instructions are for AI assistants working in this project.

**Project**: {info.name}
**Vision**: {info.vision}

Always open `@/.specgraph/AGENT.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/.specgraph/AGENT.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'devspec update' can refresh the instructions.

<!-- DEVSPEC:END -->
"""


def get_cli_filename(info: "ProjectInfo") -> str:
    """
    根据 AI CLI 类型获取文件名。

    Args:
        info: 项目信息

    Returns:
        str: 文件名（CLAUDE.md 或 GEMINI.md）
    """
    from devspec.init.collector import AICli

    return "CLAUDE.md" if info.ai_cli == AICli.CLAUDE else "GEMINI.md"
