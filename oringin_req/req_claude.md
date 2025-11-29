# SpecIndex：软件产品知识管理系统设计规范

> **Software Product Knowledge Management System**  
> Version 2.0 Final | Infrastructure Design Document

---

## 1. 系统定义

### 1.1 是什么

**SpecIndex** 是一个面向 AI 原生开发模式的 **"无头语义数据库（Headless Semantic Database）"**。

它作为软件产品的 **"可信事实源（Single Source of Truth）"**，解决以下核心问题：

| 问题 | 解决方案 |
|------|----------|
| AI无状态，每次都要重新理解项目 | **记忆外挂**：瞬时构建精准上下文 |
| 文档与代码容易脱节 | **逻辑一致性**：结构化契约 + 自动校验 |
| 知识库与代码分支不同步 | **分支跟随**：YAML文件纳入Git管理 |

### 1.2 系统边界

```
✅ 本设计包含（IN SCOPE）：
   • 数据存储架构（YAML + SQLite）
   • 元数据模型定义（Schema）
   • 知识图谱拓扑与算法
   • 读写 API（Query / Mutation / Audit）
   • 数据一致性校验

❌ 本设计不包含（OUT OF SCOPE）：
   • AI Agent 执行逻辑
   • 任务调度与工作量评估
   • IDE 插件或图形化界面
```

---

## 2. 核心架构：Git原生双模态

系统采用 **"文件即真理，数据库即缓存"** 的双层存储策略。

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Git Version Control                        │
│                   (分支切换时知识库自动同步)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 1: 持久层 (Cold Storage Truth)                │
│                         YAML Files                              │
│  ────────────────────────────────────────────────────────────── │
│  • 人类可读，Diff友好                                            │
│  • Git版本控制，跟随代码分支                                     │
│  • Source of Truth                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Index Syncer (单向同步)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 2: 运行时层 (Hot Runtime Cache)               │
│                    SQLite + NetworkX                            │
│  ────────────────────────────────────────────────────────────── │
│  • 毫秒级查询响应                                                │
│  • 全文搜索 + 图遍历                                             │
│  • 衍生品，放入 .gitignore                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 3: API网关 (Cognitive Gateway)                │
│                         FastAPI                                 │
│  ────────────────────────────────────────────────────────────── │
│  • Query API：构建上下文                                         │
│  • Mutation API：变更提案                                        │
│  • Audit API：一致性校验                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    [ External: AI Agent / User ]
```

### 2.2 数据流向

```
写入：External → API(Mutation) → YAML文件 → Syncer → SQLite
读取：External → API(Query) → SQLite/NetworkX → 返回结果
```

**铁律**：
- ✅ 所有写操作 → 最终写入 YAML 文件
- ✅ 所有读操作 → 从 SQLite/NetworkX 读取
- ❌ 绝不直接写 SQLite（它是衍生品）

---

## 3. 三层粒度模型

### 3.1 层级总览

```
┌─────────────────────────────────────────────────┐
│  L1 概念层 (Concept)                            │
│  ─────────────────────────────────────────────  │
│  WHY：为什么做？                                 │
│  节点：Feature (功能)                            │
│  更新频率：月级                                  │
└─────────────────────────────────────────────────┘
                      │
                      │ IMPLEMENTS (实现)
                      ▼
┌─────────────────────────────────────────────────┐
│  L2 结构层 (Structure)        ← 核心层          │
│  ─────────────────────────────────────────────  │
│  WHAT：做什么？                                  │
│  节点：API, Component, DataModel                 │
│  更新频率：周级                                  │
│  维护重点：80%精力在此层                         │
└─────────────────────────────────────────────────┘
                      │
                      │ REALIZED_BY (落地于)
                      ▼
