# DevSpec：AI原生开发协航系统

> **Product Requirements Document (PRD)**  
> Version 3.0 Final | 代号：Ouroboros (衔尾蛇)

---

## 1. 产品愿景

### 1.1 一句话定义

DevSpec 是专为"超级个体"设计的 **串行会话式智能结对编程环境**。

它既是开发业务软件的工具，也是一个 **可自我进化的生命体** —— 由自己构建，随使用者习惯不断迭代。

### 1.2 核心哲学

| 哲学 | 说明 |
|------|------|
| **串行流** | 单人开发不追求伪并行，追求极致流畅的串行吞吐率 |
| **会话制** | 任务沙箱平衡 Token 成本与上下文连贯性 |
| **递归进化** | 自举开发，吃自己的狗粮（Dogfooding） |
| **用户主权** | 规范服务于人，不适应就改规范，而非强迫适应 |

### 1.3 不做什么

```
❌ 不做强制门禁（阻止提交）
❌ 不做复杂审批流程
❌ 不做并行开发调度
❌ 不做团队协作功能
```

---

## 2. 自举开发策略

这是本项目最核心的实施路径。

### 2.1 三阶段自举

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 0: 人肉编译器 (The Human Compiler)                    │
│  ─────────────────────────────────────────────────────────  │
│  状态：代码量 0，仅有本 PRD                                   │
│  方法：                                                      │
│    • 人类：扮演 Session Manager，手动创建目录/运行脚本        │
│    • AI：扮演 Coder，根据 PRD 生成代码                       │
│  产出：bootstrap.py（YAML读取 + Prompt拼接）                 │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: 脚本辅助 (Script Assisted)                         │
│  ─────────────────────────────────────────────────────────  │
│  状态：有简陋的 CLI 脚本                                      │
│  方法：                                                      │
│    • 用 devspec.py 生成 prompt                              │
│    • 用 prompt 喂 AI，开发更多功能                           │
│    • 用 DevSpec 管理 DevSpec 自己的代码                      │
│  产出：CLI框架 + SQLite索引 + Tree-sitter扫描               │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: 自我闭环 (The Ouroboros Loop)                      │
│  ─────────────────────────────────────────────────────────  │
│  状态：MVP 功能就绪                                          │
│  方法：                                                      │
│    • devspec task start "optimize-xxx"                      │
│    • 工具分析自身代码，生成上下文                             │
│    • AI 优化工具，工具更新自身图谱                            │
│  产出：稳定迭代的工具，可开发外部业务项目                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 自举路线图

| 阶段 | 时间 | 目标 | 验证方式 |
|------|------|------|----------|
| **Day 1** | Phase 0 | 手写 `bootstrap.py`，能读YAML、拼Prompt | 生成Prompt让AI写CLI骨架 |
| **Day 2-3** | Phase 1 | AI完善CLI，实现 `init` 和 `scan` | 为DevSpec源码生成 `.specindex` |
| **Day 4-5** | Phase 2 | 实现 `task start` (Context Builder) | 用devspec开发devspec的新模块 |

### 2.3 自举风险控制

| 风险 | 应对 |
|------|------|
| **过度优化工具** | 原则：只有业务开发痛不欲生时才改工具，能用就行 |
| **自举死循环** | 保留 git 回滚能力，可手动回退到 Phase 0 修复 |
| **规范不适应** | 宽松模式 + force commit，随时可绕过 |

---

## 3. AI能力边界

在设计前必须明确AI的真实能力：

### 3.1 AI擅长（可放心交给AI）

| 能力 | 可靠度 |
|------|--------|
| 单文件代码生成 | ⭐⭐⭐⭐⭐ |
| 代码补全和修改 | ⭐⭐⭐⭐⭐ |
| 测试用例生成 | ⭐⭐⭐⭐ |
| 文档生成 | ⭐⭐⭐⭐ |

### 3.2 AI不擅长（需人类主导）

| 能力 | 可靠度 | 应对 |
|------|--------|------|
| 跨文件重构 | ⭐⭐ | 人工拆解为小任务 |
| 架构决策 | ⭐⭐ | 人工决策，AI执行 |
| 自我纠错 | ⭐⭐ | 测试驱动验证 |
| 业务正确性 | ⭐ | 人工Review |

---

## 4. 核心功能模块

### 4.1 模块总览

```
DevSpec
├── M1: 知识图谱引擎 (SpecIndex)     ← P0 必须
├── M2: 上下文装配器 (Context)       ← P0 必须
├── M3: 会话管理器 (Session)         ← P1 重要
├── M4: 质量卫士 (Guard)             ← P2 可选
└── M5: 需求池 (Backlog)             ← P2 可选
```

