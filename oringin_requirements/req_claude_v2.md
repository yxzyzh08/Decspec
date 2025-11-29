# SpecIndex 2.0：AI辅助开发知识图谱系统设计规范

> **Software Product Knowledge Graph System Specification**  
> 版本 2.0 | 综合优化版

---

## 1. 设计哲学

### 1.1 核心隐喻：软件的「海马体」

大语言模型如同一个「失忆的天才」——每次对话都是无状态的。SpecIndex 是软件系统的**海马体（Hippocampus）**，负责：

- **长期记忆存储**：持久化软件的功能、依赖、规则
- **上下文重建**：每次任务启动时快速恢复AI的认知
- **记忆保护**：AI不能直接修改记忆，必须通过神经接口（API）

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **接口即法律** | AI必须通过强类型API与系统交互，杜绝格式混乱 |
| **认知双缓冲** | 提案层（暂存）+ 真相层（主存储），人类审核后才写入 |
| **文档先行** | 代码变更前必须更新文档，变更后必须校验一致性 |
| **最小工作量** | 任务必须满足工作量门槛，防止琐碎任务污染系统 |
| **按需构建现实** | 动态检索并组装当前任务的「世界观」给AI |

### 1.3 核心等式

```
SpecIndex = 多层粒度 + 认知双缓冲 + API中介 + 闭环校验 + 工作量证明
```

---

## 2. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        超级个体（Human）                          │
│                     审核 / 批准 / 驳回                            │
└─────────────────────────────────────────────────────────────────┘
                                ▲
                                │ 提案展示
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     提案层（Proposal Layer）                      │
│                   AI的修改请求暂存区                              │
│              PendingChanges / GraphDiff / Audit                 │
└─────────────────────────────────────────────────────────────────┘
                                ▲
                                │ API调用（感知+行动）
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   认知API网关（Cognitive API Gateway）            │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│    │  感知类API   │    │  行动类API   │    │  校验类API   │    │
│    │  (Read)      │    │  (Propose)   │    │  (Verify)    │    │
│    └──────────────┘    └──────────────┘    └──────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                ▲
                                │ 读写
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    真相层（Truth Layer）                          │
│                   知识图谱核心存储                                │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   │
│    │L1 概念层│    │L2 结构层│    │L3 实现层│    │规则+文档│   │
│    └─────────┘    └─────────┘    └─────────┘    └─────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 三层粒度模型

### 3.1 层级总览

| 层级 | 粒度 | 更新频率 | AI权限 | 维护成本 |
|------|------|----------|--------|----------|
| **L1 概念层** | 功能/流程级 | 月级 | 只读 | 低 |
| **L2 结构层** | 接口/类/组件级 | 周级 | 提案修改 | 中（核心层） |
| **L3 实现层** | 函数/文件级 | 日级 | 提案修改 | 低 |
| **跨层：规则** | 约束/规范 | 季度级 | 只读 | 极低 |
| **跨层：文档** | PRD/设计/测试 | 按需 | 提案修改 | 中 |

### 3.2 L1 概念层（Concept Layer）

**定位**：构建AI的「心理模型」，提供任务的宏观框架。

> ⚠️ **铁律**：此层绝不包含任何代码相关内容。AI只能读取，不能提案修改。

**节点类型（3种）**：

| 节点 | 说明 | 示例 |
|------|------|------|
| **Feature** | 用户可感知的功能点 | 「订单管理」「微信支付」 |
| **UserStory** | 用户视角的需求描述 | 「作为买家，我要能取消订单」 |
| **BusinessFlow** | 跨功能的业务流转 | 「下单→支付→发货→收货」 |

**Feature 完整Schema**：

```yaml
Feature:
  id: "feat_order_001"
  title: "订单管理"
  description: "管理用户订单的创建、查询、修改、取消"
  parent_feature_id: null           # 父功能（支持层级）
  dependencies: ["feat_payment"]    # 依赖的其他功能
  maturity_level: "implemented"     # draft → reviewed → implemented → verified
  owner: "zhangsan"                 # 负责人
  created_at: "2024-01-15"
  linked_docs: ["doc_prd_order"]    # 关联文档
  linked_user_stories: ["us_001", "us_002"]
```

