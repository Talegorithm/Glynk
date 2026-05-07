# Timetrack 架构说明

Timetrack 是 Glynk 生态中一个独立且完整的时间追踪模块，遵循**前后端分离**架构，与 Glynk 的核心知识库（Entities / Units / Anchors）逻辑隔离。

## 1. 核心业务概念

- **Tag (标签)**：代表追踪的项目或分类（如“阅读”、“编码”）。每个 Tag 包含唯一的 ID、名称、自定义颜色以及排序权重。
- **Session (会话/时间块)**：具体的一次追踪记录。包含绑定的 Tag、开始时间、结束时间（如果为空则代表正在进行中）以及可选的文字备注（Remark）。

## 2. 后端架构 (Python + FastAPI)

后端代码主要集中在 `glynk/timetrack/` 目录下。

### 2.1 数据库结构 (`db.py`)
使用 PostgreSQL 存储，提供底层的 CRUD 操作：
- **表 `tt_tags`**：存储 `id`, `entity_id` (归属用户), `name`, `color`, `sort_order`。
- **表 `tt_sessions`**：存储 `id`, `entity_id`, `tag_id`, `start_time`, `end_time`, `note`。
- **特定业务逻辑**：
  - **4:00 AM 业务日**：在 `get_today_stats` 中，日期的划分线被设定为凌晨 4:00，即通过 `(CURRENT_TIMESTAMP - INTERVAL '4 hours')::date + INTERVAL '4 hours'` 逻辑来判定“今天”。

### 2.2 路由 API (`router.py`)
提供标准的 RESTful 接口供前端调用：
- `GET /timetrack/tags` / `POST` / `PUT` / `DELETE`：标签的增删改查。
- `POST /timetrack/tags/reorder`：批量更新标签排序。
- `GET /timetrack/sessions/active`：获取当前正在计时（`end_time IS NULL`）的会话。
- `POST /timetrack/sessions/{tag_id}/start`：开始新计时（可选 `single_mode` 自动结束其他计时）。
- `POST /timetrack/sessions/{session_id}/stop`：结束计时。
- `PUT /timetrack/sessions/{session_id}/note`：更新运行中或已完成会话的备注。
- `POST /timetrack/sessions/past`：手动补录过去的专注记录。
- `DELETE /timetrack/sessions/{session_id}`：删除一条历史日志。
- `GET /timetrack/stats`：查询指定日期区间的原始 Session 列表，供前端汇总图表或日志流水账。
- `GET /timetrack/stats/today`：按标签聚合计算今天的总时长，用于主页的快速展示。

### 2.3 数据模型 (`models.py`)
定义了 Pydantic 模型（如 `TagCreate`, `SessionResponse`），用于 FastAPI 的请求校验与响应序列化。

---

## 3. 前端架构 (React + Zustand)

前端代码深度集成在 Glynk Web 项目中，主要位于 `glynk-web/src/pages/Timetrack/` 等相关目录。

### 3.1 状态管理 (`store/timetrack.ts`)
使用 **Zustand** 构建全局状态，确保多页面数据同步与交互的连贯性：
- 维护 `tags`, `activeSessions`, `todayStats` 以及全局的 `singleMode` 设置。
- 提供封装好的异步 Action（如 `startSession`, `addPastSession`, `reorderTags`），内部调用 API 并自动触发关联状态刷新，保证 UI 最新。

### 3.2 页面视图
前端采取了带有顶部导航栏的布局 `TimetrackLayout.tsx`，下辖三大核心视图：

#### 1. 计时器主页 (`index.tsx`)
- **交互逻辑**：采用经典的基于触控优化的交互。
  - **短按**：切换计时状态（开始/停止）。
  - **长按**：唤起聚合弹窗 (`modal`)。
    - **活跃标签长按**：用于添加/修改当前计时的备注（Remark）。
    - **非活跃标签长按**：用于“补录”（Log Past Session），用户输入时长（默认30分钟）和备注后自动计算并插入历史记录。
  - **拖拽**：在编辑模式下，支持重新拖拽排布标签位置。
- **指针事件拦截**：底层使用原生的 `onPointerDown`/`onPointerUp`/`onPointerCancel` 来精准区分长按与短按，规避了由于手指滑动触发 `Cancel` 而导致误判的交互隐患。

#### 2. 日志流水账 (`Logs.tsx`)
- **动态加载与按天切分**：沿用 4:00 AM 的切分逻辑展示详细的历史清单。
- **高密度 UI 设计**：采取自适应的 Compact 布局。无备注的情况下仅占一行，极大地节省纵向空间；有备注则优雅地换行并与标签对齐。
- **快速筛选与管理**：提供按标签 (Tag) 或 有无备注 (With Remark) 的组合筛选功能；并支持单条数据的快捷删除。

#### 3. 统计视图 (`Stats.tsx`)
- 利用 Recharts 等图表库，提供可视化的饼图（Pie Chart）与汇总列表。
- 支持 天 (Day) / 周 (Week) / 月 (Month) 的多维度查看与前后翻页。前端动态计算时间范围，传参给后端 `get_stats` API，然后前端处理归类聚合。

## 4. 总结
Timetrack 模块的设计非常内聚：它没有复杂的嵌套结构和角色权限，完全由用户自身的 Entity 进行横向的数据隔离。通过基于指针的极简触碰交互和底层精准的 4AM 逻辑，提供了一个极其符合个人专注流和补录习惯的独立工作台。
