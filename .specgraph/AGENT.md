# DevSpec (Ouroboros) Agent Protocol

> **Identity**: You are the AI assistant for **DevSpec**, a self-bootstrapping software engineering tool.
> **Mission**: Help the user build DevSpec using DevSpec itself (The Ouroboros Loop).
> **Core Principle**: 理解优先于分解，对话优先于流程 (Understanding before decomposition, dialogue before pipeline)

---

## 0. 核心法则 (The Prime Directives)

### 0.1 SPEC FIRST (文档先行)

**触发**: 收到功能需求或变更请求时

> 文档是代码的真理，代码是文档的投影。
> - **功能变更**: 必须先通过 `/devspec-collect-req` 更新 Spec，再编写代码
> - **Bug 修复/微小变更**: 可直接修改代码，但需同步更新 Component YAML (`design.logic`)
>
> **判断标准 (何时必须使用 `/devspec-collect-req`)**:
>
> | 变更类型 | 必须使用 collect-req? | 说明 |
> |:---|:---|:---|
> | 新增 CLI 命令 | ✅ 是 | 影响 Feature workflow 和 Component API |
> | 修改 Feature 的核心功能 | ✅ 是 | 需要更新 Feature intent/user_stories |
> | 新增/修改 Domain exports | ✅ 是 | 需要更新 product.yaml |
> | 新增设计原则或规范 | ✅ 是 | 可能涉及 Design/Substrate YAML |
> | 修改 Component 内部实现 | ❌ 否 | 只需更新 comp_*.yaml 的 design.logic |
> | Bug 修复 | ❌ 否 | 可直接修改代码 |
> | 文档修正/补充 | ❌ 否 | 直接修改文档 |
>
> **遗漏风险**: 如果不使用 collect-req，容易遗漏需要同步更新的文件（如 feat_*.yaml, product.yaml）。

### 0.2 FOLLOW SCHEMA (YAML 格式规范)

**触发**: 创建或修改 YAML 文件时

> **权威来源**: `.specgraph/substrate/sub_meta_schema.yaml` 是所有 YAML 格式的唯一权威定义。
>
> **创建 YAML 前必须加载 sub_meta_schema.yaml**，确保：
> *   使用正确的路径模式 (`feat_*.yaml`, `comp_*.yaml`, `des_*.yaml`, `sub_*.yaml`)
> *   包含所有必填字段 (id, domain, intent 等)
> *   遵守命名规范 (snake_case, 正确前缀)
>
> **显式依赖原则**:
> *   Feature 必须通过 `domain` 字段声明归属 (product.yaml 不包含 features 列表)
> *   Feature 间依赖必须通过 `depends_on` 字段显式声明
> *   Component 间依赖必须通过 `dependencies` 字段显式声明

### 0.3 STRICT TECH STACK (技术栈铁律)

**触发**: 编写代码或引入依赖时

> *   Python 3.10+ (Type Hints Required)
> *   **CLI**: `typer` + `rich`
> *   **Data**: `pydantic` v2 + `sqlmodel` + `pyyaml`
> *   **Path**: `pathlib.Path` (**Strictly NO `os.path`**)
> *   **Env**: `uv`

### 0.4 VALIDATE ALWAYS (持续验证)

**触发**: 更新 PRD 或 更新/新增任何 YAML 文件后

> **必须运行 `uv run devspec monitor`** 校验格式和一致性。
> *   确保所有 YAML 文件符合 Schema。
> *   确保 PRD 和 YAML 保持一致。
> *   **不要等到最后才验证，立刻验证。**

### 0.5 FRONTEND STYLE (前端风格规范)

**触发**: 编写前端代码 (HTML/Jinja2/CSS) 时

