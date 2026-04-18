# 亚马逊辅助选品系统

数据驱动 + AI 分析的亚马逊产品选择工具。

## 快速开始

```bash
# 1. 安装依赖
cd amazon-product-finder
uv pip install -r requirements.txt

# 2. 配置（可选，不配置则使用 demo 模式）
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入 API keys

# 3. 运行 demo（无需 API key）
python -m src.main scan --category "Home & Kitchen" --pages 2

# 4. 查看结果
python -m src.main report --top 20

# 5. 导出报告
python -m src.main export --top 20
```

## 命令说明

| 命令 | 说明 | 示例 |
|:---|:---|:---|
| `scan` | 扫描品类 Best Sellers | `python -m src.main scan --category "Home & Kitchen" --pages 2` |
| `search` | 关键词搜索 | `python -m src.main search --keyword "garlic press"` |
| `report` | 查看 Top 产品 | `python -m src.main report --top 20` |
| `export` | 导出 Markdown 报告 | `python -m src.main export --top 20` |
| `analyze` | 深度分析单个产品 | `python -m src.main analyze --asin B09XYZ001` |

## 评分体系

| 维度 | 权重 | 说明 |
|:---|:---:|:---|
| 需求分 | 35% | BSR 排名、月销量、评分区间 |
| 竞争分 | 30% | 评论数、卖家数、销量评论比 |
| 利润分 | 25% | 售价区间、毛利率、FBA 费用占比 |
| 机会分 | 10% | Listing 质量、新品占比、促销状态 |

## 数据源

| 数据源 | 用途 | 获取方式 |
|:---|:---|:---|
| Rainforest API | 商品数据（价格、评论、BSR等） | https://rainforestapi.com |
| Keepa API | 价格历史、BSR 趋势、促销检测 | https://keepa.com |
| OpenAI API | AI 深度分析（差评痛点、改进建议） | 任意 OpenAI 兼容 API |

## 项目结构

```
├── config.yaml           # 配置文件
├── config.example.yaml   # 配置模板
├── requirements.txt      # Python 依赖
├── db/products.db        # SQLite 数据库（自动创建）
├── reports/              # 导出报告目录
├── scripts/init_db.py    # 数据库管理
└── src/
    ├── main.py           # CLI 入口
    ├── collectors/       # 数据采集（Rainforest + Keepa）
    ├── analyzer/         # 分析引擎（评分 + 利润 + AI）
    ├── models/           # 数据模型
    └── utils/            # FBA 费用计算器
```

## 后续迭代方向

- [ ] 接入真实 Rainforest API / Keepa API
- [ ] 差评爬取 + NLP 情感分析
- [ ] 竞品 Listing 对比分析
- [ ] 供应链成本估算（1688 对标）
- [ ] Web Dashboard 可视化
- [ ] 自动化定时扫描 + 邮件通知
- [ ] 多站点支持（欧洲/日本）