### 3.3 L2 结构层（Structural Layer）

**定位**：AI执行任务时的默认上下文来源，是知识图谱的**核心层**。

> ⚠️ **维护重点**：80%的维护精力应投入此层。必须稳定、少变、强结构。

**节点类型（4种）**：

| 节点 | 说明 | 关键属性 |
|------|------|----------|
| **API** | 接口定义 | 路径、方法、参数、返回值、幂等性 |
| **Component** | 前端组件/后端服务 | 职责、输入输出、依赖 |
| **Class** | 核心业务类 | 属性、方法签名、设计模式 |
| **DataModel** | 数据库Schema | 字段、索引、约束、关联 |

**API 完整Schema**：

```yaml
API:
  id: "api_create_order"
  path: "/api/v1/orders"
  method: "POST"
  summary: "创建订单"
  
  # 输入输出契约（JSONSchema格式）
  request_schema:
    type: object
    required: [user_id, items]
    properties:
      user_id: { type: string }
      items: { type: array, items: { $ref: "#/OrderItem" } }
  
  response_schema:
    type: object
    properties:
      order_id: { type: string }
      status: { type: string, enum: [pending, confirmed] }
  
  # 关键属性
  idempotent: false                 # 是否幂等
  auth_required: true               # 是否需要认证
  rate_limit: "100/min"             # 限流规则
  
  # 关联
  implements_feature: "feat_order_001"
  depends_on: ["api_check_inventory", "api_calculate_price"]
  constrained_by: ["rule_order_amount_positive"]
```

### 3.4 L3 实现层（Implementation Layer）

**定位**：提供代码索引，帮助AI定位修改点。

> ⚠️ **铁律**：绝不将完整代码存入图谱，只存结构化摘要（Semantic Index）。

**节点类型（2种）**：

| 节点 | 说明 | 更新方式 |
|------|------|----------|
| **File** | 源文件元信息 | 自动扫描 |
| **FunctionSummary** | 函数签名、用途、副作用 | 自动+人工校验 |

**FunctionSummary 完整Schema**：

```yaml
FunctionSummary:
  id: "fn_createOrder_001"
  name: "createOrder"
  file: "/src/services/order.ts"
  line_range: [45, 120]
  
  # 语义描述（给AI读）
  purpose: "创建新订单并扣减库存"
  
  # 类型签名
  inputs:
    - name: userId
      type: string
      required: true
    - name: items
      type: OrderItem[]
      required: true
  
  output:
    type: Order
    nullable: false
  
  # ⚠️ 副作用声明（关键！）
  side_effects:
    - type: DB_WRITE
      target: orders_table
      description: "插入订单记录"
    - type: DB_WRITE
      target: inventory_table
      description: "扣减库存"
    - type: EVENT_EMIT
      target: OrderCreatedEvent
      description: "发送订单创建事件"
  
  # 调用关系
  calls: [fn_checkInventory, fn_calculatePrice, fn_sendEvent]
  called_by: [fn_checkout, fn_quickBuy]
  
  # 测试覆盖
  test_cases: [test_createOrder_success, test_createOrder_insufficient_stock]
  
  # 版本追踪
  checksum: "a1b2c3d4"              # 代码hash，用于检测变更
  last_verified: "2024-01-20"
```

### 3.5 副作用类型枚举

| 类型 | 说明 | 风险等级 |
|------|------|----------|
| `DB_WRITE` | 写入数据库 | 🔴 高 |
| `DB_READ` | 读取数据库 | 🟢 低 |
| `EVENT_EMIT` | 发送事件/消息 | 🟡 中 |
| `HTTP_CALL` | 发起外部HTTP请求 | 🔴 高 |
| `FILE_IO` | 文件读写操作 | 🟡 中 |
| `STATE_MUTATION` | 修改全局/共享状态 | 🔴 高 |
| `CACHE_WRITE` | 写入缓存 | 🟡 中 |
| `TRANSACTION` | 开启事务 | 🔴 高 |

---

## 4. 跨层节点

### 4.1 规则节点（Rule）

**定位**：记录业务规则、技术规范、安全约束。AI只能读取，不能修改。

