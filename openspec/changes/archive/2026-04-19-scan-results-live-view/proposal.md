## Why

当前用户点击类目扫描后，系统采集数据写入 DB，然后 `window.location.reload()` 刷新首页，首页固定从 DB 读取 top 50（按 total_score 排序）。这导致三个问题：

1. **无法区分新旧数据**：用户扫描后看到的列表是历史大杂烩，不是本次采集的实时结果
2. **图片大量缺失**：Rainforest API 有时不返回 image 字段，Demo 模式的图片 URL 是虚构的，导致显示 placeholder
3. **数据来源不透明**：Best Sellers 榜单经常 fallback 到搜索结果，但用户无法感知

## What Changes

- 扫描/搜索完成后，不再 `window.location.reload()`，而是前端直接渲染本次 API 返回的产品列表
- 新增 `/api/scan` 和 `/api/search` 返回完整产品数据（含图片、评分、来源标注），而非仅返回 `{"ok": true, "count": N}`
- 前端 JS 新增"扫描结果视图"，展示本次采集的产品，标注数据来源和时间
- 图片兜底策略：Rainforest API 多字段提取 + ASIN 拼接 Amazon 图片 URL 作为 fallback
- 扫描结果视图支持收藏、详情跳转、对比等现有交互功能

## Capabilities

### New Capabilities
- `live-scan-results`: 扫描/搜索完成后在前端直接渲染本次采集的产品列表，无需页面刷新
- `image-fallback`: 多层图片兜底策略，确保产品图片尽可能展示

### Modified Capabilities

## Impact

- **前端 JS** (`src/web.py` 内嵌模板)：扫描/搜索结果渲染逻辑大幅修改，从 reload 改为 AJAX 动态渲染
- **API 端点** (`/api/scan`, `/api/search`)：响应体需返回完整产品数据
- **Rainforest 采集器** (`src/collectors/rainforest.py`)：图片提取逻辑增强
- **Playwright 采集器** (`src/collectors/playwright_scraper.py`)：图片提取逻辑增强
- **首页加载** (`GET /`)：不受影响，仍展示历史 top 50
