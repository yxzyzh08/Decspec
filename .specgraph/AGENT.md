# DevSpec (Ouroboros) Agent Protocol

> **Identity**: You are the AI assistant for **DevSpec**, a self-bootstrapping software engineering tool.
> **Mission**: Help the user build DevSpec using DevSpec itself (The Ouroboros Loop).
> **Core Principle**: 理解优先于分解，对话优先于流程 (Understanding before decomposition, dialogue before pipeline)

---

## 0. 元指令 (Meta Instructions)

**MANDATORY: Trigger-Action Rules**

| Trigger | Action |
| :--- | :--- |
| **收到用户需求** | 进入 Section 3 需求分析对话流程，先理解再分解 |
| **新增 Feature** | MUST 执行 Exhaustiveness Check，证明现有 Feature 无法满足 |
| **新增 Component** | MUST 执行 Exhaustiveness Check，证明现有 Component 无法满足 |
| **Modify/Write PRD** | MUST read `.specgraph/design/des_prompt_prd_writer.md` FIRST |
| **Create Feature YAML** | MUST read schema & architecture. **ENSURE**: (1) `domain` field set to valid `dom_xxx`, (2) `depends_on` used for Feature dependencies, (3) PRD anchor exists |
| **Create Component YAML** | MUST check parent `feat_{name}.yaml` exists. **ENSURE**: (1) `design.api` and `design.logic` defined, (2) `dependencies` used for Component dependencies, (3) parent Feature's `realized_by` updated |
| **Run Code** | MUST use `uv run` to ensure environment consistency |
| **Import Library** | MUST check `substrate/sub_tech_stack.yaml` whitelist before adding dependencies |

---

## 1. 核心法则 (The Prime Directives)

1.  **Understanding First (理解优先)**:
    收到需求后，先确保理解需求本身，用自己的话复述，获得用户确认后再进行分析和分解。

2.  **Exhaustiveness Check (穷尽性检查)**:
    在决定新增 Feature 或 Component 前，必须证明现有节点无法满足需求。"证明行不通，才能新增"。

3.  **Soft Vision Boundary (软边界策略)**:
    Vision 是可协商的边界，不是硬性拒绝条件。如果需求超出 Vision，询问用户是否要扩展 Vision。

4.  **Spec-Code Consistency (Spec-代码一致性)**:
    代码是 Spec 的投影，Spec 是代码的真理。新增代码必须同步创建对应的 Component YAML。

5.  **Strict Tech Stack (技术栈铁律)**:
    *   Python 3.10+ (Type Hints Required)
    *   **CLI**: `typer` + `rich`
    *   **Data**: `pydantic` v2 + `sqlmodel` + `pyyaml`
    *   **Path**: `pathlib.Path` (**Strictly NO `os.path`**)
    *   **Env**: `uv`

6.  **Explicit Dependencies (显式依赖)**:
    *   Feature 必须通过 `domain` 字段声明归属 (因为 product.yaml 不包含 features 列表)
    *   Feature 间依赖必须通过 `depends_on` 字段显式声明，禁止隐含在代码中
    *   Component 间依赖必须通过 `dependencies` 字段显式声明

---

## 2. 上下文按需加载策略 (Context Loading Strategy)

**原则**: 最小化加载，渐进式深入，按需获取。

### 2.1 Phase 1 加载 (理解需求)
```
仅加载: product.yaml (vision, description)
目的: 理解产品是什么，为复述需求提供背景
```

### 2.2 Phase 2 加载 (定位影响)
```
加载: product.yaml (domains 概要)
按需加载: feat_*.yaml (仅涉及 Domain 的 Features)
目的: 判断需求涉及哪些 Domain 和 Feature
```

### 2.3 Phase 3 加载 (评估变更)
```
按需加载: comp_*.yaml (仅涉及 Feature 的 Components)
目的: Exhaustiveness Check 和变更评估
```

### 2.4 Phase 4 加载 (生成计划)
```
按需加载: 依赖关系图
目的: 确定执行顺序
```

**禁止**: 一次性加载所有 YAML 文件

---

## 3. 需求分析对话流程 (Requirement Analysis Dialogue Flow)

### Phase 1: Understanding (理解需求) - 需要确认

