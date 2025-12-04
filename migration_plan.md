# DevSpec SQLite 迁移与新需求工作流重构计划

本计划旨在将 DevSpec 的核心知识库从分散的 YAML 文件迁移至 SQLite 数据库，并重构需求收集工作流，以实现更精确的上下文加载和更严谨的“Read-Before-Write”机制。

## 1. 核心目标 (Core Objectives)

1.  **单一事实来源 (Single Source of Truth)**: 将 PRD、Design、Domain、Feature、Component 等所有元数据存入 SQLite 数据库。
2.  **图谱化管理 (Graph Management)**: 利用关系型数据库维护 L0 (Domain) -> L1 (Feature) -> L2 (Component) 的层级关系及依赖。
3.  **精确上下文 (Precise Context)**: 在处理新需求时，按需加载架构原则、领域模型和相关特性，避免上下文污染。
4.  **程序化维护 (Programmatic Maintenance)**: AI 不直接修改数据库文件，而是通过调用 CLI 工具或 Python API 来更新图谱。

## 2. 数据库设计 (Database Schema Design)

我们将使用 `SQLModel` (SQLAlchemy + Pydantic) 定义以下核心表：

### 2.1 基础元数据 (Base Metadata)
- **Document**: 存储非结构化文档内容 (如 PRD, Design Docs)。
    - `id`: string (e.g., "des_architecture")
    - `type`: enum (design, substrate, prd)
    - `content`: text (Markdown content)
    - `embedding`: vector (optional, for future semantic search)

### 2.2 架构层级 (Architecture Levels)
- **Domain (L0)**
    - `id`: string (e.g., "dom_core")
    - `name`: string
    - `description`: text
- **Feature (L1)**
    - `id`: string (e.g., "feat_consistency_check")
    - `domain_id`: foreign_key (Domain.id)
    - `intent`: text
    - `status`: enum (planned, active, completed)
    - `depends_on`: json_list (List of Feature IDs)
- **Component (L2)**
    - `id`: string (e.g., "comp_spec_parser")
    - `feature_id`: foreign_key (Feature.id)
    - `file_path`: string (physical binding)
    - `description`: text

### 2.3 追踪关系 (Traceability)
- **Requirement**: 原始需求记录。
- **TraceLink**: 记录 Requirement -> Feature/Component 的多对多关系。

## 3. 迁移策略 (Migration Strategy)

我们将开发一个一次性迁移脚本 `scripts/migrate_yaml_to_sqlite.py`：

1.  **Extract**: 遍历 `.specgraph` 目录下的 `product.yaml`, `design/*.yaml`, `features/*.yaml`, `components/*.yaml`。
2.  **Transform**: 将 YAML 数据转换为 SQLModel 对象。
    - 验证引用完整性 (Referential Integrity)。
    - 补全缺失的 ID 或关系。
3.  **Load**: 写入 `.specgraph/devspec.db` (SQLite)。
4.  **Verify**: 运行一致性检查，确保数据库内容与文件系统代码匹配。

## 4. 新需求收集工作流 (New Requirement Workflow)

重构 `devspec-collect-req` 指令，遵循“由上至下、按需加载”原则：

### 步骤 1: 加载架构原则 (Load Principles)
- **Action**: 读取数据库中的 `des_architecture` 和 `des_philosophy`。
- **Goal**: 让 AI 理解 L0-L2 分层原则和设计哲学。

### 步骤 2: 领域分析 (Domain Analysis)
- **Action**: 读取所有 `Domain` (L0) 信息。
- **Goal**: 识别新需求涉及哪些领域 (Domain)。
- **Decision**:
    - 如果涉及现有 Domain -> 加载该 Domain 下的 `Feature` 列表。
    - 如果是全新 Domain -> 建议创建新 Domain。

### 步骤 3: 特性定位 (Feature Targeting)
- **Action**: 基于选定的 Domain，加载相关 `Feature` (L1) 的 Intent 和 Contract。
- **Goal**: 判断是修改现有 Feature 还是创建新 Feature。
    - **Cross-Domain**: 如果涉及多个 Domain，需加载相关联 Domain 的 API/Interface。

### 步骤 4: 组件设计 (Component Design)
- **Action**: 加载相关 `Component` (L2) 定义及代码摘要。
- **Goal**: 生成具体的代码修改计划或新组件定义。

### 步骤 5: 图谱更新 (Graph Update)
- **Action**: AI 生成 JSON/YAML 格式的变更请求，调用 `devspec graph update` (新命令) 更新数据库。
- **Constraint**: 禁止 AI 直接操作 SQL，必须通过 API。

### 4.1 执行策略：CLI 优先 (CLI-First Strategy)

为了节省 API 成本并利用现有 CLI 工具 (Claude Code, Gemini CLI) 的强大能力，初期采用 **Prompt Engineering** 模式：

1.  **DevSpec 角色**: 
    - **Context Assembler**: 负责从图数据库中提取精准的上下文（仅相关 Feature/Component）。
    - **Prompt Generator**: 生成包含架构原则、任务指令、相关代码引用的结构化 Prompt。
    - **Verifier**: 任务完成后，检查 Spec 与代码的一致性。

2.  **CLI 角色**: 
    - **Executor**: 接收 DevSpec 生成的 Prompt，执行具体的代码编写和重构。

3.  **交互流程**:
    - 用户输入: `devspec plan "Add logging to scanner"`
    - DevSpec 输出: 生成 `.devspec/context/task_context.md`
    - 用户执行: `claude -p "Read .devspec/context/task_context.md and implement"`
    - 用户验收: `devspec verify`

## 5. 执行计划 (Execution Steps)

1.  **环境准备**: 添加 `sqlmodel` 依赖 (已存在)，创建 `devspec/db` 模块。
2.  **Schema 定义**: 在 `devspec/db/models.py` 中实现上述模型。
3.  **迁移工具**: 开发并运行迁移脚本，生成初始数据库。
4.  **CLI 改造**: 修改 `devspec` CLI，使其从 DB 读取数据而非 YAML。
    - 优先改造 `devspec validate-prd` 和 `devspec monitor`。
5.  **工作流更新**: 更新 `.agent/workflows/devspec-collect-req.md` 以匹配新流程。

## 6. 风险与对策 (Risks & Mitigation)

- **风险**: 数据库与文件系统不同步。
    - **对策**: 每次运行 `devspec` 命令时，自动检查文件哈希与 DB 记录是否一致 (Consistency Check)。
- **风险**: 迁移过程中丢失数据。
    - **对策**: 迁移脚本执行前备份 `.specgraph` 目录。
