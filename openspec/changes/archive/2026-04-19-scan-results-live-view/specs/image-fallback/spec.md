## ADDED Requirements

### Requirement: 多层图片兜底策略
系统 SHALL 对每个产品的 image_url 实施三层兜底策略，确保图片尽可能展示。

#### Scenario: Rainforest API 返回 image 字段
- **WHEN** Rainforest API 的产品数据中包含 `image` 字段且非空
- **THEN** 使用该字段作为 image_url

#### Scenario: Rainforest API 返回 main_image 字段
- **WHEN** `image` 字段为空，但 `main_image.link` 字段存在且非空
- **THEN** 使用 `main_image.link` 作为 image_url

#### Scenario: ASIN 拼接 Amazon 图片 URL
- **WHEN** 前两层均未获取到有效图片
- **THEN** 使用 ASIN 拼接 Amazon 图片 URL：`https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={asin}&Format=_SL250_&ID=AsinImage`

#### Scenario: 所有兜底均失败
- **WHEN** 三层兜底均未获取到有效图片
- **THEN** 前端 onerror 回退到 placeholder 图片

### Requirement: 图片字段在采集器中增强提取
Rainforest 和 Playwright 采集器 SHALL 尝试从多个字段提取图片 URL。

#### Scenario: Rainforest 采集器提取图片
- **WHEN** 解析 Rainforest API 响应
- **THEN** 依次尝试 `item.image`、`item.main_image.link`，取第一个非空值作为 image_url

#### Scenario: Playwright 采集器提取图片
- **WHEN** 解析 Playwright 抓取结果
- **THEN** 优先使用产品卡片中的 `img src`，若为空则使用 ASIN 拼接 URL