```yaml
Rule:
  id: "rule_order_amount_positive"
  type: "Business"                  # Business / Technical / Security
  title: "订单金额必须为正"
  description: "订单总金额必须大于0，且单笔不超过100万"
  
  # 约束表达式（可执行校验）
  expression: "order.amount > 0 && order.amount <= 1000000"
  
  # 约束对象
  constrains:
    - api_create_order
    - api_update_order
  
  # 校验方式
  verification: "Automated"         # Manual / Automated / AI-Check
  
  # 来源
  source: "PRD v2.3 第4.2节"
```

### 4.2 文档节点（Doc）

**定位**：管理PRD、设计文档、测试文档，与代码建立双向链接。

```yaml
Doc:
  id: "doc_prd_order"
  type: "PRD"                       # PRD / Design / Test / API
  title: "订单模块产品需求文档"
  path: "/docs/prd/order.md"
  version: "2.3"
  
  # 内容摘要（给AI快速理解）
  summary: "定义订单的创建、查询、修改、取消流程及业务规则"
  
  # 关联
  related_features: ["feat_order_001"]
  related_apis: ["api_create_order", "api_cancel_order"]
  
  # 版本追踪
  checksum: "e5f6g7h8"
  last_updated: "2024-01-18"
  
  # 变更历史
  changelog:
    - version: "2.3"
      date: "2024-01-18"
      changes: "新增订单取消的退款规则"
```

### 4.3 任务节点（Task）

**定位**：记录每次AI执行任务的输入、输出、工作量证明。

```yaml
Task:
  id: "task_20240120_001"
  title: "实现微信支付功能"
  status: "completed"               # pending → in_progress → completed → verified
  
  # 输入上下文
  input_context:
    features: ["feat_payment"]
    related_docs: ["doc_prd_payment"]
    related_apis: ["api_create_payment"]
    rules: ["rule_payment_security"]
  
  # 输出产物
  output_artifacts:
    docs_changed: ["doc_design_wechat_pay"]
    apis_added: ["api_wechat_callback"]
    functions_added: ["fn_processWechatPayment"]
    tests_added: ["test_wechat_payment_success"]
  
  # ⚠️ 工作量证明（PoW）
  proof_of_workload:
    doc_changes: 1                  # 文档变更数
    api_changes: 1                  # API变更数
    function_changes: 3             # 函数变更数
    test_changes: 2                 # 测试变更数
    meets_threshold: true           # 是否满足最小工作量
  
  # 审计信息
  started_at: "2024-01-20T10:00:00Z"
  completed_at: "2024-01-20T14:30:00Z"
  approved_by: "zhangsan"
```

---

## 5. 边（关系）类型定义

系统定义 **9种核心边类型**。

### 5.1 层内关系

| 边类型 | 连接 | 语义 | 示例 |
|--------|------|------|------|
| `CONTAINS` | L1→L1, L2→L2 | 包含/组成 | Feature → UserStory |
| `DEPENDS_ON` | L2→L2, L3→L3 | 调用/依赖 | ComponentA → API_X |
| `TRIGGERS` | L1→L1, L2→L2 | 触发/引发 | Flow_Login → Flow_Dashboard |

### 5.2 层间关系

| 边类型 | 连接 | 语义 | 示例 |
|--------|------|------|------|
| `IMPLEMENTS` | L2→L1 | 实现 | API_CreateOrder → UserStory_下单 |
| `REALIZED_BY` | L3→L2 | 落地于 | fn_createOrder → API_CreateOrder |
| `DOCUMENTS` | Doc→L1/L2 | 描述 | Doc_PRD → Feature_Order |

### 5.3 约束关系

| 边类型 | 连接 | 语义 | 示例 |
|--------|------|------|------|
| `CONSTRAINED_BY` | L2→Rule | 受规则约束 | API_Withdraw → Rule_每日限额 |
| `VALIDATED_BY` | L2→L3 | 被测试覆盖 | API_CreateOrder → Test_OrderCreation |
| `VERIFIED_BY` | Task→Doc/Code | 任务产出验证 | Task_001 → Doc_Design |

---

## 6. 认知API网关设计

### 6.1 API分类

```
认知API网关
├── 感知类API（Read）     ─→ AI构建上下文
├── 行动类API（Propose）  ─→ AI发起变更提案
└── 校验类API（Verify）   ─→ 闭环校验
```

