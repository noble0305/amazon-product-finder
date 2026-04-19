# 亚马逊辅助选品系统

数据驱动 + AI 分析的亚马逊产品选择工具。支持多数据源采集、智能评分、趋势监控和数据导入。

## 快速开始

```bash
# 1. 创建虚拟环境 & 安装依赖
cd amazon-product-finder
uv venv .venv
uv pip install -r requirements.txt

# 2. 配置（可选，不配置则使用 demo 模式）
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入 API keys

# 3. 启动 Web 服务
.venv/bin/python src/web.py
# 访问 http://localhost:5002
```

## 功能概览

### 🔍 多榜单扫描
- 🏆 Best Sellers 畅销榜
- 🆕 New Releases 新品榜
- 🚀 Movers & Shakers 飙升榜
- 支持关键词搜索

### 🌍 17 个亚马逊站点
美国 / 英国 / 德国 / 法国 / 日本 / 澳洲 / 加拿大 / 意大利 / 西班牙 / 印度 / 巴西 / 墨西哥 / 新加坡 / 阿联酋 / 荷兰 / 瑞典 / 比利时

### 🔀 双数据源 + 自动降级
| 数据源 | 说明 |
|:---|:---|
| 🌊 Rainforest API | 付费 API，数据精准，32 个品类自动采集 |
| 🕷️ Playwright 直爬 | 免费直爬亚马逊页面，Rainforest 失败时自动降级 |

### 📤 数据导入（商机探测器）
支持从亚马逊后台「商机探测器」导出的数据直接导入：
- **CSV / Excel 文件上传**：拖拽上传，支持 .csv 和 .xlsx
- **表格粘贴导入**：直接复制粘贴数据
- **智能列映射**：中英文字段名自动匹配（ASIN、搜索量、点击份额、转化率等）
- **导入预览**：上传后先预览，确认列映射再入库
- **合并策略**：覆盖 / 合并 / 跳过（同 ASIN 已有数据时）

### 📊 智能评分体系

| 维度 | 权重 | 说明 |
|:---|:---:|:---|
| 需求分 | 35% | BSR 排名、月销量、搜索量（增强） |
| 竞争分 | 30% | 评论数、卖家数、点击份额（增强） |
| 利润分 | 25% | 售价区间、毛利率、FBA 费用占比 |
| 机会分 | 10% | Listing 质量、新品占比、转化率（增强） |

> 有商机探测器数据（搜索量/转化率/点击份额）时，评分算法自动增强。

### 🔔 价格预警 + BSR 监控
- **价格预警**：价格下跌 / 价格上涨 / 低于目标价（自定义阈值）
- **BSR 监控**：排名飙升 / 排名下降（自定义阈值百分比）
- 扫描时自动记录价格和 BSR 快照
- 产品列表快速预警按钮

### ⭐ 收藏夹 + 竞品对比
- 按分组管理收藏产品
- 多产品对比分析
- 价格/BSR 趋势图表

### 🤖 AI 品类报告
- 品类市场概况分析
- 竞争格局评估
- 选品建议

## 技术栈

| 组件 | 技术 |
|:---|:---|
| 后端 | Python Flask |
| 前端 | 内嵌模板（单文件 SPA） |
| 数据库 | SQLite |
| 数据采集 | Rainforest API + Playwright |
| AI 分析 | OpenAI 兼容 API（智谱 GLM） |
| 图表 | Chart.js |
| 测试 | Playwright E2E |

## 项目结构

```
├── config.yaml             # 配置文件
├── config.example.yaml     # 配置模板
├── requirements.txt        # Python 依赖
├── db/products.db          # SQLite 数据库（自动创建）
├── scripts/
│   └── init_db.py          # 数据库管理 + CRUD
├── src/
│   ├── web.py              # Web 服务 + 前端模板（单文件）
│   ├── main.py             # CLI 入口
│   ├── collectors/
│   │   ├── rainforest.py   # Rainforest API 采集器
│   │   └── playwright_scraper.py  # Playwright 直爬采集器
│   ├── analyzer/
│   │   ├── scorer.py       # 评分引擎（含增强评分）
│   │   ├── profit.py       # 利润分析
│   │   └── ai_analyzer.py  # AI 分析
│   ├── models/
│   │   └── product.py      # 数据模型
│   └── utils/
│       └── fba.py          # FBA 费用计算器
└── tests/
    ├── test_e2e.py         # Playwright E2E 测试
    └── screenshot.png      # 测试截图
```

## API 端点

| 端点 | 方法 | 说明 |
|:---|:---:|:---|
| `/api/scan` | GET | 扫描榜单（支持 bestsellers/new_releases/movers_shakers） |
| `/api/search` | GET | 关键词搜索 |
| `/api/categories` | GET | 获取品类列表 |
| `/api/import/upload` | POST | 文件上传导入（CSV/Excel） |
| `/api/import/paste` | POST | 粘贴数据导入 |
| `/api/import/confirm` | POST | 确认导入（列映射 + 合并策略） |
| `/api/alerts` | GET/POST | 价格预警 CRUD |
| `/api/alerts/check` | GET | 检查价格预警触发状态 |
| `/api/bsr-alerts` | GET/POST | BSR 监控 CRUD |
| `/api/bsr-alerts/check` | GET | 检查 BSR 监控触发状态 |
| `/api/favorites` | GET | 获取收藏列表 |
| `/api/favorite/add` | POST | 添加收藏 |
| `/api/favorite/<asin>` | DELETE | 删除收藏 |
| `/api/trend/<asin>` | GET | 获取价格历史 |
| `/api/report/category` | POST | AI 品类报告 |
| `/api/export` | GET | 导出数据 |

## 配置说明

编辑 `config.yaml`：

```yaml
# Rainforest API
rainforest:
  api_key: "YOUR_API_KEY"    # 留空使用 demo 模式
  marketplace: "us"

# AI 分析
ai:
  api_key: "YOUR_API_KEY"
  base_url: "https://aiapis.help/v1"
  model: "gpt-5.4"

# 评分权重（可自定义）
scoring:
  demand_weight: 0.35
  competition_weight: 0.30
  profit_weight: 0.25
  opportunity_weight: 0.10

# 筛选条件
filters:
  min_price: 15
  max_price: 50
  min_reviews: 10
  max_reviews: 2000
  min_rating: 3.5
  max_bsr: 200000
```

## 后续规划

| 阶段 | 内容 | 状态 |
|:---|:---|:---:|
| Phase 1 | 基础功能（扫描/评分/报告） | ✅ |
| Phase 2 | 多站点 + 品类自动采集 + Playwright 数据源 | ✅ |
| Phase 3 | 价格预警 + BSR 监控 | ✅ |
| Phase 3.5 | 商机探测器数据导入 + 增强评分 | ✅ |
| Phase 4 | 供应链分析 / 关键词挖掘 / 评论情感分析 | 📋 |
| Phase 5 | 多用户 / Chrome 插件 / 企微集成 | 📋 |

## License

MIT