┌─────────────────────────────────────────────────┐
│  L3 实现层 (Implementation)                     │
│  ─────────────────────────────────────────────  │
│  HOW：怎么做？                                   │
│  节点：FunctionSummary                          │
│  更新频率：日级（自动扫描）                      │
│  注意：只存摘要，不存代码                        │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  基质层 (Substrate) - 环境上下文                 │
│  ─────────────────────────────────────────────  │
│  全局规范：日志、安全、错误码等                  │
│  不作为图谱节点，而是"宪法"                      │
│  按 Domain/Tags 自动注入上下文                   │
└─────────────────────────────────────────────────┘
```

### 3.2 设计原则

| 原则 | 说明 |
|------|------|
| **L1不含代码** | 只有业务概念，无技术细节 |
| **L2是核心** | 稳定、结构化、80%维护精力 |
| **L3不存代码** | 只存结构化摘要（签名+副作用） |
| **L3自动维护** | Tree-sitter扫描，无需人工 |
| **基质是宪法** | 全局规范，只读注入 |

---

## 4. 节点类型定义

### 4.1 节点总览（6种）

| 层级 | 节点类型 | ID前缀 | 说明 |
|------|----------|--------|------|
| L1 | Feature | `feat_` | 用户可感知的功能点 |
| L2 | API | `api_` | HTTP接口定义 |
| L2 | Component | `comp_` | 前端组件/后端服务 |
| L2 | DataModel | `model_` | 数据库Schema |
| L3 | FunctionSummary | `fn_` | 函数签名与副作用 |
| 基质 | Substrate | `sub_` | 全局规范（日志/安全/错误码） |

### 4.2 L1: Feature（功能）

```yaml
# .specindex/features/OrderDomain/feat_create_order.yaml

meta:
  id: feat_create_order
  type: Feature
  domain: OrderDomain
  status: IMPLEMENTED          # DRAFT | PROPOSED | IMPLEMENTED

intent:
  title: 创建订单
  summary: |
    用户将购物车商品生成订单，扣减库存，等待支付。
    包含地址选择、优惠券使用、价格计算等子流程。

# 验收标准
acceptance:
  - 选择商品后点击下单，生成订单
  - 库存不足时提示并阻止下单
  - 订单创建后跳转到支付页面

# 关系
dependencies:
  - target: feat_inventory
    type: HARD                 # HARD=强依赖 | SOFT=弱关联
    reason: 需要检查并扣减库存
  - target: feat_payment
    type: SOFT
    reason: 创建后跳转支付

# 关联的L2节点（实现此Feature的接口/组件）
implemented_by:
  - api_create_order
  - comp_order_form

# 元信息
created_at: "2024-01-15"
updated_at: "2024-01-20"
owner: zhangsan
tags: [核心功能, 交易]
```

### 4.3 L2: API（接口）

```yaml
# .specindex/apis/OrderDomain/api_create_order.yaml

meta:
  id: api_create_order
  type: API
  domain: OrderDomain
  status: IMPLEMENTED

intent:
  title: 创建订单接口
  summary: 创建新订单并扣减库存

# 接口契约
contract:
  path: /api/v1/orders
  method: POST
  
  input:
    user_id: String
    items: List<OrderItem>
    address_id: String
    coupon_id: String?         # ?表示可选
    
  output:
    order_id: String
    order_no: String
    total_amount: Decimal
    status: Enum[pending_payment]
    
  errors:
    - code: INSUFFICIENT_STOCK
      message: 库存不足
    - code: INVALID_ADDRESS
      message: 收货地址无效

  # ⚠️ 副作用声明（关键）
  side_effects:
    - DB_WRITE: orders
    - DB_WRITE: inventory
    - EVENT_EMIT: OrderCreatedEvent

  # 接口属性
  auth: required
  idempotent: false
  rate_limit: 100/min

# 关系
dependencies:
  - target: api_check_inventory
    type: HARD
    reason: 检查库存
  - target: api_get_address
    type: HARD
    reason: 获取收货地址

implements: feat_create_order

# 元信息
version: "1.2"
created_at: "2024-01-15"
updated_at: "2024-01-20"
```

### 4.4 L2: Component（组件）

```yaml
# .specindex/components/OrderDomain/comp_order_form.yaml

meta:
  id: comp_order_form
  type: Component
  domain: OrderDomain
  category: frontend           # frontend | backend

intent:
  title: 订单表单组件
  summary: 订单确认页面的表单，展示商品、地址、支付方式

# 组件接口
contract:
  props:
    - name: cartItems
      type: List<CartItem>
      required: true
    - name: onSubmit
      type: Function
      required: true
      
  emits:
    - name: order-created
      payload: { order_id: String }
      
  slots:
    - name: footer
      description: 底部自定义区域

# 关系
dependencies:
  - target: comp_address_selector
    type: HARD
    reason: 选择收货地址
  - target: api_create_order
    type: HARD
    reason: 提交订单