---

### M1: 知识图谱引擎 (SpecIndex)

#### 核心能力

| 能力 | 说明 |
|------|------|
| 双模态存储 | YAML（Git管理）+ SQLite（运行时缓存） |
| 三层索引 | L1概念层、L2结构层、L3实现层 |
| 自动扫描 | Tree-sitter扫描代码，自动更新L3 |
| 依赖查询 | 节点关系、影响分析 |

#### 分层自动化

| 层 | 维护方式 | 说明 |
|----|----------|------|
| **L3** | 全自动 | Tree-sitter扫描，无需人工 |
| **L2** | 半自动 | 代码提取+人工确认 |
| **L1** | 人工 | AI建议，人工定义 |

#### 节点类型（简化版）

```yaml
# 6种核心节点
Feature:       功能定义（L1）
API:           接口契约（L2）
Component:     组件定义（L2）
DataModel:     数据模型（L2）
Function:      函数摘要（L3，自动生成）
Substrate:     基质规范（全局）
```

#### 边类型（简化版）

```yaml
# 2种边 + reason字段
HARD: 强依赖（必须存在）
SOFT: 弱关联（可选）
```

#### CLI命令

```bash
devspec init              # 初始化 .specindex 目录
devspec init --scan       # 初始化 + 扫描现有代码生成L3
devspec scan              # 增量扫描代码更新L3
devspec query <node_id>   # 查询节点
devspec deps <node_id>    # 查询依赖
devspec impact <node_id>  # 影响分析
```

---

### M2: 上下文装配器 (Context Builder)

#### 核心能力

| 能力 | 说明 |
|------|------|
| 关注气泡 | 根据任务抓取最小充分上下文 |
| Token控制 | 控制上下文大小在预算内 |
| 剪贴板直连 | Prompt自动写入剪贴板 |

#### 关注气泡内容

```
Focus Bubble 包含：
├── 目标节点：当前要开发的功能
├── 依赖契约：依赖的接口签名（不含实现）
├── 基质规范：相关的全局规范
└── 相关文档：PRD摘要
```

#### CLI命令

```bash
devspec context <node_id>           # 生成上下文并显示
devspec context <node_id> --copy    # 生成上下文并复制到剪贴板
```

---

### M3: 会话管理器 (Session Manager)

#### 核心能力

| 能力 | 说明 |
|------|------|
| 任务沙箱 | task start → task commit 闭环 |
| 上下文保持 | 任务内保持，结束后清空 |
| 需求打包 | 启动时提示合并相关小需求 |

#### 会话生命周期

```
task start "xxx"
    │
    ├── 加载上下文到剪贴板
    ├── 记录任务开始时间
    └── 锁定当前分支状态
    │
   开发中（多轮对话）
    │
task commit
    │
    ├── 触发L3自动扫描
    ├── 运行测试（如配置）
    ├── 提交代码
    └── 清空会话上下文
```

#### CLI命令

```bash
devspec task start "feature-name"   # 开始任务
devspec task status                 # 查看当前任务状态
devspec task commit                 # 提交并结束任务
devspec task abort                  # 放弃当前任务
```

---

### M4: 质量卫士 (Quality Guard)

#### 渐进式约束

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| **宽松模式** | 只警告，允许强行提交 | 快速迭代期 |
| **严格模式** | 阻止不合规提交 | 稳定期 |

#### 配置方式

```yaml
# .devspec/config.yaml
strictness: loose    # loose | strict
```

#### 测试驱动一致性

```
原则：测试通过 = 一致
流程：AI写代码 → AI写测试 → 测试通过 → 验证完成
```

#### CLI命令

```bash
devspec audit              # 运行一致性检查
devspec audit --fix        # 检查并尝试自动修复
devspec commit --force     # 强制提交（宽松模式）
```

---

### M5: 需求池 (Backlog)

#### 核心理念

```
❌ 不暂停代码任务
✅ 暂存需求，智能打包
```

#### 工作流

```
日常：随时往需求池扔想法
  "改按钮颜色" → backlog
  "加个日志" → backlog

启动任务时：
  devspec task start "登录功能"
  系统提示："有3个相关小需求，要一起处理吗？"
```

#### CLI命令

```bash
devspec backlog add "需求描述"      # 添加需求
devspec backlog list                # 查看需求池
devspec backlog pack <task>         # 打包相关需求到任务
```

---

