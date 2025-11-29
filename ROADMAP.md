# 🗺️ DevSpec 自举路线图 (Phase 1)

## 🟢 已完成 (Done)
- [x] **M0: CLI 骨架** (`feat_cli_structure`)
- [x] **M1: 数据库同步引擎** (`feat_specindex_sync`)
  - [x] 定义 DataModel (Node/Edge)
  - [x] 实现 YAML -> SQLite 同步逻辑

## 🟡 进行中 (In Progress: dom_core)
> 目标：让 SpecGraph 能读懂代码，并能回答查询。

- [ ] **M1.2: L3 代码扫描器 (Tree-sitter)**  <-- **(当前的卡点)**
  - [ ] 定义 `feat_l3_scanner.yaml`
  - [ ] 编写 Python 代码集成 tree-sitter
  - [ ] 验证扫描 `devspec` 自身代码生成 L3 节点
  
- [ ] **M1.3: 图谱查询 API**
  - [ ] 定义 `feat_graph_query.yaml`
  - [ ] 实现 `devspec query <id>`
  - [ ] 实现 `devspec deps <id>` (依赖分析)

## ⚪ 待办 (Backlog)
- [ ] **M2: 上下文装配器** (`feat_context_builder`)
- [ ] **M3: 会话管理** (`feat_session_manager`)