### 6.2 感知类API（构建上下文）

```typescript
// 1. 获取任务上下文（核心API）
// AI启动任务时调用，系统返回完整的「世界观」
function getTaskContext(params: {
  task_description: string;      // 任务描述
  feature_ids?: string[];        // 指定功能范围（可选）
}): ContextPackage;

// 返回的上下文包
interface ContextPackage {
  // L1：心理模型
  features: Feature[];           // 相关功能
  user_stories: UserStory[];     // 用户故事
  business_flows: BusinessFlow[];// 业务流程
  
  // L2：执行上下文
  apis: API[];                   // 相关API（含契约）
  components: Component[];       // 相关组件
  data_models: DataModel[];      // 数据模型
  
  // L3：代码索引（摘要，非全文）
  functions: FunctionSummary[];  // 函数摘要
  files: FileMeta[];             // 文件元信息
  
  // 约束
  rules: Rule[];                 // 必须遵守的规则
  docs: DocSummary[];            // 文档摘要
  
  // 元信息
  context_token_count: number;   // token估算
  generated_at: string;
}

// 2. 语义搜索
// 当AI发现上下文不够时，主动检索
function searchKnowledge(params: {
  query: string;
  type?: 'FEATURE' | 'API' | 'FUNCTION' | 'RULE' | 'DOC';
  limit?: number;
}): SearchResult[];

// 3. 读取节点详情
function getNode(type: NodeType, id: string): Node;

// 4. 查询依赖图
function getDependencyGraph(node_id: string, depth?: number): Graph;
```

### 6.3 行动类API（发起提案）

> ⚠️ **关键机制**：所有Write操作不直接修改数据库，而是生成`PendingChange`，等待人类审核。

```typescript
// 1. 提案：创建/修改API
function proposeAPIChange(params: {
  action: 'CREATE' | 'UPDATE' | 'DELETE';
  api_id?: string;               // UPDATE/DELETE时必填
  data: Partial<API>;
  reason: string;                // ⚠️ 必须解释原因
  related_task_id: string;
}): ProposalID;

// 2. 提案：建立依赖关系
function proposeDependency(params: {
  source_id: string;
  target_id: string;
  relation_type: EdgeType;
  reason: string;                // ⚠️ 必须解释为什么依赖
}): ProposalID;

// 3. 提案：更新函数摘要
function proposeFunctionChange(params: {
  action: 'CREATE' | 'UPDATE' | 'DELETE';
  function_id?: string;
  data: Partial<FunctionSummary>;
  code_diff?: string;            // 可选：附带代码变更摘要
}): ProposalID;

// 4. 提案：更新文档
function proposeDocChange(params: {
  doc_id: string;
  changes_summary: string;       // 变更摘要
  new_version: string;
}): ProposalID;

// 5. 批量提案（事务性）
function proposeBatch(params: {
  proposals: Proposal[];
  transaction: boolean;          // true = 全部成功或全部失败
  task_id: string;
}): BatchProposalID;
```

### 6.4 校验类API（闭环校验）

```typescript
// 1. 校验代码与图谱一致性
// AI完成编码后调用，检查实际依赖是否都已声明
function validateCodeConsistency(params: {
  task_id: string;
  code_files: string[];          // 变更的文件列表
}): ValidationResult;

interface ValidationResult {
  passed: boolean;
  issues: {
    type: 'UNDECLARED_DEPENDENCY' | 'MISSING_SIDE_EFFECT' | 'DOC_CODE_MISMATCH';
    severity: 'ERROR' | 'WARNING';
    message: string;
    suggestion: string;
  }[];
}

// 2. 校验工作量门槛
function validateWorkload(task_id: string): WorkloadValidation;

interface WorkloadValidation {
  passed: boolean;
  proof: {
    doc_changes: number;
    api_changes: number;
    function_changes: number;
    test_changes: number;
    total_score: number;
    threshold: number;
  };
  rejection_reason?: string;
}

// 3. 校验文档-代码一致性
function validateDocCodeSync(params: {
  doc_id: string;
  related_code_ids: string[];
}): SyncValidation;
```

### 6.5 错误响应规范

API返回的错误必须**对AI友好**：

