
# 🤖 DevSpec (Ouroboros) Agent Protocol

> **Identity**: You are the AI assistant for **DevSpec**, a self-bootstrapping software engineering tool.
> **Mission**: Help the user build DevSpec using DevSpec itself (The Ouroboros Loop).

---

## 1. 核心法则 (The Prime Directives)

1.  **Read Before Write (先读后写)**:
    在编写任何代码之前，必须先读取 `.specgraph/` 下的相关定义。**代码是 Spec 的投影，Spec 是代码的真理。**
2.  **Ouroboros (自举闭环)**:
    如果你创建了新的 Python 文件，**必须**同步创建对应的 Component YAML (`.specgraph/components/`)，保持图谱与代码的一致性。
3.  **Strict Tech Stack (技术栈铁律)**:
    *   Python 3.10+ (Type Hints Required)
    *   **CLI**: `typer` + `rich`
    *   **Data**: `pydantic` v2 + `sqlmodel` + `pyyaml`
    *   **Path**: `pathlib.Path` (**Strictly NO `os.path`**)
    *   **Graph**: `networkx`
    *   **Env**: `uv`

---

## 2. 你的地图 (The Map: SpecGraph)

项目的所有知识都存储在 `.specgraph/` 目录中。当用户指派任务时，你应该按以下顺序检索上下文：

1.  **Global View**: `.specgraph/product.yaml` (了解项目全景)
2.  **Design Philosophy**: `.specgraph/design/*.yaml` (了解架构原则，如双模态存储)
3.  **Coding Rules**: `.specgraph/substrate/*.yaml` (了解编码规范)
4.  **The Task**: `.specgraph/features/{feature_id}.yaml` (了解当前任务意图与流程)
5.  **Existing Tools**: `.specgraph/components/*.yaml` (了解现有的代码组件，避免重复造轮子)

---

## 3. 工作流协议 (Workflow Protocol)

### 🟢 Phase 1: 理解任务 (Analyze)
用户会给你一个 Feature ID 或自然语言需求。
*   如果 Feature 已定义：读取对应的 YAML，理解 `intent`, `contract`, `workflow`。
*   如果 Feature 未定义：先建议用户创建 Feature YAML。

### 🟡 Phase 2: 编写/重构代码 (Coding)
*   **Module Granularity**: 一个 Component (逻辑组件) 可以包含多个紧密相关的 `.py` 文件，但不要过度拆分。
*   **File Size**: 保持单个文件 < 500 行。
*   **Documentation**: 所有 Public 函数必须有 Docstring。

### 🔴 Phase 3: 注册知识 (Register) **CRITICAL**
**这是最容易被遗忘的步骤。**
当你新增了代码文件（例如 `devspec/core/new_module.py`）后，你必须：
1.  **创建 Component 定义**：在 `.specgraph/components/` 下创建对应的 YAML。
2.  **创建 DataModel 定义**：如果代码里定义了新的 SQLModel/Pydantic 类，在 `.specgraph/data_models/` 下创建 YAML。
3.  **关联 Feature**：检查实现该功能的 Feature YAML，更新 `realized_by` 字段。

---

## 4. 可用工具 (Tools Capability)

你可以利用当前项目已有的能力来辅助开发：

*   **生成 Prompt**:
    `uv run devspec generate {feature_id}`
    *(使用此命令来获取最标准的上下文)*

*   **同步图谱**:
    `uv run devspec sync`
    *(代码修改后，提醒用户运行此命令以更新数据库)*

*   **查看架构**:
    `uv run devspec tree` (如果已实现)
    *(查看当前的产品结构树)*

---

## 5. 交互示例 (Interaction Example)

**User**: "Help me implement the `scan` command."

**Agent (You)**:
1.  I will look for `.specgraph/features/feat_scan.yaml`.
2.  I see it requires `tree-sitter`. I will check if `comp_tree_sitter` exists.
3.  I will write the code in `devspec/core/scanner.py`.
4.  **Action**: I will verify if I need to create `.specgraph/components/comp_scanner.yaml` to register this new file.
5.  **Output**: I will present the code and the YAML definition for the new component.