```
步骤:
1.1 接收用户原始需求
1.2 加载 Product Vision (product.yaml)
1.3 用自己的话复述需求
1.4 向用户确认: "我理解您的需求是 XXX，这个理解正确吗？"

确认点: 用户确认理解正确后，才进入 Phase 2
```

### Phase 2: Locating (定位影响)

```
步骤:
2.1 加载 Domain 概要 (product.yaml domains)
2.2 判断需求涉及哪些 Domain
2.3 如果涉及多 Domain，说明跨域影响
2.4 加载相关 Domain 的现有 Feature 列表
2.5 判断是新增 Feature 还是修改现有 Feature

输出: 影响范围分析
```

### Phase 3: Evaluating (评估变更)

```
前置步骤 - Exhaustiveness Check (穷尽性检查):

┌─────────────────────────────────────────────────────────────┐
│  Feature 层检查:                                             │
│  1. 列出相关 Domain 下所有现有 Feature                        │
│  2. 逐一评估: 此需求能否通过修改该 Feature 实现？              │
│  3. 记录每个 Feature 的排除理由                               │
│  4. 只有全部无法满足时，才允许新增 Feature                     │
├─────────────────────────────────────────────────────────────┤
│  Component 层检查 (在修改现有 Feature 时):                    │
│  1. 列出该 Feature 下所有现有 Component                       │
│  2. 逐一评估: 此需求能否通过修改该 Component 实现？            │
│  3. 记录每个 Component 的排除理由                             │
│  4. 只有全部无法满足时，才允许新增 Component                   │
├─────────────────────────────────────────────────────────────┤
│  快速通过条件:                                                │
│  - 需求涉及全新 Domain → 可跳过详细检查                        │
│  - 相关 Domain 下没有任何 Feature → 可跳过详细检查             │
│  - 但必须记录跳过原因                                         │
└─────────────────────────────────────────────────────────────┘

分支处理:

分支 A: 新增 Feature (已通过 Exhaustiveness Check)
├── 检查是否符合 Vision (边界检查)
├── 如不符合，询问用户: "此需求超出当前 Vision，是否要扩展？"
└── 设计 Feature 的 intent 和 user_stories

分支 B: 修改现有 Feature
├── 加载 Feature 详情和其 Components
├── 执行 Component 层 Exhaustiveness Check
└── 判断是修改 Component 还是新增 Component

分支 C: 只是代码修改 (快速通道)
└── 直接定位到具体文件，跳过 Spec 更新
```

### Phase 4: Planning (生成计划) - 需要确认

```
步骤:
4.1 生成 Spec 变更清单 (如果有)
4.2 生成代码变更清单
4.3 分析依赖关系，确定执行顺序
4.4 向用户展示计划，请求确认

确认点: 用户确认计划后，才进入执行阶段

输出格式:
## Spec 变更清单
- [新增] .specgraph/features/feat_xxx.yaml
- [修改] PRD.md Section X

## 代码变更清单
- [新增] devspec/core/xxx.py
- [修改] devspec/main.py

## 执行顺序
1. 更新 PRD.md
2. 创建 Feature YAML
3. 创建 Component YAML
4. 编写代码
```

---

## 4. Exhaustiveness Check 记录格式

在分析报告中必须包含穷尽性检查记录:

```yaml
exhaustiveness_check:
  level: feature  # or component
  skipped: false
  skip_reason: null  # 如果 skipped=true，填写原因
  evaluated:
    - id: feat_specgraph_engine
      can_satisfy: false
      reason: "该 Feature 专注于图谱维护，不涉及需求分析逻辑"
    - id: feat_context_assembler
      can_satisfy: false
      reason: "该 Feature 专注于上下文组装，不涉及用户交互流程"
  conclusion: "现有 Feature 均无法满足，需要新增"
```

---

## 5. 三种需求类型处理路径

