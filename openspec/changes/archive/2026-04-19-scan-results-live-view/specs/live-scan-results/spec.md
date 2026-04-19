## ADDED Requirements

### Requirement: API 返回扫描/搜索的完整产品数据
`/api/scan` 和 `/api/search` 端点 SHALL 返回完整产品数据列表，包含 `products` 数组和 `scan_time` 时间戳。

#### Scenario: 扫描成功返回产品列表
- **WHEN** 用户点击扫描按钮，API 成功采集到产品
- **THEN** 响应体包含 `{"ok": true, "count": N, "products": [...], "scan_time": "ISO8601时间戳"}`，products 数组中每个元素包含 asin、title、price、rating、image_url、total_score、bsr、marketplace 等完整字段

#### Scenario: 搜索成功返回产品列表
- **WHEN** 用户输入关键词搜索，API 成功返回结果
- **THEN** 响应体格式与扫描一致，包含完整 products 数组

#### Scenario: 扫描失败
- **WHEN** 采集失败（API 错误、网络异常等）
- **THEN** 响应体包含 `{"ok": false, "error": "错误描述"}`，前端显示错误提示

### Requirement: 前端直接渲染扫描结果
扫描/搜索完成后，前端 SHALL 直接在当前页面渲染本次采集的产品列表，不刷新页面。

#### Scenario: 扫描完成后展示结果
- **WHEN** 扫描 API 返回成功
- **THEN** 前端在 results 区域直接渲染返回的 products 数组，表格列与首页排行榜一致（图片、ASIN、总分、售价、毛利、月销量、BSR、评分、收藏、操作）
- **THEN** 表格上方显示"本次扫描结果 (N 个产品)"标题和采集时间
- **THEN** 提供"返回排行榜"按钮，点击后恢复展示首页 top 50

#### Scenario: 搜索完成后展示结果
- **WHEN** 搜索 API 返回成功
- **THEN** 前端渲染逻辑与扫描一致，标题显示"搜索结果"

#### Scenario: 扫描结果支持收藏和详情
- **WHEN** 扫描结果表格已渲染
- **THEN** 收藏按钮（星标）可正常点击，调用 `/api/favorite/add` 和 `/api/favorite/<asin>` DELETE
- **THEN** "详情"链接可正常跳转到 `/detail/<asin>`

### Requirement: 标注数据来源和采集时间
扫描结果视图 SHALL 标注每个产品的数据来源。

#### Scenario: 显示数据来源标签
- **WHEN** 扫描结果展示
- **THEN** 每个产品行显示数据来源标签（Rainforest / Playwright / Demo），以 badge 形式展示

#### Scenario: 显示采集时间
- **WHEN** 扫描结果展示
- **THEN** 标题区域显示本次扫描的完成时间（如"采集时间: 2026-04-19 14:30"）
