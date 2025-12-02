# DevSpec: The Ouroboros Project

> **Product Requirements Document (PRD)**
> **Version**: 0.3.0 (Restructured)
> **Strategy**: Spec-First Bootstrapping

---

## 1. Product Vision <!-- id: prod_devspec -->

**DevSpec** 是专为 "Super Individuals" (超级个体) 设计的 **Serial Conversational Intelligent Pair-Programming Environment** (串行会话式智能结对编程环境)。
它不仅是开发业务软件的工具，更是一个 **Self-Evolving Life Form** (自我进化的生命体) —— 由自己构建，随使用者习惯不断迭代。

---

## 2. Design Principles

### 2.1 Core Philosophy <!-- id: des_philosophy -->

| Philosophy | Description |
| :--- | :--- |
| **Spec First** | 文档是唯一的事实来源 (Single Source of Truth)。代码是 Spec 的投影。 |
| **Serial Flow** | 专注单任务。追求极致流畅的串行吞吐率，而非伪并行。 |
| **Conversational** | 任务沙箱化，平衡 Token 成本与 Context (上下文) 连贯性。 |
| **Recursive Evolution** | Dogfooding (吃自己的狗粮)。工具由工具自身构建。 |

### 2.2 Documentation Principles <!-- id: des_documentation -->

本原则是 AI 编写和更新 PRD 的"元规则"，必须严格遵守：

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

### 2.3 Architectural Concepts <!-- id: des_architecture -->

为了保证图谱的清晰度，必须严格遵守以下分层定义与粒度标准：

| Concept | Level | Definition | Granularity Rule |
| :--- | :--- | :--- | :--- |
| **Domain (领域)** | L0 | 系统的战略版图 (Strategic Scope)。 | 对应业务目标或职能。全系统不应超过 5-7 个。 |
| **Feature (特性)** | L1 | 用户视角的价值单元 (User Value Unit)。 | 必须能被独立验收。避免太细（如"改颜色"）或太泛（如"核心功能"）。 |
| **Component (组件)** | L2 | 代码的详细设计 (Detailed Design)。 | 包含 API 签名、伪代码逻辑、关键常量、输出文件格式。目标：AI 可还原 90-95% 代码。 |

**Component 设计原则**:

*   **设计即代码**: Component 是代码的详细设计文档，任意 AI (Claude/Gemini/GPT) 应能根据此设计还原 90-95% 的代码。
*   **物理绑定**: 每个 Component 必须通过 `file_path` 字段关联到物理位置。
*   **两种形态**:
    *   **单文件模块**: `file_path: "devspec/core/parser.py"` — 适用于简单组件 (< 500 行)。
    *   **包目录模块**: `file_path: "devspec/core/scanner/"` (以 `/` 结尾) — 适用于复杂组件，内部文件由该 Component 统一管理。

**Component Design Schema (设计字段规范)**:

| Field | Required | Description |
| :--- | :--- | :--- |
| `design.api` | ✅ 必填 | 公开接口定义：函数签名、参数、返回值、异常。 |
| `design.logic` | ✅ 必填 | 伪代码逻辑：用自然语言+编号步骤描述实现流程。 |
| `design.constants` | ⚠️ 条件必填 | 关键常量/模板：如果组件包含影响输出的常量则必填。 |
| `design.output_files` | ⚠️ 条件必填 | 输出文件格式：如果组件生成文件则必填，需定义路径和格式。 |
| `design.error_handling` | ❌ 可选 | 错误处理：关键错误场景及处理方式。 |

**粒度边界 (Granularity Boundary)**:
*   ✅ **包含**: 伪代码逻辑、关键常量、输入输出参数定义、输出文件格式。
*   ❌ **不包含**: 具体实现代码、临时变量、内部私有函数细节。

### 2.4 Bootstrapping Strategy <!-- id: des_bootstrap_strategy -->

本项目采用极致的 **"Spec-First"** 自举策略。我们不依靠临时脚本启动，而是依靠完备的规范。

#### Evolution Phases (演进阶段)

##### Phase 0: Genesis Spec (创世规范)
*   **Principle**: Document First (文档优先)。参考原始需求 (`origin_req/standard_req.md`)，但根目录的 `PRD.md` 和 `.specgraph` 才是事实来源。
*   **Status**: 代码量 0。仅存在 `.specgraph` 目录结构。
*   **Method**:
    1.  定义 **Product** (`product.yaml`)。
    2.  定义核心 **Domains** & **Features** (L1)。
    3.  设计核心 **Components** (L2)。
    4.  Human/AI 扮演 "Execution Engine" (执行引擎)，严格基于 L2 设计生成 bootstrap 代码。
*   **Output**: DevSpec 的 SpecGraph + 初始 Kernel Code。

##### Phase 1: Spec-Driven Implementation (规范驱动实现)
*   **Status**: 拥有基于 Spec 生成的初始 CLI。
*   **Method**:
    1.  修改/细化文档 (L1/L2)。
    2.  运行 DevSpec 工具读取新文档。
    3.  生成/更新功能代码。