> **权威来源**: `.specgraph/substrate/sub_frontend_style.yaml` 是前端规范的唯一权威定义。
> **设计理念**: `.specgraph/design/des_frontend_design.yaml` 解释了为什么需要这些规范。
>
> **Spec-First 原则**: 组件 = MD文档(Truth) + HTML代码(Projection)
>
> **组件开发流程** (必须严格遵守):
> ```
> 1. 注册 → devspec frontend register <category> <name> --desc "描述"
>          创建 MD 设计文档 (status: registered)
> 2. 设计 → 编辑 .md 文件，完善参数、样式规范
> 3. 编码 → 根据 MD 文档编写 .html 模板
> 4. 验证 → devspec frontend check (status: verified)
> ```
>
> **重要规则**:
> - **必须先注册再编码**: 不允许直接创建 HTML 文件
> - **MD 文档是 Truth**: HTML 必须遵循 MD 文档定义
> - **修改需同步**: 先更新 MD，再修改 HTML
>
> **组件库结构** (适用于所有项目):
> ```
> templates/components/
> ├── _index.yaml        # 组件索引 (自动维护)
> ├── cards/             # 卡片类组件
> │   ├── domain.md      # 设计文档 (Truth)
> │   └── domain.html    # 代码实现 (Projection)
> ├── badges/            # 徽章类组件
> ├── nav/               # 导航类组件
> └── forms/             # 表单类组件
> ```
>
> **相关 Domain**: `dom_frontend` (Frontend Infrastructure)

---

## 1. 需求收集 (Requirement Collection)

**触发条件**: 用户提出新需求、功能请求、或问"我想要..."类问题时

**执行方式**: `/devspec-collect-req <用户需求描述>`

---

## 2. YAML 生成规范 (YAML Generation Rules) - CRITICAL

**原则**: PRD 先行，YAML 跟随，代码最后。

### 2.1 Feature YAML 生成规范

**触发条件**: 分支 A (新增 Feature) 通过 Exhaustiveness Check 后

**生成顺序** (必须严格遵守):
```
1. 先在 PRD.md 中添加 Feature Section (带 <!-- id: feat_xxx --> anchor)
2. 再创建 .specgraph/features/feat_{name}.yaml
3. 最后规划并创建 Component YAML (如有)
```

**必填字段**:

| 字段 | 格式 | 说明 |
|:---|:---|:---|
| `id` | `feat_{snake_case_name}` | 全小写，下划线分隔，必须与文件名一致 |
| `domain` | `dom_{name}` | 必须是 product.yaml 中已定义的 Domain ID |
| `source_anchor` | `PRD.md#feat_{name}` | 必须先在 PRD 中创建对应 Section 和 anchor |
| `intent` | 一句话描述 | 回答"这个 Feature 解决什么问题？"(The Why) |

**可选字段**:

| 字段 | 何时添加 | 说明 |
|:---|:---|:---|
| `user_stories` | 有明确用户故事时 | 列表格式，"As a X, I want Y" |
| `realized_by` | 已规划 Components 时 | Component ID 列表 |
| `depends_on` | 依赖其他 Feature 时 | Feature ID 列表 |
| `workflow` | 有明确交互流程时 | 步骤列表 |
| `design_principles` | 有特殊设计原则时 | 原则列表 |

**粒度检查**:
- ✅ 正确粒度: 可被独立验收的用户价值单元 (如 "CLI Command Dispatcher", "Code Scanner")
- ❌ 太细: "修改按钮颜色", "修复拼写错误"
- ❌ 太泛: "整个 CLI 系统", "核心功能"

**Feature YAML 模板**:
```yaml
# Feature Definition: {Human Readable Name}
# Part of {Domain Name} (L0: {domain_id})

id: feat_{snake_case_name}
domain: dom_{domain_name}
source_anchor: "PRD.md#feat_{snake_case_name}"
intent: "{一句话描述解决什么问题}"

user_stories:
  - "As a {role}, I want {goal} so that {benefit}."

realized_by:
  - comp_{component_1}
  - comp_{component_2}

# 可选: 如有依赖其他 Feature
depends_on:
  - feat_{other_feature}

# 可选: 如有明确工作流程
workflow:
  - step: 1
    action: "{动作描述}"
    output: "{输出描述}"
```

### 2.2 Component YAML 生成规范

**触发条件**:
- 新增 Feature 后需要实现
- 修改现有 Feature 需要新增 Component (已通过 Exhaustiveness Check)

**生成顺序** (必须严格遵守):
```
1. 确认父 Feature YAML 已存在
2. 创建 .specgraph/components/comp_{name}.yaml
3. 更新父 Feature YAML 的 realized_by 字段
4. 编写代码实现
```

**必填字段**:

| 字段 | 格式 | 说明 |
|:---|:---|:---|
| `id` | `comp_{snake_case_name}` | 全小写，下划线分隔 |
| `type` | `module` | 固定值 |
| `desc` | 技术描述 | 一句话描述这个组件做什么 |
| `file_path` | 物理路径 | 单文件: `devspec/core/xxx.py`，包目录: `devspec/core/xxx/` (以 `/` 结尾) |
| `design` | 详细设计 | 包含 api, logic, 可选 constants/output_files/error_handling |

**design 字段内部结构** (目标: AI 可还原 90-95% 代码):

| 子字段 | Required | 说明 |
|:---|:---|:---|
| `design.api` | ✅ 必填 | 公开接口: signature, desc, params, returns, raises |
| `design.logic` | ✅ 必填 | 伪代码逻辑: 用编号步骤描述实现流程 |
| `design.constants` | ⚠️ 条件必填 | 关键常量/模板 (如果有影响输出的常量) |
| `design.output_files` | ⚠️ 条件必填 | 输出文件格式 (如果组件生成文件) |
| `design.error_handling` | ❌ 可选 | 错误处理策略 |

**可选字段**:

| 字段 | 说明 |
|:---|:---|
| `tech_stack` | 使用的库/工具列表 |
| `dependencies` | 依赖的其他 Component ID 列表 |

**粒度检查**:
- ✅ 正确粒度: 一个内聚的 Python 模块 (单文件 < 500 行，或一个包目录)
- ❌ 太大: 整个 `devspec/core/` 目录作为一个 Component

**Component YAML 模板**:
```yaml
# Component Definition: {Human Readable Name}
# Implements: {parent_feature_id}

id: comp_{snake_case_name}
type: module
desc: "{技术描述}"
file_path: "devspec/{path}/{name}.py"

tech_stack:
  - "{library_1}"
  - "{library_2}"

dependencies:
  - comp_{other_component}

design:
  api:
    - signature: "class {ClassName}"
      desc: "{类描述}"
      methods:
        - signature: "def method_name(self, param: Type) -> ReturnType"
          desc: "{方法描述}"
          params:
            - name: "param"
              type: "Type"
              desc: "{参数描述}"
          returns:
            type: "ReturnType"
            desc: "{返回值描述}"

  logic: |
    1. {步骤 1}
       1.1 {子步骤}
       1.2 {子步骤}
    2. {步骤 2}
    3. {步骤 3}

  # 条件必填: 如有关键常量
  constants:
    CONSTANT_NAME: "{value or template}"

  # 条件必填: 如生成文件
  output_files:
    - path: "{output_path_pattern}"
      format: "{format_description}"

  # 可选: 错误处理
  error_handling:
    - condition: "{错误条件}"
      action: "{处理方式}"
```

---

## 3. 代码编写规范 (Coding Phase)

**触发**: 编写代码时

> **权威来源**: `.specgraph/substrate/sub_coding_style.yaml` 是编码规范的唯一权威定义。
>
> **编写代码前必须加载 sub_coding_style.yaml**，遵循其中的：
> - Type Hints 规范 (所有公开函数必须有完整类型注解)
> - Import 顺序 (标准库 → 第三方 → 项目内部)
> - 命名规范 (modules, classes, functions, constants)
> - Docstring 格式 (Google Style)
> - 路径处理 (`pathlib.Path`，**禁止 `os.path`**)
> - 文件规范 (< 500 行, utf-8, 行宽 100)
> - 错误处理规范 (具体异常类型，避免裸 except)

---

## 4. 知识注册 (Register) - CRITICAL

**这是最容易被遗忘的步骤。每次代码变更后必须检查。**

### 4.1 新增 Feature 时的注册清单

```
□ PRD.md 中已添加 Feature Section (带 <!-- id: feat_xxx --> anchor)
□ .specgraph/features/feat_{name}.yaml 已创建
□ Feature YAML 包含所有必填字段 (id, domain, source_anchor, intent)
□ product.yaml 中 domain 存在且 ID 匹配
```

### 4.2 新增 Component 时的注册清单

```
□ 父 Feature YAML 存在
□ .specgraph/components/comp_{name}.yaml 已创建
□ Component YAML 包含所有必填字段 (id, type, desc, file_path, design)
□ design 包含 api 和 logic
□ 父 Feature YAML 的 realized_by 字段已更新
□ 代码文件路径与 file_path 一致
```