```typescript
interface APIError {
  code: string;                  // 错误码
  message: string;               // 错误描述
  reason: string;                // 详细原因
  suggestion: string;            // 建议的解决方案
  related_api?: string;          // 相关的修复API
  context?: object;              // 上下文信息
}

// 示例
{
  code: "DEPENDENCY_EXISTS",
  message: "无法删除 API_CreateOrder",
  reason: "以下组件依赖此API: Component_Checkout, Component_OrderList",
  suggestion: "请先调用 proposeDependency 解除依赖关系",
  related_api: "proposeDependency({ action: 'DELETE', ... })",
  context: {
    dependent_nodes: ["Component_Checkout", "Component_OrderList"]
  }
}
```

---

## 7. 动态工作流

### 7.1 五阶段流程

```
┌─────────────────────────────────────────────────────────────┐
│  阶段一：上下文加载（Rehydration）                           │
│  ────────────────────────────────────────────────────────── │
│  1. 超级个体输入任务描述                                     │
│  2. 系统调用 getTaskContext() 组装上下文包                   │
│  3. 上下文包注入AI的System Prompt                            │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段二：图谱规划（Graph Planning）                          │
│  ────────────────────────────────────────────────────────── │
│  ⚠️ AI先规划图谱变更，后写代码                               │
│  1. AI分析任务，确定需要的新节点/边                          │
│  2. AI调用 proposeAPIChange / proposeDependency 等          │
│  3. 系统生成 PendingChanges，展示给人类                      │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段三：人类授权（Ratification）                            │
│  ────────────────────────────────────────────────────────── │
│  1. 控制台展示 GraphDiff（节点/边变更预览）                  │
│  2. 人类审核：批准 / 驳回 / 要求修改                         │
│  3. 批准后，提案写入真相层，生成唯一ID                       │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段四：代码实现（Implementation）                          │
│  ────────────────────────────────────────────────────────── │
│  1. AI收到批准的节点ID，确认「大脑」已建立认知               │
│  2. AI生成具体代码（函数名/类名必须与提案一致）              │
│  3. AI调用 proposeDocChange 同步更新文档                     │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段五：闭环校验（Verification）                            │
│  ────────────────────────────────────────────────────────── │
│  1. 系统调用 validateCodeConsistency 检查依赖声明            │
│  2. 系统调用 validateWorkload 检查工作量门槛                 │
│  3. 系统调用 validateDocCodeSync 检查文档一致性              │
│  4. 全部通过 → 任务完成；失败 → 拒绝合并，返回修改           │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 上下文包组装策略

```typescript
function assembleContextPackage(task: TaskInput): ContextPackage {
  // 1. 解析任务意图，识别关键词
  const keywords = extractKeywords(task.description);
  
  // 2. 检索相关L1节点
  const features = searchFeatures(keywords);
  
  // 3. 获取L1的所有依赖Feature
  const allFeatures = expandDependencies(features);
  
  // 4. 获取关联的L2节点
  const l2Nodes = getImplementingNodes(allFeatures);
  
  // 5. 获取L2的依赖图（深度2层）
  const l2WithDeps = expandL2Dependencies(l2Nodes, depth=2);
  
  // 6. 获取关联的L3摘要（只取摘要，不取代码）
  const l3Summaries = getL3Summaries(l2WithDeps);
  
  // 7. 获取相关规则
  const rules = getConstrainingRules(l2WithDeps);
  
  // 8. 获取相关文档摘要
  const docs = getRelatedDocs(allFeatures);
  
  // 9. Token预算控制
  return compressToTokenBudget({
    features: allFeatures,
    l2_nodes: l2WithDeps,
    l3_summaries: l3Summaries,
    rules,
    docs
  }, maxTokens=8000);
}
```

---

## 8. 最小工作量约束（Proof-of-Workload）

### 8.1 设计目的

防止AI执行「琐碎任务」污染系统，确保每次任务都有实质性产出。

### 8.2 工作量计分规则

| 产出类型 | 分值 | 说明 |
|----------|------|------|
| 新增/修改PRD文档 | 3分 | 需求层变更 |
| 新增/修改设计文档 | 2分 | 设计层变更 |
| 新增API | 3分 | 接口层变更 |
| 修改API契约 | 2分 | 接口变更（非破坏性） |
| 破坏性API变更 | 4分 | 需要处理兼容性 |
| 新增核心函数 | 2分 | 实现层变更 |
| 新增测试用例 | 1分 | 质量保证 |

### 8.3 最小门槛

```yaml
minimum_threshold:
  total_score: 5                 # 总分至少5分
  required_chains: 2             # 至少覆盖2个链条
  