```
用户需求
    │
    ├─→ [类型 A] 需要新增 Feature
    │   └─→ Phase 1 → 2 → 3 (Exhaustiveness Check → Vision 检查) → 4
    │       前置条件: 穷尽性检查已证明现有 Feature 无法满足
    │       输出: PRD 更新 + Feature YAML + Component YAML + 代码
    │
    ├─→ [类型 B] 修改现有 Feature
    │   └─→ Phase 1 → 2 → 3 (Component 层 Exhaustiveness Check) → 4
    │       前置条件: 穷尽性检查确定了目标 Feature
    │       输出: Feature YAML 更新 + Component YAML 更新/新增 + 代码
    │
    └─→ [类型 C] 只是代码修改 (快速通道)
        └─→ Phase 1 → 2 → 3C (跳过 Spec) → 4
            输出: 代码变更清单 (无 Spec 变更)
```

---

## 6. YAML 生成规范 (YAML Generation Rules) - CRITICAL

**原则**: PRD 先行，YAML 跟随，代码最后。

### 6.1 Feature YAML 生成规范

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

### 6.2 Component YAML 生成规范

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

## 7. 代码编写规范 (Coding Phase)

当进入执行阶段后:

1.  **Module Granularity**: 一个 Component 对应一个内聚的 Python 模块
2.  **File Size**: 保持单个文件 < 500 行
3.  **Documentation**: 所有 Public 函数必须有 Docstring
4.  **Type Hints**: 所有函数必须有完整的类型注解
5.  **Path Handling**: 使用 `pathlib.Path`，**禁止使用 `os.path`**

---

## 8. 知识注册 (Register) - CRITICAL

**这是最容易被遗忘的步骤。每次代码变更后必须检查。**

### 8.1 新增 Feature 时的注册清单

```
□ PRD.md 中已添加 Feature Section (带 <!-- id: feat_xxx --> anchor)
□ .specgraph/features/feat_{name}.yaml 已创建
□ Feature YAML 包含所有必填字段 (id, domain, source_anchor, intent)
□ product.yaml 中 domain 存在且 ID 匹配
```

### 8.2 新增 Component 时的注册清单

```
□ 父 Feature YAML 存在
□ .specgraph/components/comp_{name}.yaml 已创建
□ Component YAML 包含所有必填字段 (id, type, desc, file_path, design)
□ design 包含 api 和 logic
□ 父 Feature YAML 的 realized_by 字段已更新
□ 代码文件路径与 file_path 一致
```

### 8.3 修改代码时的注册清单

```
□ 如果修改了公开 API → 更新 Component YAML 的 design.api
□ 如果修改了核心逻辑 → 更新 Component YAML 的 design.logic
□ 如果新增了常量/模板 → 更新 Component YAML 的 design.constants
```

---

## 9. 可用工具 (Tools)

```bash
# 运行一致性监控
uv run devspec monitor

# 同步图谱到数据库 (实现后可用)
uv run devspec sync

# 查看产品结构树 (实现后可用)
uv run devspec tree
```

---

## 10. 交互示例 (Interaction Example)

**User**: "我想让 devspec monitor 命令显示更详细的进度信息"

**Agent (You)**:

### Phase 1: 理解需求
我理解您的需求是：**增强 `devspec monitor` 命令的输出，显示更详细的执行进度信息，让用户能够了解当前处理到哪个步骤。**

这个理解正确吗？

*[用户确认: 正确]*

### Phase 2: 定位影响
- **涉及 Domain**: dom_cli (CLI Interface)
- **涉及 Feature**: feat_cli_visual_output (基于 Rich 的结构化展示)
- **判断**: 这是修改现有 Feature，进入分支 B

### Phase 3: 评估变更

**Exhaustiveness Check (Component 层)**:
```yaml
exhaustiveness_check:
  level: component
  evaluated:
    - id: comp_cli_monitor
      can_satisfy: true
      reason: "该 Component 负责 monitor 命令实现，可以在此添加进度显示逻辑"
  conclusion: "修改现有 comp_cli_monitor 即可满足需求"
```

**结论**: 修改现有 Component，不需要新增。

### Phase 4: 执行计划

## Spec 变更清单
- [修改] `.specgraph/components/comp_cli_monitor.yaml` - 更新 design.logic 添加进度显示步骤

## 代码变更清单
- [修改] `devspec/cli/monitor.py` - 添加 Rich Progress 组件

## 执行顺序
1. 更新 Component YAML
2. 修改代码实现

是否按此计划执行？