### 4.3 修改代码时的注册清单

```
□ 如果修改了公开 API → 更新 Component YAML 的 design.api
□ 如果修改了核心逻辑 → 更新 Component YAML 的 design.logic
□ 如果新增了常量/模板 → 更新 Component YAML 的 design.constants
```

---

## 5. 能力注册 (Capability Registry)

**自举演进规则**: 当项目实现了新能力后，必须在此注册，将"需求描述"升级为"操作指令"。

### 状态说明

| 状态 | 含义 |
|:---|:---|
| ⏳ 手动 | 需要 AI 手动执行文件操作 |
| ✅ 自动 | 可通过 CLI 命令执行 |
| 🔜 待实现 | 功能尚未开发 |

### 5.1 需求分析阶段能力

| 能力 | 状态 | 操作指令 |
|:---|:---|:---|
| 加载 Product (Vision + Domains) | ⏳ 手动 | `Read .specgraph/product.yaml` (完整文件: vision, description, domains) |
| 筛选 Domain 的 Features | ⏳ 手动 | `Glob .specgraph/features/feat_*.yaml` → 逐个读取 → 按 `domain` 字段过滤 |
| 加载 Feature 的 Components | ⏳ 手动 | 读取 `feat_*.yaml` 的 `realized_by` 字段 → `Read .specgraph/components/comp_*.yaml` |
| 查询节点关系图 | 🔜 待实现 | `uv run devspec query <node_id>` (待 feat_specgraph_database 完成) |

### 5.2 YAML 生成阶段能力

| 能力 | 状态 | 操作指令 |
|:---|:---|:---|
| 创建 Feature YAML | ⏳ 手动 | `Write .specgraph/features/feat_{name}.yaml` (使用 Section 2.1 模板) |
| 创建 Component YAML | ⏳ 手动 | `Write .specgraph/components/comp_{name}.yaml` (使用 Section 2.2 模板) |
| 验证 YAML 结构 | 🔜 待实现 | `uv run devspec validate` (待 feat_consistency_monitor 增强) |

### 5.3 代码生成阶段能力

| 能力 | 状态 | 操作指令 |
|:---|:---|:---|
| 根据 Component 设计生成代码 | ⏳ 手动 | 读取 `comp_*.yaml` 的 `design` 字段 → 按 `api` 和 `logic` 编写代码 |
| 同步图谱到数据库 | 🔜 待实现 | `uv run devspec sync` (待 feat_specgraph_database 完成) |

### 5.4 质量保障阶段能力

| 能力 | 状态 | 操作指令 |
|:---|:---|:---|
| 运行一致性监控 | ✅ 自动 | `uv run devspec monitor` |
| PRD-YAML 一致性检查 | ✅ 自动 | `uv run devspec monitor` (包含在 monitor 中) |

### 5.5 SpecGraph 查看能力

| 能力 | 状态 | 操作指令 |
|:---|:---|:---|
| 启动 SpecGraph Viewer | 🔜 待实现 | `uv run devspec serve` (待 dom_specview 完成) |

### 5.6 前端开发能力

| 能力 | 状态 | 操作指令 |
|:---|:---|:---|
| 注册新组件 | ✅ 自动 | `uv run devspec frontend register <category> <name> --desc "描述"` |
| 列出组件 | ✅ 自动 | `uv run devspec frontend list` |
| 搜索组件 | ✅ 自动 | `uv run devspec frontend list --search <keyword>` |
| 验证组件 | ✅ 自动 | `uv run devspec frontend check` |
| 使用统计 | ✅ 自动 | `uv run devspec frontend stats` |

**组件开发工作流**:
```
1. 注册: devspec frontend register cards domain --desc "Domain 展示卡片"
   → 创建 templates/components/cards/domain.md (设计文档)
   → 更新 _index.yaml (status: registered)

2. 设计: 编辑 domain.md，完善参数、样式规范

3. 编码: 创建 templates/components/cards/domain.html
   → 遵循 domain.md 定义的规范

4. 验证: devspec frontend check
   → 检查 MD 与 HTML 一致性 (status: verified)
```

---

*Auto-generated by DevSpec Agent Protocol*
