# AI辅助开发知识图谱设计规范

> **Knowledge Graph Specification for AI-Assisted Development**  
> 版本 1.0 | 文档状态：设计稿

---

## 1. 概述

### 1.1 设计背景

大语言模型（LLM）在软件开发中展现出强大能力，但存在一个根本性限制：**每次对话都是无状态的**。AI如同一个「失忆的天才」，每次任务都需要重新理解项目背景。

本知识图谱系统的核心目标是构建一个「**外部长期记忆系统**」，让AI在每次任务启动时能够快速、精准地恢复对项目的认知。

### 1.2 核心设计原则

- **多层粒度**：知识图谱采用金字塔式分层结构，不同层级服务于不同的认知需求
- **API化访问**：AI通过标准化API进行增删查改，而非直接操作图谱存储
- **代码即真相**：所有变更必须通过代码逻辑校验，确保图谱一致性
- **文档先行**：代码变更前必须更新文档，变更后必须校验一致性

### 1.3 核心等式

```
知识图谱 = 多层粒度 + 层间映射 + API化访问 + 代码校验
```

---

## 2. 三层粒度模型

知识图谱采用三层架构，每层服务于AI不同阶段的认知需求。

**核心理念**：粒度不是选一个，而是以「多层粒度 + 层间语义映射」来构建稳定性与可扩展性。

| 层级 | 粒度 | 更新频率 | AI用途 | 维护成本 |
|------|------|----------|--------|----------|
| **L1 概念层** | 功能/流程级 | 月级 | 建立产品认知 | 低 |
| **L2 结构层** | 接口/类/组件级 | 周级 | 稳定上下文来源 | 中（主要层） |
| **L3 实现层** | 函数/文件级 | 日级 | 定位代码修改点 | 低 |

### 2.1 L1 概念层（Concept Layer）

**定位**：构建AI的「心理模型」，提供任务的宏观框架。

> ⚠️ **关键约束**：此层绝不包含任何代码相关内容。

**节点类型（3种）**：

1. **Feature（功能）**：产品的核心功能单元
2. **UserStory（用户故事）**：用户视角的需求描述
3. **BusinessFlow（业务流程）**：跨功能的业务流转路径

### 2.2 L2 结构层（Structural Layer）

**定位**：AI执行任务时的默认上下文来源，是知识图谱的**核心层**。

> ⚠️ **维护重点**：80%的维护精力应投入此层。它必须稳定、少变、强结构。

**节点类型（4种）**：

1. **API**：包含路径、方法、参数、返回值的接口定义
2. **Component（组件）**：前端组件或后端服务模块
3. **Class（类）**：核心业务类的定义
4. **DataModel（数据模型）**：数据库Schema或领域模型

### 2.3 L3 实现层（Implementation Layer）

**定位**：提供代码索引，帮助AI定位修改点。

> ⚠️ **关键约束**：绝不将完整代码存入图谱，只存结构化摘要（Semantic Index）。

**节点类型（2种）**：

1. **File（文件）**：源文件的元信息
2. **FunctionSummary（函数摘要）**：函数签名、用途、副作用的结构化描述

### 2.4 规则节点（Rule）——跨层约束

除三层节点外，系统还需要一个**跨层的规则节点**，用于记录业务规则、技术规则和安全规则。

**Rule节点属性**：

| 属性 | 说明 |
|------|------|
| 类型 | Business / Technical / Security |
| 约束对象 | 关联的L2节点列表 |
| 校验方式 | Manual / Automated / AI-Check |
| 来源 | PRD章节或技术规范引用 |

**示例**：
- 订单金额不能为负（Business）
- 所有API必须幂等（Technical）
- 用户数据必须脱敏（Security）

---

## 3. 节点类型总览

系统共定义 **10种节点类型**，确保无论系统多大，图谱都不会爆炸。

| 层级 | 节点类型 | 英文标识 | 说明 |
|------|----------|----------|------|
| L1 | 功能 | Feature | 产品核心功能单元 |
| L1 | 用户故事 | UserStory | 用户视角的需求 |
| L1 | 业务流程 | BusinessFlow | 跨功能的业务路径 |
| L2 | 接口 | API | 含参数、返回值的接口 |
| L2 | 组件 | Component | 前端组件/后端服务 |
| L2 | 类 | Class | 核心业务类 |
| L2 | 数据模型 | DataModel | 数据库Schema |
| L3 | 文件 | File | 源文件元信息 |
| L3 | 函数摘要 | FunctionSummary | 函数签名与副作用 |
| 跨层 | 规则 | Rule | 业务/技术/安全约束 |

---

## 4. 边（关系）类型定义

节点是「名词」，边是「动词」。AI理解系统如何运作，靠的是边。