*   **Output**: 通过 Spec 验证的完整功能模块。

##### Phase 2: The Ouroboros Loop (衔尾蛇闭环)
*   **Status**: 工具完全成熟。
*   **Method**: Requirement (需求) -> Doc Update (文档更新) -> Tool Perceives Change (工具感知) -> Code Evolves (代码演进)。
*   **Output**: 一个随文档"生长"的软件生命体。

### 2.5 Domain Model <!-- id: des_domain_model -->

DevSpec 的核心架构分为三大领域：

*   **Core Engine (核心引擎)**: 系统的"大脑"，负责维护知识图谱、解析代码、管理上下文。
*   **CLI Interface (命令行界面)**: 系统的"嘴巴"和"耳朵"，负责与用户交互。
*   **Quality Assurance (质量保障)**: 系统的"免疫系统"，负责确保代码与 Spec 的一致性。

### 2.6 Technical Strategy <!-- id: des_tech_strategy -->

为了保证工具的长期可维护性与自举能力，必须遵循以下技术约束：

*   **Language**: Python 3.10+ (强制 Type Hints)。
*   **Environment**: 使用 `uv` 进行极速包管理与环境隔离。
*   **CLI Framework**: 基于 `Typer` 构建命令系统。
*   **UI/UX**: 使用 `Rich` 实现终端可视化 (Tree, Table, Markdown)。
*   **Core Parsing**: 使用 `Tree-sitter` 进行高性能代码分析。
*   **Storage**: `PyYAML` (Git 存储) + `SQLite/SQLModel` (运行时缓存)。

### 2.7 Knowledge Classification: Design vs Substrate <!-- id: des_knowledge_classification -->

SpecGraph 中的知识分为两类：**Design (设计)** 和 **Substrate (基质)**。它们有明确的边界和用途：

| 分类 | 定义 | 回答的问题 | AI 加载时机 |
| :--- | :--- | :--- | :--- |
| **Design** | 设计决策 (Why & What) | 为什么这样设计？目标是什么？ | 理解项目背景、做架构决策时 |
| **Substrate** | 执行约束 (How & Constraints) | 怎么执行？有什么约束？ | 编写代码、验证规范时 |

**Design 节点 (`.specgraph/design/`)** — 理解"为什么":
*   `des_philosophy` - 核心理念 (Spec-First, Serial Flow 的原因)
*   `des_domain_model` - 领域划分的设计思路
*   `des_bootstrap_strategy` - 自举策略的设计决策
*   `des_architecture` - 分层架构的目的和原则

**Substrate 节点 (`.specgraph/substrate/`)** — 执行"怎么做":
*   `sub_tech_stack` <!-- id: sub_tech_stack --> - 技术栈约束 (用 typer 不用 click，用 pathlib 不用 os.path)
*   `sub_meta_schema` - YAML 结构验证规则 (必填字段、命名规范)
*   `sub_coding_style` <!-- id: sub_coding_style --> - 编码规范 (命名、路径、注释、Type Hints)

**AI 加载规则**:

| 任务场景 | 加载的知识 |
| :--- | :--- |
| "帮我理解这个项目" | Design 节点 |
| "帮我设计一个新 Feature" | Design + 相关 Feature YAML |
| "帮我实现这个 Component" | Substrate + Component YAML |
| "帮我创建新的 YAML 文件" | `sub_meta_schema` |
| "帮我写/审查代码" | `sub_tech_stack` + `sub_coding_style` |

---

## 3. Domain: Core Engine (`dom_core`) <!-- id: dom_core -->

**Description**: 系统的"大脑"，负责维护知识图谱、解析代码、管理上下文。

### 3.1 Feature: Meta-Schema Management <!-- id: sub_meta_schema -->

定义 Feature/Component 的 YAML 结构规范与粒度标准，防止图谱熵增。

### 3.2 Feature: Consistency Monitor <!-- id: feat_consistency_monitor -->

监控 PRD (Markdown) 与 Spec (YAML) 的一致性，生成分层状态报告 (Layered Dashboard)。

**Dashboard Structure (分层仪表板)**:
*   **Progress Overview**: 多维度进度统计 (Spec Sync + Feature Assignment + Overall)。
*   **System Design Table**: Domain 与 Design 节点的 Spec 同步状态。
*   **Features Table**: Feature 节点的 Spec 同步 + Component 分配状态。
*   **Components Table**: Component 节点的 Spec 同步状态。

**Components**:
*   **Core Logic** <!-- id: comp_consistency_monitor -->: 核心比对逻辑与分层统计实现。
*   **Spec Indexer** <!-- id: comp_spec_indexer -->: 索引 SpecGraph 节点。
*   **Markdown Parser** <!-- id: comp_markdown_parser -->: 解析 PRD 锚点。

