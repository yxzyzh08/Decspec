# 📘 SpecIndex 2.0 系统架构设计白皮书
**架构模式**：API-Driven Semantic Kernel（API 驱动型语义内核）
**核心机制**：AI 提案 $\rightarrow$ 人类审核 $\rightarrow$ 状态变更
**适用场景**：AI Native 无状态开发流水线

---

## 1. 核心设计哲学 (Core Philosophy)

我们将 SpecIndex 定义为软件系统的**“海马体（Hippocampus）”**。AI 不直接操作长时记忆（直接改文件），而是通过神经接口（API）发送信号。

1.  **接口即法律（Interface as Law）**：
    AI 无法随意生成混乱的文本格式。它必须通过强类型的 API（如 `registerFeature`）与系统交互。API 的参数结构强制了数据的一致性。
2.  **认知双缓冲（Cognitive Double-Buffering）**：
    *   **前台缓冲区（Proposal Layer）**：AI 的修改请求首先进入“暂存区”。
    *   **后台主存储（Truth Layer）**：只有经过人类（超级个体）确认的逻辑，才会写入核心图谱。
3.  **按需构建现实（On-Demand Reality）**：
    由于开发是无状态的，SpecIndex 负责在每次任务开始时，通过 API 动态检索并组装出当前的“世界观”给 AI。

---

## 2. 系统架构组件 (System Architecture)

### 2.1 核心数据库 (The Graph Store)
后端不再仅仅是 Markdown 文件系统，建议采用 **轻量级图数据库**（如 SQLite + Graph 扩展，或 Neo4j）配合 **向量索引**。
*   存储节点：Domain（域）, Feature（特性）, API Signature（签名）。
*   存储边：`DependsOn`（依赖）, `Implements`（实现）, `GuardedBy`（受限于规范）。

### 2.2 认知 API 层 (The Cognitive API Gateway)
这是系统的心脏。它向 AI Agent 暴露一套符合 OpenAPI (Swagger) 标准的工具集 (Tools)。

### 2.3 交互控制台 (The Human Console)
一个可视化的 CLI 或 Web 界面，用于展示 AI 的 **"Call Hierarchy"**（调用层级）和 **"Graph Diff"**（图谱变更），供人类点击“批准/驳回”。

---

## 3. API 协议定义 (The Protocol)

这是 AI 与 SpecIndex 交流的唯一语言。分为 **感知（Read）** 和 **行动（Write/Propose）** 两类。

### 3.1 感知类 API (用于构建上下文)

```typescript
// 1. 获取任务上下文 (核心)
// AI 输入任务描述，系统返回相关的原子特性、依赖和规范
function getFocusContext(taskId: string, userIntent: string): ContextBundle;

// 2. 语义搜索
// 当 AI 发现当前上下文不够用时，主动检索
function searchKnowledge(query: string, type: 'FEATURE' | 'RULE'): Node[];

// 3. 读取契约
// 获取某个特性的详细 I/O 定义
function getFeatureContract(featureId: string): JSONSchema;
```

### 3.2 行动类 API (用于发起提案)

**注意：所有 Write 操作不直接修改数据库，而是生成 `PendingChange`。**

```typescript
// 1. 提案：注册新特性
// 当 AI 分析认为需要新功能时调用
function proposeNewFeature(params: {
    domain: string;
    name: string;
    description: string;
    inputSchema: object;
    outputSchema: object;
}): ProposalID;

// 2. 提案：建立依赖
// 当 AI 编写代码发现需要调用其他模块时调用
function proposeDependency(params: {
    sourceFeatureId: string;
    targetFeatureId: string;
    reason: string; // 必须解释为什么依赖，供人类审核
}): ProposalID;

// 3. 提案：更新契约
// 当业务逻辑变更导致接口变化时调用
function proposeContractChange(params: {
    featureId: string;
    newInputSchema: object;
    breakingChange: boolean; // 是否是破坏性更新
}): ProposalID;
```

---

## 4. 动态工作流 (The Dynamic Workflow)

在这个架构下，开发流程变成了一场**“精密的外科手术”**。

### 阶段一：上下文加载 (Rehydration)
1.  **触发**：超级个体输入任务：“在订单模块增加微信支付功能”。
2.  **系统动作**：
    *   调用 `SpecIndex.search("支付", "订单")`。
    *   检索 `Standards/Payment_Security.spec`（基质规范）。
    *   **组装 Prompt**：将上述信息打包成 JSON 格式的 Context 给 AI。

