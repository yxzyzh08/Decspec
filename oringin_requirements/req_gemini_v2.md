### 🚀 终极融合版设计文档

**文档名称**：SpecIndex：AI 原生研发认知操作系统
**版本**：3.0 (Final Synthesis)
**核心定义**：一个基于 API 驱动、采用提案审核机制、以契约（Contract）为核心的动态知识图谱系统。

---

## 1. 核心架构哲学：权力的游戏

我们不构建“图书馆”，我们构建“立法与行政机构”。

1.  **双重状态机 (Dual State Machine)**：
    *   图谱不仅仅记录“当前是什么 (Current State)”，更重要的是管理“这是否被允许 (Pending Proposal)”。
2.  **基质与实体分离 (Substrate vs. Entity)**：
    *   业务功能是“实体”，切面规范（日志、安全）是“基质”。实体在基质之上生长。
3.  **负熵流 (Negative Entropy Flow)**：
    *   AI 倾向于混乱（熵增），SpecIndex 通过强制 API 格式和人工审核（麦克斯韦妖）强制做功，维持系统的有序性。

---

## 2. 数据模型：认知三明治 (The Cognitive Sandwich)

融合 Claude 的分层结构与 Gemini 的基质概念。

### 2.1 垂直业务层 (The Vertical Graph)

*   **L1 领域 (Domain)**：`User`, `Order`, `Payment`。
*   **L2 原子特性 (Atomic Feature) —— [核心锚点]**
    *   这是 AI 能够“理解”的最小业务单元。
    *   **Schema 定义**：
        ```yaml
        Feature:
          id: "feat_user_login"
          domain: "User"
          intent: "允许用户通过手机号登录"
          contract: # 输入输出契约
            input: { phone: string, code: string }
            output: { token: string }
          dependencies: # 显式依赖
            - target: "feat_sms_verify"
              type: "HARD_LINK"
          linked_assets: # 关联资产索引
            doc: "docs/login.spec.md"
            test: "tests/login.test.ts"
        ```
*   **L3 实现索引 (Implementation Index)**
    *   **不存代码，只存签名**。
    *   包含 **Side Effects（副作用）** 声明（采纳 Claude 建议）：`DB_WRITE`, `API_CALL`。

### 2.2 水平基质层 (The Substrate)

*   **定义**：全局强制规范，不作为节点参与连线，而是作为**环境上下文**。
*   **内容**：`Standards/Logging.yaml`, `Standards/ErrorHandling.yaml`。
*   **作用**：当 AI 处理 Backend 任务时，系统自动注入 Logging 规范。

---

## 3. 核心机制：API 驱动的提案系统

这是 SpecIndex 的心脏。AI 绝不直接修改 YAML 文件，必须通过 API。

### 3.1 读：动态上下文构建 (The Focus Bubble)

当任务启动时，系统调用 `SpecIndex.getContext(task)`，返回：
1.  **Target Spec**：当前任务的 Feature 定义。
2.  **Dependency Interface**：所有依赖节点的接口签名（**而非实现**）。
3.  **Active Substrate**：当前适用的基质规范（如：仅注入日志规范，不注入 UI 规范）。

### 3.2 写：提案-审核协议 (Proposal Protocol)

AI 的每一次“写”操作，在 SpecIndex 看来都是一次“立法提案”。

*   **Step 1: AI 提案**
    *   Call `SpecIndex.proposeChange({ type: 'ADD_DEPENDENCY', from: 'A', to: 'B' })`
*   **Step 2: 系统拦截**
    *   SpecIndex 挂起 AI 线程。
    *   在控制台输出 Diff，并请求人类确认。
*   **Step 3: 人类授权**
    *   超级个体点击 `[Approve]`。
*   **Step 4: 状态提交**
    *   系统更新底层存储（YAML），并返回 `SUCCESS` 给 AI。

---

## 4. 关键特性：工作量证明与审计

采纳 ChatGPT 的建议，防止 AI 进行低价值的“假忙碌”。

### 4.1 最小工作量阈值 (Workload Threshold)
*   **机制**：在任务启动前，SpecIndex 评估任务的“图谱影响范围”。
*   **规则**：
    *   如果只是修改 UI 颜色（无图谱变动） $\rightarrow$ 标记为 **Trivial Task**，存入暂存区，积累一批后批量执行。
    *   如果涉及 L2 接口变更 $\rightarrow$ 标记为 **Critical Task**，立即启动完整流程。

### 4.2 审计机器人 (The Auditor)
*   **机制**：在代码提交前，运行一个基于 AST（抽象语法树）的静态分析器。
*   **校验逻辑**：
    *   *“代码里调用了 `Logger.info`，请问 `Standards/Logging.yaml` 里允许吗？”*
    *   *“代码里 import 了 `PaymentService`，请问 `feat_user_login` 的 `dependencies` 列表里声明了吗？”*
*   **结果**：如果未声明就调用，**构建失败**。

---

## 5. 存储与实现路线图 (Implementation Path)

为了兼顾“人类可读”与“机器可读”，我们采用 **Git-backed Graph**。

### 5.1 物理存储
*   **文件格式**：YAML。
*   **目录结构**：
    ```text
    spec_index/
    ├── .graph_meta/       # 自动生成的图索引（JSON，加速查询）
    ├── substrate/         # 基质层
    │   └── logging.yaml
    └── features/          # 业务层 (按 Domain 文件夹分类)
        └── user/
            ├── login.yaml # 包含 Feature 定义 + L3 签名 + 依赖
            └── register.yaml
    ```

### 5.2 软件栈推荐
*   **后端**：FastAPI (Python) 或 NestJS (Node)。
*   **解析器**：Tree-sitter (用于从代码中自动提取 L3 签名)。
*   **向量库**：ChromaDB (用于模糊搜索 "那个处理订单退款的功能")。

---

## 6. 开发者工作流 (The Super-Individual Loop)

这就是您未来的日常开发模式：

1.  **立项**：您告诉工具：“我要做微信支付”。
2.  **解析**：工具调用 SpecIndex，发现没有相关 Feature。
3.  **提案**：AI 调用 `proposeFeature`。**您批准**。
4.  **规范**：AI 生成 `docs/payment.md`。**您审核**。
5.  **编码**：SpecIndex 注入 `Order` 上下文 + `Logging` 基质。AI 写代码。
6.  **审计**：SpecIndex 扫描代码，发现 AI 偷偷引用了 User 表（未声明依赖）。**报警，拒绝提交**。
7.  **修正**：AI 重新申请 `proposeDependency` 或修改代码。
8.  **完成**：图谱更新，代码合入。

---

### 架构师总结

这份设计文档彻底解决了您最初的担忧：

1.  **粒度问题**：通过 L2 原子特性 + L3 签名摘要，既不模糊也不爆炸。
2.  **无状态问题**：API 动态构建“关注气泡”，每次只给 AI 最需要的 5% 上下文。
3.  **一致性问题**：提案机制 + AST 审计，确保图谱永远是代码的“上级”。

**这是为您这位“超级个体”量身打造的数字外骨骼。**