implements: feat_create_order

# 物理位置
file_path: /src/components/order/OrderForm.vue

# 元信息
created_at: "2024-01-16"
updated_at: "2024-01-19"
```

### 4.5 L2: DataModel（数据模型）

```yaml
# .specindex/models/OrderDomain/model_order.yaml

meta:
  id: model_order
  type: DataModel
  domain: OrderDomain

intent:
  title: 订单数据模型
  summary: 订单表的数据库Schema定义

# 表定义
contract:
  table_name: orders
  database: mysql
  
  fields:
    - name: id
      type: BIGINT
      primary: true
      auto_increment: true
      
    - name: order_no
      type: VARCHAR(32)
      unique: true
      nullable: false
      comment: 订单编号
      
    - name: user_id
      type: VARCHAR(64)
      nullable: false
      index: true
      
    - name: total_amount
      type: DECIMAL(10,2)
      nullable: false
      
    - name: status
      type: TINYINT
      nullable: false
      default: 0
      comment: "0-待支付 1-已支付 2-已发货 3-已完成 4-已取消"
      
    - name: created_at
      type: DATETIME
      nullable: false
      default: CURRENT_TIMESTAMP

  indexes:
    - name: idx_user_id
      columns: [user_id]
    - name: idx_status_created
      columns: [status, created_at]

# 关系
used_by:
  - api_create_order
  - api_query_orders

# 元信息
created_at: "2024-01-10"
updated_at: "2024-01-15"
```

### 4.6 L3: FunctionSummary（函数摘要）

> ⚠️ 此层由 **Tree-sitter** 自动扫描生成，人工只需校验，无需手写。

```yaml
# .specindex/functions/OrderDomain/fn_create_order.yaml

meta:
  id: fn_create_order
  type: FunctionSummary
  domain: OrderDomain
  auto_generated: true         # 标记为自动生成

# 代码位置
location:
  file: /src/services/order.ts
  line_range: [45, 120]
  signature_hash: a1b2c3d4     # 用于检测代码变更

# 语义摘要
intent:
  summary: |
    创建新订单的核心函数。
    验证库存 → 计算价格 → 创建记录 → 扣减库存 → 发送事件。

# 类型签名
contract:
  signature: "async createOrder(userId: string, items: OrderItem[], addressId: string): Promise<Order>"
  
  inputs:
    - name: userId
      type: string
    - name: items
      type: OrderItem[]
    - name: addressId
      type: string
      
  output:
    type: Order
    nullable: false

  # ⚠️ 副作用声明（关键）
  side_effects:
    - type: DB_WRITE
      target: orders
    - type: DB_WRITE
      target: inventory
    - type: EVENT_EMIT
      target: OrderCreatedEvent
    - type: TRANSACTION
      scope: full_function

  throws:
    - InsufficientStockError
    - InvalidAddressError

# 调用关系（自动扫描）
calls:
  - fn_check_inventory
  - fn_calculate_price
  - fn_deduct_inventory
  
called_by:
  - fn_checkout
  - fn_quick_buy

# 实现关系
realizes: api_create_order

# 元信息
last_scanned: "2024-01-20T10:30:00Z"
```

### 4.7 基质层: Substrate（全局规范）

> 基质不是图谱节点，而是 **"环境上下文（Ambient Context）"**，按需注入。

```yaml
# .specindex/substrate/sub_logging.yaml

meta:
  id: sub_logging
  type: Substrate
  category: infrastructure     # infrastructure | security | convention

intent:
  title: 日志规范
  summary: 全系统的日志格式与级别标准

# 规范内容
spec:
  format: JSON
  required_fields:
    - timestamp
    - level
    - trace_id
    - message
    
  levels:
    DEBUG: 开发调试信息
    INFO: 业务关键节点
    WARN: 可恢复异常
    ERROR: 不可恢复异常
    
  examples:
    - level: INFO
      message: "Order created"
      context: { order_id: "xxx", user_id: "yyy" }

# 注入规则：哪些Domain/Tags需要遵守此规范
inject_to:
  domains: ["*"]               # 所有Domain
  tags: []
  