### 阶段二：思维链与图谱提案 (CoT & Graph Proposal)
**这是与旧方案最大的不同点。**
AI **不先写代码**，而是先规划图谱变更。

1.  **AI 思考**：“我要实现微信支付，这需要一个新的 Feature 节点，并且依赖外部 API。”
2.  **AI 动作 (Function Call)**：
    *   调用 `proposeNewFeature({ name: "WeChatPay", domain: "Order" ... })`。
    *   调用 `proposeDependency({ source: "WeChatPay", target: "LoggingService" })`。
3.  **系统拦截**：
    *   SpecIndex 暂停 AI 执行。
    *   向人类展示：**“AI 请求创建节点 [WeChatPay] 并连接到 [LoggingService]。批准？”**

### 阶段三：人类授权 (Ratification)
1.  **人类动作**：在控制台输入 `Yes` (或点击批准)。
2.  **系统动作**：
    *   将提案写入 Graph Database。
    *   生成该节点的唯一 ID（如 `feat_wx_pay_001`）。
    *   将 ID 返回给 AI。

### 阶段四：代码实现 (Implementation)
1.  **AI 动作**：收到 ID 后，AI 确认“大脑”已建立认知。
2.  **Coding**：AI 生成具体的 TypeScript/Python 代码。
3.  **约束**：代码中的函数名、类名必须与 API 提案中的 `name` 保持一致。

### 阶段五：闭环校验 (Auditor)
1.  **自动化复核**：
    *   扫描 AI 生成的代码。
    *   验证：代码里实际调用的依赖，是否都在 Graph 里声明了？
    *   *如果代码调用了 `UserModule` 但图谱里没连线* $\rightarrow$ **报错，拒绝合并**。

---

## 5. 数据粒度策略 (Granularity Strategy)

依然遵循**“关注点分离”**原则，但通过 API 强制执行。

| 层级 | 管理对象 | API 行为 | 备注 |
| :--- | :--- | :--- | :--- |
| **L1 领域** | 业务模块 | 仅限人类创建 (Admin Only) | AI 不可随意发明新的领域 |
| **L2 原子特性** | 核心逻辑单元 | `proposeNewFeature` | **主要管理层级** |
| **L3 接口签名** | Public API | `proposeContractChange` | AI 可修改，需审核 |
| **L4 实现细节** | Private Method | **无 API** | SpecIndex 彻底忽略，不存储 |
| **基质层** | 日志/安全规范 | `Read Only` | AI 只能读，不能改 |

---

## 6. 关键优势分析

1.  **杜绝“隐式依赖”**：
    在传统开发中，程序员偷偷 import 一个库，没人知道。
    在本系统中，AI 想要 import，必须先调 API `proposeDependency`。如果人类不批，它就没法写那行代码。这是**架构腐化的终极防火墙**。

2.  **结构化思维强植入**：
    强迫 AI 先想“结构（Graph）”再想“细节（Code）”。这符合专家级工程师的思维模式（Top-Down Design）。

3.  **无状态的完美支持**：
    因为所有知识都存在 DB 里并通过 API 存取。哪怕换了一个全新的 AI 模型（比如从 Claude 换成 GPT-5），只要它能理解 Function Calling，就能立刻接手工作，不需要预训练。

---

## 7. 落地建议：第一步做什么？

建议优先开发 **SpecIndex Server (API 后端)**。

1.  定义 `.yaml` 或 `.json` 的 Schema，用来描述 Feature 节点。
2.  写一个简单的 Python/Node 服务：
    *   实现 `POST /propose/feature` (接收 JSON，存入 `pending_changes.json`)。
    *   实现 `GET /context` (根据关键词简单的 grep 搜索)。
3.  不要一开始就上复杂的图数据库，先用 **JSON 文件 + 内存对象** 跑通流程。

---

### 💡 架构师点评

这个设计的精妙之处在于**“权力的反转”**。

通常 AI 工具是用户的“奴隶”，用户说改哪里就改哪里。
在 SpecIndex 2.0 中，**AI 是“施工队”，SpecIndex 是“监理”，而您是“业主”**。

*   施工队（AI）申请：“我要在这个墙上打洞。”（API Call）
*   监理（SpecIndex）记录并上报。
*   业主（您）签字。
*   施工队（AI）才被允许动工。

这确保了在软件高速迭代的过程中，**知识图谱永远是纯净、受控且真实的。**