### 3.3 Feature: SpecGraph Engine <!-- id: feat_specgraph_engine -->

维护 L1-L3 的多层级知识图谱。

*   **L1 (Requirement Layer)**: Feature (功能), Requirement (需求) —— *定义"要做什么"*。
*   **L2 (Design Layer)**: Component (组件), API (接口), DataModel (模型) —— *定义"怎么做"*。
*   **L3 (Implementation Layer)**: Code Symbols (Function, Class) —— *代码的物理投影，由 Scanner 自动维护*。

### 3.4 Feature: Code Scanner <!-- id: feat_code_scanner -->

基于 Tree-sitter 的代码分析与索引。

### 3.5 Feature: Context Assembler <!-- id: feat_context_assembler -->

为 AI 组装最小充分上下文。

### 3.6 Feature: Requirement Collector <!-- id: feat_requirement_collector -->

负责收集、分析和分解用户需求，但不直接修改代码。

**Core Functions (核心功能)**:
1.  **Raw Logging (原始记录)**: 将用户的原始想法或要求追加到原始需求文档，不做任何更改，仅记录时间戳。
2.  **Analysis & Decomposition (分析与分解)**:
    *   **Vision Check**: 检查需求是否符合当前 Product Vision。如果不符，明确指出并中止，不更新 PRD。
    *   **Decomposition**: 如果符合 Vision，按粒度分解任务：
        *   **Cross-Domain**: 生成 Domain 级别的子任务清单。
        *   **Domain-Level**: 生成 Feature 级别的子任务清单。
        *   **Feature-Level**: 生成 Component 级别的子任务清单。
        *   **Component-Level**: 仅更新 Component。
3.  **Doc-Only Update (仅文档更新)**: 收集阶段只更新文档 (PRD/SpecGraph)，绝不更新代码。
4.  **Reporting (报告)**: 输出详细的更新报告，保存到 `reports/` 目录，文件名包含日期和时间。

---

## 4. Domain: CLI Interface (`dom_cli`) <!-- id: dom_cli -->

**Description**: 系统的"嘴巴"和"耳朵"，负责与用户交互。

### 4.1 Feature: Command Structure <!-- id: feat_cli_command_structure -->

基于 Typer 的命令分发系统，提供统一的 CLI 入口和命令注册机制。

**Initial Commands (初始命令集)**:
*   `devspec init` - 初始化项目，为 Claude Code 和 Gemini CLI 生成 slash command 文件。
*   `devspec monitor` - 运行一致性检查，生成 Dashboard。
*   `devspec validate-prd` - 校验 PRD.md 格式是否符合规范。
*   `devspec tree` - 查看产品结构树（预留）。
*   `devspec generate <feature_id>` - 为指定 Feature 生成上下文 Prompt（预留）。

**Components**:
*   **CLI App** <!-- id: comp_cli_app -->: Typer 应用主入口，负责命令注册与全局配置。
*   **Init Command** <!-- id: comp_cli_init -->: `devspec init` 命令实现，生成 `.claude/commands/` 和 `.gemini/commands/` 下的 slash command 文件（包括 `devspec-monitor` 和 `devspec-write-prd`），使 AI CLI 可直接调用 DevSpec 命令。
*   **Monitor Command** <!-- id: comp_cli_monitor -->: `devspec monitor` 命令实现，调用 ConsistencyMonitor。
*   **Validate PRD Command** <!-- id: comp_cli_validate_prd -->: `devspec validate-prd` 命令实现，调用 PRD Validator 校验 PRD.md 格式。

### 4.2 Feature: Visual Output <!-- id: feat_cli_visual_output -->

基于 Rich 的结构化展示 (Tree, Tables)。

### 4.3 Feature: Session Management <!-- id: feat_cli_session_management -->

任务会话的生命周期管理 (Start/Commit/Abort)。

---

## 5. Domain: Quality Assurance (`dom_quality`) <!-- id: dom_quality -->

**Description**: 系统的"免疫系统"，负责确保代码与 Spec 的一致性。

### 5.1 Feature: Drift Detection <!-- id: feat_quality_drift_detection -->

检测 Spec 与 Code 的偏差。

### 5.2 Feature: Compliance Audit <!-- id: feat_quality_compliance_audit -->

审计代码规范。

### 5.3 Feature: Auto-Fix <!-- id: feat_quality_auto_fix -->

自动修复简单的合规性问题。

### 5.4 Feature: PRD Format Validator <!-- id: feat_quality_prd_validator -->

校验 PRD.md 是否符合 `des_prompt_prd_writer.md` 定义的结构规范。验证章节结构、锚点格式、双语规则等。

**Components**:
*   **PRD Validator** <!-- id: comp_prd_validator -->: PRD 格式校验核心逻辑，检查章节结构、锚点格式、命名规范。

---
*Generated by DevSpec Agent - strict adherence to Spec-First Protocol.*