# 元信息
version: "1.0"
updated_at: "2024-01-01"
```

### 4.8 副作用类型枚举

| 类型 | 说明 | 风险 |
|------|------|------|
| `DB_READ` | 读取数据库 | 🟢 低 |
| `DB_WRITE` | 写入数据库 | 🔴 高 |
| `CACHE_READ` | 读取缓存 | 🟢 低 |
| `CACHE_WRITE` | 写入缓存 | 🟡 中 |
| `EVENT_EMIT` | 发送事件/消息 | 🟡 中 |
| `HTTP_CALL` | 外部HTTP请求 | 🔴 高 |
| `FILE_IO` | 文件读写 | 🟡 中 |
| `STATE_MUTATION` | 修改全局状态 | 🔴 高 |
| `TRANSACTION` | 数据库事务 | 🔴 高 |

---

## 5. 边（关系）类型

### 5.1 简化设计

只有 **2种边类型** + **reason字段**，兼顾简洁与语义：

| 边类型 | 说明 | 示例 |
|--------|------|------|
| `HARD` | 强依赖，必须存在 | API调用另一个API |
| `SOFT` | 弱关联，可选/参考 | 文档关联、触发关系 |

### 5.2 YAML表示

```yaml
dependencies:
  - target: api_check_inventory
    type: HARD
    reason: 创建订单前必须检查库存    # reason字段承载语义
    
  - target: feat_payment
    type: SOFT
    reason: 订单创建后跳转支付页面
```

### 5.3 层间关系

层间关系用专门字段表示：

```yaml
# L1 Feature 中
implemented_by:
  - api_create_order
  - comp_order_form

# L2 API 中
implements: feat_create_order
realized_by:
  - fn_create_order

# L3 Function 中
realizes: api_create_order
```

---

## 6. 目录结构

```
project_root/
├── src/                          # 源代码
├── docs/                         # 项目文档
│
├── .specindex/                   # 📁 知识图谱根目录
│   │
│   ├── config.yaml               # 全局配置
│   │
│   ├── schema/                   # Pydantic Schema（校验用）
│   │   ├── feature.py
│   │   ├── api.py
│   │   └── ...
│   │
│   ├── substrate/                # 基质层（全局规范）
│   │   ├── sub_logging.yaml
│   │   ├── sub_security.yaml
│   │   └── sub_error_codes.yaml
│   │
│   ├── features/                 # L1 概念层
│   │   ├── OrderDomain/
│   │   │   └── feat_create_order.yaml
│   │   └── UserDomain/
│   │       └── feat_login.yaml
│   │
│   ├── apis/                     # L2 接口
│   │   └── OrderDomain/
│   │       └── api_create_order.yaml
│   │
│   ├── components/               # L2 组件
│   │   └── OrderDomain/
│   │       └── comp_order_form.yaml
│   │
│   ├── models/                   # L2 数据模型
│   │   └── OrderDomain/
│   │       └── model_order.yaml
│   │
│   ├── functions/                # L3 函数摘要（自动生成）
│   │   └── OrderDomain/
│   │       └── fn_create_order.yaml
│   │
│   └── .cache/                   # ⚠️ 运行时缓存（.gitignore）
│       ├── index.db              # SQLite
│       └── graph.pickle          # NetworkX序列化
│
├── .gitignore                    # 包含 .specindex/.cache/
└── specindex.yaml                # 项目级配置
```

### 配置文件

```yaml
# specindex.yaml

spec_root: .specindex
runtime_dir: .specindex/.cache

domains:
  - OrderDomain
  - UserDomain
  - PaymentDomain

scan:
  source_dirs:
    - src/
  languages:
    - typescript
    - python
  ignore_patterns:
    - "**/*.test.ts"
    - "**/node_modules/**"

sync:
  auto_on_startup: true
  watch_changes: false           # 生产环境建议关闭
```

---

## 7. SQLite 索引层

### 7.1 表结构

```sql
-- 节点表
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,              -- feat_create_order
    type TEXT NOT NULL,               -- Feature / API / Component / ...
    layer TEXT NOT NULL,              -- L1 / L2 / L3 / Substrate
    domain TEXT,                      -- OrderDomain
    
    file_path TEXT NOT NULL,          -- YAML文件路径
    file_hash TEXT NOT NULL,          -- 用于增量同步
    
    content JSON NOT NULL,            -- YAML完整内容
    
    -- 冗余字段（加速查询）
    title TEXT,
    status TEXT,
    summary TEXT,                     -- 用于全文搜索
    
    -- 时间戳
    created_at TEXT,
    updated_at TEXT,
    synced_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 边表