chains:
  - name: "需求链"
    nodes: [PRD, UserStory, Feature]
  - name: "设计链"
    nodes: [DesignDoc, API, Component]
  - name: "实现链"
    nodes: [Function, File]
  - name: "测试链"
    nodes: [TestCase, TestDoc]
```

### 8.4 不合格任务示例

| 任务 | 得分 | 结果 |
|------|------|------|
| 修改按钮文字颜色 | 0分 | ❌ 拒绝 |
| 替换一个字段名 | 1分 | ❌ 拒绝 |
| 新增一个简单API | 3分 | ❌ 拒绝（只覆盖1个链条） |
| 新增API + 测试 + 文档 | 6分 | ✅ 通过 |

---

## 9. 更新机制与变更传播

### 9.1 更新触发条件

| 层级 | 自动触发 | 人工触发 |
|------|----------|----------|
| L3 | 代码commit时自动扫描checksum | — |
| L2 | L3累积变更超阈值时提醒 | 接口变更、重构时 |
| L1 | — | PRD更新、需求评审后 |
| Rule | — | 仅管理员可修改 |

### 9.2 变更传播规则

```typescript
// L3 → L2 传播判断
function shouldPropagateToL2(l3Change: L3Change): boolean {
  // 不传播：内部逻辑优化
  if (l3Change.type === 'INTERNAL_REFACTOR') return false;
  
  // 传播：签名变更
  if (l3Change.signatureChanged) return true;
  
  // 传播：新增副作用
  if (l3Change.newSideEffects.length > 0) return true;
  
  // 传播：删除函数
  if (l3Change.type === 'DELETE') return true;
  
  return false;
}
```

### 9.3 并行开发的图谱分支

```
knowledge-graph/
├── main/                    # 主干图谱（稳定版）
├── branches/
│   ├── feature-wechat-pay/  # 微信支付分支（增量delta）
│   └── feature-refund/      # 退款功能分支
└── proposals/               # 待审核的提案
    ├── pending/
    └── approved/
```

合并策略：
1. 代码合并时同步合并图谱增量
2. 检测节点/边冲突
3. 冲突时人工介入解决

---

## 10. 技术实现方案

### 10.1 存储方案选型

| 阶段 | 方案 | 说明 |
|------|------|------|
| **MVP阶段** | YAML + Git | 零依赖，人类可读，Git天然版本控制 |
| 小团队 | SQLite + JSON | 单文件，支持复杂查询 |
| 规模化 | Neo4j + Redis | 图数据库 + 缓存，支持复杂图遍历 |

### 10.2 推荐目录结构（YAML方案）

```
specindex/
├── graph/                      # 知识图谱核心存储
│   ├── L1/
│   │   ├── features/
│   │   │   └── feat_order.yaml
│   │   ├── user_stories/
│   │   └── flows/
│   ├── L2/
│   │   ├── apis/
│   │   │   └── api_create_order.yaml
│   │   ├── components/
│   │   ├── classes/
│   │   └── data_models/
│   ├── L3/
│   │   ├── files/
│   │   └── functions/
│   ├── rules/
│   └── docs/
├── proposals/                  # 待审核提案
│   ├── pending/
│   │   └── prop_20240120_001.yaml
│   └── history/
├── tasks/                      # 任务记录
│   └── task_20240120_001.yaml
└── config/
    ├── schema.yaml             # 节点/边类型定义
    └── thresholds.yaml         # 工作量门槛配置