系统定义 **7种核心边类型**。

### 4.1 层内关系

| 边类型 | 连接 | 语义与示例 |
|--------|------|------------|
| **CONTAINS** | L1→L1, L2→L2 | 包含/组成。如：Feature → UserStory |
| **DEPENDS_ON** | L2→L2 | 调用/依赖。如：ComponentA → API_X |
| **TRIGGERS** | L1→L1, L2→L2 | 触发/引发。如：Flow_Login → Flow_Dashboard |

### 4.2 层间关系

| 边类型 | 连接 | 语义与示例 |
|--------|------|------------|
| **IMPLEMENTS** | L2→L1 | 实现。如：API_CreateOrder → UserStory_下单 |
| **REALIZED_BY** | L3→L2 | 落地于。如：File_order.ts → Class_OrderService |

### 4.3 约束关系

| 边类型 | 连接 | 语义与示例 |
|--------|------|------------|
| **CONSTRAINED_BY** | L2→Rule | 受规则约束。如：API_Withdraw → Rule_每日限额 |
| **VALIDATED_BY** | L2→L3 | 被测试覆盖。如：Component_Form → TestCase_表单校验 |

---

## 5. FunctionSummary 标准化 Schema

L3层的FunctionSummary是AI定位代码修改点的关键。必须采用**标准化结构**，而非自由文本。

### 5.1 完整字段定义

```yaml
FunctionSummary:
  id: "fn_createOrder_001"          # 唯一标识
  name: "createOrder"               # 函数名称
  file: "/src/services/order.ts"    # 所在文件路径
  line_range: [45, 120]             # 起止行号
  
  purpose: "创建新订单并扣减库存"    # 1-3句话描述函数用途（给AI读）
  
  inputs:                           # 输入参数列表
    - name: userId
      type: string
    - name: items
      type: OrderItem[]
  
  output:                           # 返回值类型定义
    type: Order
    nullable: false
  
  side_effects:                     # ⚠️ 副作用声明（关键！）
    - type: DB_WRITE
      target: orders_table
    - type: EVENT_EMIT
      target: OrderCreatedEvent
  
  calls:                            # 调用的其他函数ID列表
    - fn_checkInventory
    - fn_calculatePrice
  
  called_by:                        # 被哪些函数调用
    - fn_checkout
  
  test_cases:                       # 关联的测试用例ID
    - test_createOrder_success
    - test_createOrder_insufficient_stock
```

### 5.2 side_effects 类型枚举

副作用声明是AI最容易踩坑的地方。**显式声明副作用等于给AI画红线**。

| 类型 | 说明 |
|------|------|
| `DB_WRITE` | 写入数据库 |
| `DB_READ` | 读取数据库 |
| `EVENT_EMIT` | 发送事件/消息 |
| `HTTP_CALL` | 发起HTTP外部请求 |
| `FILE_IO` | 文件读写操作 |
| `STATE_MUTATION` | 修改全局/共享状态 |

---

## 6. 更新机制

### 6.1 更新触发条件

| 层级 | 自动触发 | 人工触发 |
|------|----------|----------|
| L3 | 代码commit时自动扫描 | — |
| L2 | L3累积变更超过阈值时提醒 | 接口变更、重构时 |
| L1 | — | PRD更新、需求评审后 |

### 6.2 变更传播规则

当L3发生变化时，系统自动判断是否影响L2：

| L3变更类型 | 是否传播到L2 | 处理方式 |
|------------|--------------|----------|
| 函数内部逻辑优化 | 否 | L2保持不变 |
| 函数签名变更 | 是 | 标记关联L2需审查 |
| 新增副作用 | 是 | 更新side_effects |
| 删除函数 | 是 | 检查L2依赖是否断裂 |

### 6.3 并行开发时的图谱分支

支持并行开发多个小项目时，图谱也需要分支概念：

```
knowledge-graph/
├── main/           # 主干图谱
├── feature-a/      # 项目A的图谱增量（delta）
└── feature-b/      # 项目B的图谱增量
```

合并代码时，同步合并图谱增量，并检测冲突。

---

## 7. API化访问设计

AI不直接操作图谱存储，而是通过标准化API进行增删查改。这在AI和图谱之间插入了一个「**可信中介层**」。

### 7.1 架构对比

```
传统方式:
AI → 直接读写 → 知识图谱存储 (不可控)

API中介方式:
AI → API调用(可审计) → API服务层(可校验) → 知识图谱存储
                        ├── 输入校验
                        ├── 权限控制
                        ├── 事务管理
                        ├── 变更日志
                        └── 联动触发
```

**本质**：用「类型系统+契约」约束AI的自由度。

### 7.2 设计优势