CREATE TABLE edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,               -- HARD / SOFT
    reason TEXT,                      -- 关系说明
    
    PRIMARY KEY (source_id, target_id, type)
);

-- 代码签名表（Tree-sitter扫描结果）
CREATE TABLE signatures (
    id TEXT PRIMARY KEY,              -- fn_create_order
    node_id TEXT,                     -- 关联的节点ID
    file_path TEXT NOT NULL,
    func_name TEXT NOT NULL,
    signature_hash TEXT NOT NULL,     -- 快速检测代码变更
    line_range TEXT,                  -- JSON: [start, end]
    
    last_scanned TEXT
);

-- 索引
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_layer ON nodes(layer);
CREATE INDEX idx_nodes_domain ON nodes(domain);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_signatures_file ON signatures(file_path);
```

### 7.2 全文搜索

```sql
-- FTS5虚拟表
CREATE VIRTUAL TABLE nodes_fts USING fts5(
    id, title, summary,
    content='nodes'
);
```

---

## 8. 核心组件

### 8.1 Index Syncer（海马体同步器）

**职责**：将YAML数据同步到SQLite，并维护代码签名。

**触发时机**：
- 系统启动
- Git分支切换（post-checkout hook）
- YAML文件变更

**工作流**：

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Purge (可选)                                       │
│  如果 force=true，清空 .cache/index.db                       │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Load YAML                                          │
│  • 遍历 .specindex/**/*.yaml                                │
│  • Pydantic Schema 校验                                     │
│  • 写入 nodes 表和 edges 表                                  │
│  • 增量模式：对比 file_hash，只更新变化的文件                 │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Scan Code (Tree-sitter)                            │
│  • 扫描 src/ 目录                                           │
│  • 提取所有 Public Function 签名                             │
│  • 更新 signatures 表                                        │
│  • 生成/更新 L3 FunctionSummary YAML                         │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Build Graph                                        │
│  • 加载 edges 表到 NetworkX DiGraph                          │
│  • 序列化到 .cache/graph.pickle                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Query Engine（查询引擎）

**双引擎架构**：

| 引擎 | 职责 | 场景 |
|------|------|------|
| SQLite | 属性查询、全文搜索 | `list_nodes(type='API')` |
| NetworkX | 图遍历、依赖分析 | `get_dependencies(depth=3)` |

**核心方法**：

```python
class QueryEngine:
    
    def get_node(self, node_id: str) -> Node | None:
        """获取单个节点"""
        
    def list_nodes(self, 
                   type: str = None,
                   layer: str = None,
                   domain: str = None) -> list[Node]:
        """按条件查询节点"""
        
    def search(self, query: str) -> list[Node]:
        """全文搜索"""
        
    def get_dependencies(self, 
                         node_id: str, 
                         depth: int = 3,
                         type: str = None) -> DependencyTree:
        """获取依赖树（向外）"""
        
    def get_dependents(self,
                       node_id: str,
                       depth: int = 3) -> DependentTree:
        """获取被依赖树（向内）"""
        
    def get_impact(self, node_id: str) -> ImpactAnalysis:
        """影响分析：修改此节点会影响谁"""
```

---

## 9. API 接口设计

### 9.1 Query API（构建上下文）

```
GET /context/bubble
────────────────────────────────────────
获取"关注气泡"：返回最小且充分的知识切片

Params:
  - focus_node_id: string (可选)
  - query: string (可选，语义搜索)
  - depth: int (默认2)

Response:
{
  "target": { ... },              // 目标节点完整定义
  "dependencies": [ ... ],        // 直接依赖（只含签名，不含实现）
  "substrate": [ ... ],           // 相关的基质规范
  "related_docs": [ ... ]         // 关联文档路径
}
```

```
GET /context/search
────────────────────────────────────────
语义搜索

Params:
  - q: string
  - type: string (可选，过滤节点类型)
  - limit: int (默认20)

Response:
{
  "nodes": [ ... ]
}
```

```
GET /context/dependencies/{node_id}
────────────────────────────────────────
获取依赖树

Params:
  - depth: int (默认3)
  - direction: "out" | "in" | "both"

