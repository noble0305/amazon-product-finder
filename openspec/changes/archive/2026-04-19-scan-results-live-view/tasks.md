## 1. API 增强 — 返回完整产品数据

- [x] 1.1 修改 `/api/scan` 端点：将 `_run_pipeline` 处理后的 products 序列化为 dict 列表，在响应中返回 `{"ok": true, "count": N, "products": [...], "scan_time": "ISO8601"}`（`src/web.py:1330-1379`）
- [x] 1.2 修改 `/api/search` 端点：同 1.1 逻辑，返回完整 products 数组和 scan_time（`src/web.py:1382-1413`）
- [x] 1.3 为每个产品数据增加 `data_source` 字段标注来源（rainforest / playwright / demo）

## 2. 图片兜底 — 采集器增强

- [x] 2.1 修改 Rainforest `_parse_products` 方法：依次尝试 `item.image`、`item.main_image.link`，取第一个非空值（`src/collectors/rainforest.py:516`）
- [x] 2.2 在 Product 模型中增加 `get_image_url` 属性方法：如果 image_url 为空，拼接 `https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={asin}&Format=_SL250_&ID=AsinImage`（`src/models/product.py`）
- [x] 2.3 修改 Playwright 采集器：若抓取的 image_url 为空，使用 ASIN 拼接 URL（`src/collectors/playwright_scraper.py`）

## 3. 前端 — 扫描结果动态渲染

- [x] 3.1 新增 `renderScanResults(products, scanTime, source)` JS 函数：动态生成结果表格 HTML，替换 results 区域内容（`src/web.py` 内嵌 JS）
- [x] 3.2 结果表格包含：图片（含 onerror 兜底）、ASIN（可点击跳转 Amazon）、总分、售价、毛利、月销量、BSR、评分、数据来源 badge、收藏按钮、详情链接
- [x] 3.3 标题区域显示"本次扫描结果 (N 个产品)"和采集时间
- [x] 3.4 新增"返回排行榜"按钮，点击后调用 `window.location.reload()` 恢复首页 top 50
- [x] 3.5 修改 `doScan()` 函数：移除 `window.location.reload()`，改为调用 `renderScanResults(data.products, data.scan_time, data.source)`
- [x] 3.6 修改 `doSearch()` 函数：同 3.5 逻辑

## 4. 测试验证

- [x] 4.1 验证扫描后页面不刷新，直接展示本次采集结果
- [x] 4.2 验证搜索后页面不刷新，直接展示搜索结果
- [x] 4.3 验证"返回排行榜"按钮恢复首页 top 50
- [x] 4.4 验证图片兜底：Rainforest 无 image 时 fallback 到 ASIN 拼接 URL
- [x] 4.5 验证数据来源 badge 正确展示（Rainforest / Playwright / Demo）