```

### 10.3 架构分层

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5: AI Agent 集成层          ～200行胶水代码      │
│  (Claude Tool Use / OpenAI Function Calling)           │
├─────────────────────────────────────────────────────────┤
│  Layer 4: 校验层                   ～300行校验逻辑      │
│  (WorkloadValidator / ConsistencyChecker)              │
├─────────────────────────────────────────────────────────┤
│  Layer 3: 认知API层                ～500行业务逻辑      │
│  (ContextAssembler / ProposalManager / SearchEngine)   │
├─────────────────────────────────────────────────────────┤
│  Layer 2: 基础操作层               ～300行CRUD封装      │
│  (GraphStore / NodeRepository / EdgeRepository)        │
├─────────────────────────────────────────────────────────┤
│  Layer 1: 存储层                   现成，不用写         │
│  (YAML Files + Git / SQLite / Neo4j)                   │
└─────────────────────────────────────────────────────────┘
```

### 10.4 工作量估算

| 阶段 | 工作内容 | 时间 | 产出 |
|------|----------|------|------|
| Week 1 | Schema设计 + YAML模板 | 4天 | 节点/边类型定义 |
| Week 2 | Layer 2 GraphStore | 3天 | 约300行代码 |
| Week 3 | Layer 3 认知API | 5天 | 约500行代码 |
| Week 4 | Layer 4 校验层 | 3天 | 约300行代码 |
| Week 5 | Layer 5 AI集成 + CLI | 4天 | 约200行代码 |
| Week 6 | 测试 + 文档 + 调优 | 5天 | 完整MVP |

> ✅ **结论：一个人，6周，可以做出完整MVP（约1300行核心代码）**

---

## 11. 关键优势总结

| 优势 | 说明 |
|------|------|
| **杜绝隐式依赖** | AI想import必须先调API声明，未声明的依赖无法通过校验 |
| **防止幻觉污染** | API返回什么才算数，AI说什么不重要 |
| **强制结构化思维** | AI先想「图谱结构」再想「代码细节」（Top-Down） |
| **工作量兜底** | PoW机制防止琐碎任务污染系统 |
| **文档-代码一致性** | 闭环校验确保文档与代码同步 |
| **无状态完美支持** | 知识都在DB，换AI模型也能立刻接手 |
| **人类始终掌控** | 认知双缓冲，所有变更需人类批准 |

---

## 附录A：设计原则速查

### 三条铁律

1. **L1绝不含代码**：只有业务概念，AI只读
2. **L3绝不存代码**：只存结构化摘要（Semantic Index）
3. **AI绝不直接写图谱**：只能通过API提案，人类审核后才写入

### 权力模型

```
超级个体（业主）  ──→  最终审批权
      │
      ▼
SpecIndex（监理）──→  记录、校验、拦截
      │
      ▼
AI Agent（施工队）──→  只能提案，不能直接施工
```

### 快速记忆

```
12种节点（3+4+2+3），9种边，3层+跨层

L1（3）：Feature, UserStory, BusinessFlow
L2（4）：API, Component, Class, DataModel
L3（2）：File, FunctionSummary
跨层（3）：Rule, Doc, Task

层内边（3）：CONTAINS, DEPENDS_ON, TRIGGERS
层间边（3）：IMPLEMENTS, REALIZED_BY, DOCUMENTS
约束边（3）：CONSTRAINED_BY, VALIDATED_BY, VERIFIED_BY

五阶段：加载 → 规划 → 授权 → 实现 → 校验
```

---

## 附录B：与三份原始文档的对照

| 特性 | ChatGPT版 | Claude版 | Gemini版 | 本文档 |
|------|-----------|----------|----------|--------|
| 分层模型 | 6层 | 3层 | 4层 | 3层+跨层 ✅ |
| 节点类型 | 5种 | 10种 | 模糊 | 12种 ✅ |
| 边类型 | 未定义 | 7种 | 未定义 | 9种 ✅ |
| 验证层 | ✅ | ❌ | ✅ | ✅ 闭环校验 |
| 工作量证明 | ✅ PoW | ❌ | ❌ | ✅ PoW |
| 认知双缓冲 | 三阶段 | API校验 | ✅ | ✅ 提案层+真相层 |
| 动态工作流 | 基础 | 基础 | ✅ 5阶段 | ✅ 5阶段 |
| 上下文包 | ✅ | 基础 | ✅ | ✅ 完整组装策略 |
| 实现路径 | 模糊 | ✅ 详细 | 基础 | ✅ 6周计划 |
| side_effects | ❌ | ✅ | ❌ | ✅ 8种类型 |

---

*文档版本：v2.0 | 综合优化版*