Response:
{
  "root": "api_create_order",
  "dependencies": {
    "api_create_order": ["api_check_inventory", "api_get_address"],
    "api_check_inventory": ["fn_check_stock"]
  }
}
```

```
GET /context/impact/{node_id}
────────────────────────────────────────
影响分析

Response:
{
  "node": "model_order",
  "total_impact": 12,
  "by_layer": {
    "L1": ["feat_order"],
    "L2": ["api_create_order", "api_query_order"],
    "L3": ["fn_create_order", "fn_query_order"]
  }
}
```

### 9.2 Mutation API（变更提案）

```
POST /mutation/node
────────────────────────────────────────
创建或更新节点

Body:
{
  "action": "CREATE" | "UPDATE" | "DELETE",
  "type": "Feature" | "API" | ...,
  "id": "feat_xxx",                // UPDATE/DELETE时必填
  "data": { ... }                  // CREATE/UPDATE时必填
}

Response:
{
  "success": true,
  "node_id": "feat_xxx",
  "diff_preview": "..."            // YAML变更预览
}
```

```
POST /mutation/edge
────────────────────────────────────────
创建或删除边

Body:
{
  "action": "CREATE" | "DELETE",
  "source_id": "api_create_order",
  "target_id": "api_check_inventory",
  "type": "HARD",
  "reason": "创建订单前必须检查库存"
}
```

### 9.3 Audit API（一致性校验）

```
POST /audit/verify
────────────────────────────────────────
校验代码与图谱的一致性（用于CI/CD）

Body:
{
  "changed_files": ["/src/services/order.ts"]
}

Response:
{
  "passed": false,
  "violations": [
    {
      "severity": "ERROR",
      "code": "UNDECLARED_DEPENDENCY",
      "message": "Code calls 'PaymentService' but dependency not declared",
      "file": "/src/services/order.ts",
      "line": 45,
      "suggestion": "Add dependency to api_create_order.yaml"
    }
  ]
}
```

```
POST /audit/sync
────────────────────────────────────────
触发同步

Body:
{
  "force": false,                  // true=全量重建
  "scan_code": true                // 是否扫描代码
}

Response:
{
  "success": true,
  "nodes_updated": 5,
  "signatures_scanned": 120,
  "duration_ms": 350
}
```

---

## 10. 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **语言** | Python 3.11+ | |
| **Web框架** | FastAPI | 高性能异步API |
| **数据校验** | Pydantic V2 | Schema定义 + 校验 |
| **文件处理** | PyYAML / ruamel.yaml | 读写YAML（保留注释） |
| **数据库** | SQLite + SQLModel | 轻量级ORM |
| **代码解析** | Tree-sitter | 多语言AST提取 |
| **图计算** | NetworkX | 内存图算法 |
| **CLI** | Typer | 命令行工具 |

---

## 11. 实现计划

| 阶段 | 内容 | 时间 | 产出 |
|------|------|------|------|
| **Week 1** | Schema设计 + YAML模板 | 3天 | 6种节点Pydantic模型 |
| **Week 2** | Index Syncer | 3天 | YAML→SQLite同步 |
| **Week 3** | Tree-sitter集成 | 2天 | 代码签名扫描 |
| **Week 4** | Query Engine | 2天 | SQLite + NetworkX查询 |
| **Week 5** | FastAPI接口 | 3天 | 完整REST API |
| **Week 6** | Audit + CLI | 2天 | 一致性校验 + 命令行 |

**总计**：约 1000 行核心代码，6 周完成 MVP

---

## 附录：快速参考

### 节点类型

```
L1: Feature
L2: API, Component, DataModel
L3: FunctionSummary (自动生成)
基质: Substrate (环境上下文)
```

### 边类型

```
HARD = 强依赖（必须存在）
SOFT = 弱关联（可选/参考）
+ reason字段承载具体语义
```

### ID前缀

```
feat_  → Feature
api_   → API
comp_  → Component
model_ → DataModel
fn_    → FunctionSummary
sub_   → Substrate
```

### 副作用类型

```
DB_READ, DB_WRITE, CACHE_READ, CACHE_WRITE,
EVENT_EMIT, HTTP_CALL, FILE_IO, STATE_MUTATION, TRANSACTION
```

### 数据流

```
Write: API → YAML文件 → Syncer → SQLite
Read:  API → SQLite/NetworkX
```

---

*Version 2.0 Final | Infrastructure Design Document*
