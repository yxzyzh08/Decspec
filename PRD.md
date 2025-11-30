# DevSpec: The Ouroboros Project (AI-Native Development System) <!-- id: prod_devspec -->

> **Product Requirements Document (PRD)**
> **Version**: 0.2.0 (Refactored)
> **Strategy**: Spec-First Bootstrapping

---

## 1. Product Vision (产品愿景) <!-- id: prod_vision -->

**DevSpec** 是专为 "Super Individuals" (超级个体) 设计的 **Serial Conversational Intelligent Pair-Programming Environment** (串行会话式智能结对编程环境)。
它不仅是开发业务软件的工具，更是一个 **Self-Evolving Life Form** (自我进化的生命体) —— 由自己构建，随使用者习惯不断迭代。

### 1.1 Core Philosophy (核心哲学) <!-- id: des_philosophy -->

| Philosophy | Description |
| :--- | :--- |
| **Spec First** | 文档是唯一的事实来源 (Single Source of Truth)。代码是 Spec 的投影。 |
| **Serial Flow** | 专注单任务。追求极致流畅的串行吞吐率，而非伪并行。 |
| **Conversational** | 任务沙箱化，平衡 Token 成本与 Context (上下文) 连贯性。 |
| **Recursive Evolution** | Dogfooding (吃自己的狗粮)。工具由工具自身构建。 |

### 1.2 Documentation Principles (文档原则) <!-- id: des_documentation -->

本原则是 AI 编写和更新 PRD 的“元规则”，必须严格遵守：

1.  **Bilingual Structure (双语结构)**:
    *   **English**: 必须用于所有标题 (H1-H6)、专业术语 (Terms)、ID、文件名、代码片段。
    *   **Chinese**: 必须用于具体的描述 (Description)、解释 (Explanation)、原因阐述 (Reasoning)。
2.  **Anchor Injection (锚点注入)**:
    *   为了实现 PRD 与 YAML 的自动化同步，必须在关键节点（Feature/Component/Module）的标题行末尾注入隐式 ID。
    *   格式: `<!-- id: <node_id> -->`
    *   示例: `### Domain: Core Engine <!-- id: dom_core -->`
3.  **Single Source of Truth (唯一事实来源)**:
    *   PRD 定义 Intent (意图)，YAML 定义 Structure (结构)。
    *   当二者冲突时，以 PRD 的意图为准，修正 YAML 结构。

### 1.3 Architectural Concepts (架构概念) <!-- id: des_architecture -->

为了保证图谱的清晰度，必须严格遵守以下分层定义与粒度标准：

| Concept | Level | Definition | Granularity Rule |
| :--- | :--- | :--- | :--- |
| **Domain (领域)** | L0 | 系统的战略版图 (Strategic Scope)。 | 对应业务目标或职能。全系统不应超过 5-7 个。 |
| **Feature (特性)** | L1 | 用户视角的价值单元 (User Value Unit)。 | 必须能被独立验收。避免太细（如"改颜色"）或太泛（如"核心功能"）。 |
| **Component (组件)** | L2 | 架构视角的构建模块 (Building Block)。 | 逻辑上的代码集合 (Module/Class)。应具备单一职责。 |

---

## 2. Bootstrapping Strategy (自举策略) <!-- id: des_bootstrap_strategy -->

本项目采用极致的 **"Spec-First"** 自举策略。我们不依靠临时脚本启动，而是依靠完备的规范。

### 2.1 Evolution Phases (演进阶段)

#### Phase 0: Genesis Spec (创世规范)
*   **Principle**: Document First (文档优先)。参考原始需求 (`origin_req/standard_req.md`)，但根目录的 `PRD.md` 和 `.specgraph` 才是事实来源。
*   **Status**: 代码量 0。仅存在 `.specgraph` 目录结构。
*   **Method**:
    1.  定义 **Product** (`product.yaml`)。
    2.  定义核心 **Domains** & **Features** (L1)。
    3.  设计核心 **Components** (L2)。
    4.  Human/AI 扮演 "Execution Engine" (执行引擎)，严格基于 L2 设计生成 bootstrap 代码。
*   **Output**: DevSpec 的 SpecGraph + 初始 Kernel Code。

#### Phase 1: Spec-Driven Implementation (规范驱动实现)
*   **Status**: 拥有基于 Spec 生成的初始 CLI。
*   **Method**:
    1.  修改/细化文档 (L1/L2)。
    2.  运行 DevSpec 工具读取新文档。
    3.  生成/更新功能代码。
