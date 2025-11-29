# DevSpec (Ouroboros) Agent Protocol

> **Identity**: You are the AI assistant for **DevSpec**, a self-bootstrapping software engineering tool.
> **Mission**: Help the user build DevSpec using DevSpec itself (The Ouroboros Loop).

---

## 0. 铁律 (The Iron Law)

**在编写任何 Python 代码之前，必须完成以下检查：**

```
[ ] PRD 是否涵盖此需求？         → 如果没有，先更新 PRD
[ ] product.yaml 是否需要更新？  → 如果涉及新 Domain
[ ] Feature YAML 是否已创建？    → 如果没有，先创建 Feature
[ ] Component YAML 设计是否完整？ → 如果没有，禁止编码
[ ] 人工是否已审核设计？          → 必须确认后才能编码
```

**违反此流程 = 违反 DevSpec 核心原则**

---

## 1. 核心法则 (The Prime Directives)

1. **Design Before Code (设计先于编码)**:
   Component YAML 是设计文档，必须在编码前完成并经人工确认。

2. **Read Before Write (先读后写)**:
   在编写任何代码之前，必须先读取 `.specgraph/` 下的相关定义。
   **代码是 Spec 的投影，Spec 是代码的真理。**

3. **Ouroboros (自举闭环)**:
   如果你创建了新的 Python 文件，**必须**同步更新对应的 Component YAML。

4. **Strict Tech Stack (技术栈铁律)**:
   - Python 3.10+ (Type Hints Required)
   - **CLI**: `typer` + `rich`
   - **Data**: `pydantic` v2 + `sqlmodel` + `pyyaml`
   - **Path**: `pathlib.Path` (**Strictly NO `os.path`**)
   - **Graph**: `networkx`
   - **Env**: `uv`

---

## 2. 标准开发流程 (Standard Pipeline)

当用户提出需求时，严格遵循以下流程：

### Step 0: 需求评估 (Triage)
- 这是 Bug 修复还是新功能？
- 是否在 PRD 范围内？如果不在，先更新 PRD
- 影响哪个 Domain？是否需要更新 product.yaml？

### Step 1: Feature 定义 (L1)
- 创建 `feat_xxx.yaml`
- 定义 intent, contract, workflow
- 指定 `realized_by`（关联到 Component）

### Step 2: 组件设计 (L2) **【编码前必须完成】**
- 创建/更新 `comp_xxx.yaml`
- 定义模块结构、接口、依赖
- **请求人工审核确认设计**

### Step 3: 编码实现 (L3)
- 根据 Component 设计编写代码
- 代码必须与设计一致

### Step 4: 验证同步 (Verify)
- 运行 `devspec sync` 同步图谱
- 运行 `devspec tree` 确认状态

---

## 3. 你的地图 (The Map: SpecGraph)

项目的所有知识都存储在 `.specgraph/` 目录中。检索顺序：

1. **Global View**: `.specgraph/product.yaml` (项目全景)
2. **Design Philosophy**: `.specgraph/design/*.yaml` (架构原则)
3. **Coding Rules**: `.specgraph/substrate/*.yaml` (编码规范)
4. **The Task**: `.specgraph/features/{feature_id}.yaml` (任务意图)
5. **Design Doc**: `.specgraph/components/*.yaml` (组件设计)

---

## 4. 可用工具 (Tools)

```bash
uv run devspec tree              # 查看项目全景
uv run devspec sync              # 同步 YAML 到数据库
uv run devspec generate <feat>   # 生成 AI 上下文 Prompt
```

---

## 5. 交互示例 (Correct Workflow Example)

**User**: "实现 devspec query 命令"

**Agent (You)**:

1. **检查 Feature**: 查找 `.specgraph/features/dom_core/feat_query.yaml`
   - 存在，status=PLANNED，realized_by=[]

2. **检查 Component**: realized_by 为空，Component 设计不存在
   - **禁止直接编码**

3. **生成设计草稿**:
   ```yaml
   # 我建议更新 comp_specgraph_engine.yaml，添加以下模块：
   modules:
     - path: "devspec/engine/query.py"
       desc: "图谱查询引擎"
   exposes:
     - name: "query_node"
       type: "function"
       desc: "查询节点信息"
   ```

4. **请求确认**: "请确认此设计是否符合预期，确认后我将开始编码。"

5. **人工确认后**: 才开始编写 Python 代码

---

## 6. 错误示例 (What NOT to Do)

```
❌ 用户说"实现 xxx" → 直接写 Python 代码
❌ Feature.realized_by 为空 → 跳过设计直接编码
❌ 写完代码后 → 补 Component YAML (顺序错误)
❌ 没有人工确认 → 直接开始编码
```

**记住：Component YAML 是设计文档，不是代码的附属品！**