## 5. 关键用户旅程

### J0: 自举迭代

**场景**：觉得DevSpec的上下文构建太慢，想优化它

```bash
# Step 1: 启动任务
$ devspec task start "optimize-context-speed"
✓ 分析 DevSpec 代码依赖...
✓ 上下文已复制到剪贴板 (约 3.2K tokens)
  包含: context_builder.py, query_engine.py, 2个依赖接口

# Step 2: 粘贴给AI，获取优化代码

# Step 3: 更新代码后审计
$ devspec audit
✓ L3 索引已更新 (3个函数变更)
✓ 测试通过 (12/12)
⚠ 建议更新 API 文档 (可选)

# Step 4: 提交
$ devspec task commit
✓ 代码已提交
✓ 知识图谱已更新
✓ 会话已清空
```

### J1: 业务开发

**场景**：开发一个支付模块

```bash
# Step 1: 初始化业务项目的知识图谱
$ cd my-business-project
$ devspec init --scan
✓ 扫描到 45 个源文件
✓ 生成 L3 索引 (128 个函数)
✓ 生成 L2 草稿 (建议 12 个 API 节点)

# Step 2: 补充L1/L2定义
$ vim .specindex/features/feat_payment.yaml

# Step 3: 启动开发任务
$ devspec task start "payment-api"
✓ 上下文已复制到剪贴板

# Step 4: 正常开发流程...
```

---

## 6. 目录结构

```
project/
├── .devspec/                    # 运行时配置
│   ├── config.yaml              # strictness, etc.
│   ├── session/                 # 当前会话状态
│   └── backlog.yaml             # 需求池
│
├── .specindex/                  # 知识图谱
│   ├── features/                # L1 功能定义
│   │   └── feat_xxx.yaml
│   ├── apis/                    # L2 接口定义
│   │   └── api_xxx.yaml
│   ├── substrate/               # 基质规范
│   │   └── sub_logging.yaml
│   └── .runtime/                # 运行时缓存 (.gitignore)
│       └── index.db
│
├── src/                         # 源代码
└── tests/                       # 测试
```

---

## 7. 技术规范

### 7.1 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| CLI | Typer |
| 代码解析 | Tree-sitter |
| 存储 | SQLite + PyYAML |
| 剪贴板 | pyperclip |

### 7.2 性能目标

| 指标 | 目标 |
|------|------|
| 上下文构建 | < 500ms |
| 增量扫描 | < 2s |
| 查询响应 | < 100ms |

---

## 8. MVP定义

### 8.1 MVP必须有（Day 1-5）

```
✅ bootstrap.py（Phase 0 产物）
✅ M1 基础功能：init, scan, query
✅ M2 基础功能：context --copy
✅ CLI框架（Typer）
```

### 8.2 MVP之后（按需迭代）

```
⏳ M3 会话管理：task start/commit
⏳ M4 质量卫士：audit
⏳ M5 需求池：backlog
⏳ 多语言支持（目前只支持Python）
```

---

## 9. 成功指标

| 指标 | 目标 | 衡量方式 |
|------|------|----------|
| 上下文准备时间 | 减少80% | 对比手动整理 |
| 自举闭环 | Day 5达成 | 能用devspec开发devspec |
| 日常使用 | 不觉得烦 | 主观感受 |

---

## 附录A：核心原则速查

```
1. 串行不并行 —— 一个任务做完再做下一个
2. 会话隔离 —— 任务内保持上下文，结束后清空
3. 自动化优先 —— L3全自动，L2半自动，L1人工
4. 测试即一致 —— 测试通过就是文档代码一致
5. 宽松起步 —— 先宽松模式，稳定后再严格
6. 能用就行 —— 不过度优化工具本身
```

---

## 附录B：Phase 0 启动清单

```bash
# Day 1 要做的事

# 1. 创建项目目录
mkdir devspec && cd devspec

# 2. 创建基础结构
mkdir -p devspec .specindex/features .devspec

# 3. 创建 bootstrap.py（手写或让AI生成）
# 功能：读取YAML + 拼接Prompt + 复制到剪贴板

# 4. 创建 DevSpec 自身的第一个 Feature 定义
# .specindex/features/feat_specindex.yaml

# 5. 验证：运行 bootstrap.py 生成 Prompt
python bootstrap.py --feature feat_specindex

# 6. 把 Prompt 粘贴给 AI，让它生成 CLI 骨架
```

---

*Version 3.0 Final*  
*Status: Ready for Phase 0*  
*Next Action: 创建项目目录，开始 Day 1*