| 优势 | 说明 |
|------|------|
| **防止幻觉污染** | API返回什么才算数，AI说什么不重要 |
| **保证一致性** | 所有写操作必须通过校验逻辑 |
| **可审计追溯** | 每次变更都有日志，可回滚 |
| **事务性操作** | 批量更新要么全成功，要么全失败 |
| **联动自动化** | 传播规则变成代码，无需AI记忆 |

### 7.3 API分层

**高级语义API（AI主要使用）**：

```python
get_task_context(feature_ids)      # 获取任务相关的所有上下文
report_code_change(task_id, changes)  # 报告代码变更
check_impact(node_id)              # 分析修改影响范围
validate_consistency()             # 校验变更与图谱一致性
```

**原子操作API（特殊情况使用）**：

```python
create_node(type, data)
update_node(type, id, changes)
delete_node(type, id)
create_edge(from, to, relation_type)
delete_edge(edge_id)
```

### 7.4 错误处理策略

API返回的错误信息必须**对AI友好**，包含：

```python
Error(
    code="DEPENDENCY_EXISTS",
    message="无法删除API_CreateOrder",
    reason="以下组件依赖此API: Component_Checkout, Component_OrderList",
    suggestion="请先调用 update_component_dependency() 解除依赖关系",
    related_api="update_component_dependency(component_id, old_dep, new_dep)"
)
```

---

## 8. 技术实现方案

### 8.1 存储方案选型

| 方案 | 适用场景 | 说明 |
|------|----------|------|
| **YAML文件 + Git** ⭐ | MVP阶段 | 零依赖，人类可读，Git天然版本控制 |
| SQLite + JSON字段 | 小团队 | 单文件数据库，无需运维 |
| Neo4j | 规模化 | 专业图数据库，复杂查询性能好 |

> 💡 **强烈建议从YAML文件开始**

### 8.2 推荐的目录结构（YAML方案）

每个YAML文件就是一个节点，文件内容包含属性和关系引用：

```
knowledge-graph/
├── L1/
│   ├── features/
│   │   ├── feat_order.yaml
│   │   └── feat_payment.yaml
│   ├── user_stories/
│   └── flows/
│       └── flow_checkout.yaml
├── L2/
│   ├── apis/
│   │   └── api_create_order.yaml
│   ├── components/
│   ├── classes/
│   └── data_models/
├── L3/
│   ├── files/
│   └── functions/
│       └── fn_create_order.yaml
└── rules/
    └── rule_order_limit.yaml
```

### 8.3 架构分层

```
Layer 4: AI集成层        ← 约200行胶水代码
Layer 3: 业务API层       ← 约500-800行业务逻辑（核心）
Layer 2: 基础操作层      ← 约300行CRUD封装
Layer 1: 存储层          ← 现成的，不用写
```

### 8.4 工作量估算

| 阶段 | 工作内容 | 时间 | 产出 |
|------|----------|------|------|
| Week 1 | 设计节点schema + YAML结构 | 3-5天 | 10种节点模板 |
| Week 2 | 实现GraphStore | 2-3天 | 约300行代码 |
| Week 3 | 实现核心GraphAPI | 4-5天 | 约500行代码 |
| Week 4 | AI集成 + 测试 | 4-5天 | 完整MVP |

> ✅ **结论：一个人，一个月，可以做出可用的MVP**

---

## 9. 可行性判断

| 问题 | 回答 |
|------|------|
| 技术上是否可行？ | ✅ 完全可行，没有技术障碍 |
| 是否需要高深技术？ | ❌ 不需要，都是常规CRUD |
| 一个人能做吗？ | ✅ 能，MVP一个月 |
| 最大风险是什么？ | 不是技术，是「设计的抽象是否好用」 |

**关键洞察**：

- ❌ 你不是在「开发一个知识图谱系统」（类似开发Neo4j）
- ✅ 你是在「开发一个知识图谱的应用层」（类似用MySQL开发应用）

**核心工作是「定义业务规则」，不是「实现图数据库」。**

---

## 附录：设计原则速查

### 三条铁律

1. **L1绝不含代码**：只有业务概念
2. **L3绝不存代码**：只存结构化摘要
3. **AI绝不直接写图谱**：只能通过API

### 快速记忆

```
10种节点，7种边，3层结构

L1（3节点）：Feature, UserStory, BusinessFlow
L2（4节点）：API, Component, Class, DataModel
L3（2节点）：File, FunctionSummary
跨层（1节点）：Rule

层内边（3种）：CONTAINS, DEPENDS_ON, TRIGGERS
层间边（2种）：IMPLEMENTS, REALIZED_BY
约束边（2种）：CONSTRAINED_BY, VALIDATED_BY
```

---

*文档版本：v1.0*
