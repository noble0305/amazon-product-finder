## Context

当前项目是一个 Flask 单文件 SPA 应用（`src/web.py`，~86KB），所有前端 HTML/JS/CSS 内嵌在 Python 文件中。

扫描/搜索的数据流：
1. 前端调用 `/api/scan` 或 `/api/search`
2. 后端采集数据 → 评分 → 写入 DB → 返回 `{"ok": true, "count": N}`
3. 前端收到后 `window.location.reload()` 刷新首页
4. 首页 `GET /` 从 DB 读 top 50 展示

这个流程的核心问题是：用户无法看到"刚才采集了什么"，只能看到历史 top 50。

## Goals / Non-Goals

**Goals:**
- 扫描/搜索完成后，前端直接渲染本次采集的产品列表（不刷新页面）
- API 返回完整产品数据，前端无需再次查询 DB
- 图片尽可能展示，多层兜底
- 标注数据来源（Rainforest / Playwright / Demo）和采集时间

**Non-Goals:**
- 不重构为前后端分离架构（保持单文件 SPA）
- 不修改首页历史 top 50 展示逻辑
- 不修改数据库 schema
- 不做扫描历史记录功能

## Decisions

### 1. API 返回完整产品数据而非仅 count

**选择**：`/api/scan` 和 `/api/search` 返回 `{"ok": true, "count": N, "products": [...], "scan_time": "..."}`

**替代方案**：扫描后前端再调 `/api/products?scan_id=xxx` 查询本次结果

**理由**：
- 数据已经在内存中（`_run_pipeline` 处理后），直接返回省掉一次 DB 查询
- 不需要引入 scan_id 概念（避免改 DB schema）
- 前端逻辑更简单：一次请求拿到所有数据

### 2. 前端新增"扫描结果"视图

**选择**：在现有 results 区域内动态渲染，替换首页 top 50 表格

**替代方案**：弹窗 / 新 Tab 展示结果

**理由**：
- 用户习惯在当前页面看结果，弹窗会打断流程
- 复用现有的表格样式和交互（收藏、详情跳转）
- 加一个"返回排行榜"按钮让用户切回 top 50

### 3. 图片兜底三层策略

**选择**：
1. Rainforest API 的 `item.image` 字段
2. Rainforest API 的 `item.main_image.link` 字段
3. 拼接 Amazon 图片 URL：`https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={asin}&Format=_SL250_&ID=AsinImage`

**替代方案**：用 placeholder 图片

**理由**：ASIN 拼接 URL 在 Amazon 侧有较高可用性，即使前两个来源都失败，第三层仍有很大概率能展示图片。

### 4. 保持 scan 到 DB 的写入流程不变

**选择**：扫描结果既返回给前端，也继续写入 DB（`save_products` + `save_price_snapshot`）

**理由**：保持数据持久化，用户后续在首页仍能看到这些产品。

## Risks / Trade-offs

- **API 响应体积增大** → 扫描返回产品数据（~48 个产品），JSON 约 50-100KB，可接受
- **单文件 SPA 体积继续增长** → web.py 已经 86KB，本次新增 JS 约 3-5KB，在可控范围内
- **Demo 模式图片仍是虚构 URL** → 第三层兜底（ASIN 拼接）对 Demo ASIN 无效，Demo 模式下部分图片仍为 placeholder，这是预期行为