*   **Output**: 通过 Spec 验证的完整功能模块。

#### Phase 2: The Ouroboros Loop (衔尾蛇闭环)
*   **Status**: 工具完全成熟。
*   **Method**: Requirement (需求) -> Doc Update (文档更新) -> Tool Perceives Change (工具感知) -> Code Evolves (代码演进)。
*   **Output**: 一个随文档“生长”的软件生命体。

---

## 3. Core Domains (核心领域) <!-- id: des_domain_model -->

### 3.1 Domain: Core Engine (`dom_core`) <!-- id: dom_core -->
*   **Description**: 系统的“大脑”，负责维护知识图谱、解析代码、管理上下文。
*   **Key Features**:
    *   **Meta-Schema Management** <!-- id: sub_meta_schema -->: 定义 Feature/Component 的 YAML 结构规范与粒度标准，防止图谱熵增。   
    *   **Consistency Monitor** <!-- id: feat_consistency_monitor -->: 监控 PRD (Markdown) 与 Spec (YAML) 的一致性，并生成同步状态报告。
        *   **Core Logic** <!-- id: comp_consistency_monitor -->: 核心比对逻辑实现。
        *   **Spec Status**: 验证 Intent (PRD) 与 Definition (YAML) 的同步状态 (Synced/PRD_Only/YAML_Only)。
        *   **Impl Status**: 验证 Feature 是否已分配 Component (Assigned/Unassigned)。
    *   **SpecGraph Engine** <!-- id: feat_specgraph_engine -->: 维护 L1-L3 的多层级知识图谱。
        *   **L1 (Requirement Layer)**: Feature (功能), Requirement (需求) —— *定义“要做什么”*。
        *   **L2 (Design Layer)**: Component (组件), API (接口), DataModel (模型) —— *定义“怎么做”*。
        *   **L3 (Implementation Layer)**: Code Symbols (Function, Class) —— *代码的物理投影，由 Scanner 自动维护*。
    *   **Code Scanner** <!-- id: feat_code_scanner -->: 基于 Tree-sitter 的代码分析与索引。
    *   **Context Assembler** <!-- id: feat_context_assembler -->: 为 AI 组装最小充分上下文。



### 3.2 Domain: CLI Interface (`dom_cli`) <!-- id: dom_cli -->
*   **Description**: 系统的“嘴巴”和“耳朵”，负责与用户交互。
*   **Key Features**:
    *   **Command Structure** <!-- id: feat_cli_command_structure -->: 基于 Typer 的命令分发。
    *   **Visual Output** <!-- id: feat_cli_visual_output -->: 基于 Rich 的结构化展示 (Tree, Tables)。
    *   **Session Management** <!-- id: feat_cli_session_management -->: 任务会话的生命周期管理 (Start/Commit/Abort)。

### 3.3 Domain: Quality Assurance (`dom_quality`) <!-- id: dom_quality -->
*   **Description**: 系统的“免疫系统”，负责确保代码与 Spec 的一致性。
*   **Key Features**:
    *   **Drift Detection** <!-- id: feat_quality_drift_detection -->: 检测 Spec 与 Code 的偏差。
    *   **Compliance Audit** <!-- id: feat_quality_compliance_audit -->: 审计代码规范。
    *   **Auto-Fix** <!-- id: feat_quality_auto_fix -->: 自动修复简单的合规性问题。

---

## 4. Technical Strategy (技术策略) <!-- id: des_tech_strategy -->
<!-- id: sub_tech_stack -->

为了保证工具的长期可维护性与自举能力，必须遵循以下技术约束：

*   **Language**: Python 3.10+ (强制 Type Hints)。
*   **Environment**: 使用 `uv` 进行极速包管理与环境隔离。
*   **CLI Framework**: 基于 `Typer` 构建命令系统。
*   **UI/UX**: 使用 `Rich` 实现终端可视化 (Tree, Table, Markdown)。
    *   **Code Scanner**: 基于 Tree-sitter 的代码分析与索引。
        *   **Spec Indexer** <!-- id: comp_spec_indexer -->: 索引 SpecGraph 节点。
        *   **Markdown Parser** <!-- id: comp_markdown_parser -->: 解析 PRD 锚点。
*   **Core Parsing**: 使用 `Tree-sitter` 进行高性能代码分析。
*   **Storage**: `PyYAML` (Git 存储) + `SQLite/SQLModel` (运行时缓存)。


---
*Generated by DevSpec Agent - strict adherence to Spec-First Protocol.*
