"""亚马逊辅助选品系统 - CLI 入口

用法：
    python -m src.main scan --category "Home & Kitchen" --pages 2
    python -m src.main search --keyword "garlic press" --pages 1
    python -m src.main report --top 20
    python -m src.main export --top 20 --output reports/report.md
    python -m src.main analyze --asin B09XYZ001
"""

import argparse
import os
import sys
import yaml
from datetime import datetime

# 将项目根目录加入 path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.collectors.rainforest import RainforestCollector
from src.collectors.keepa import KeepaCollector
from src.analyzer.scorer import Scorer, filter_products
from src.analyzer.profit import calculate_profit_batch
from src.analyzer.ai_analyzer import AIAnalyzer
from scripts.init_db import (
    init_db, save_products, save_scan,
    get_top_products, get_product_by_asin,
)


def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    if not os.path.exists(config_path):
        print("⚠️ 未找到 config.yaml，使用 config.example.yaml 作为模板")
        example_path = os.path.join(PROJECT_ROOT, "config.example.yaml")
        if os.path.exists(example_path):
            with open(example_path, "r") as f:
                return yaml.safe_load(f)
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_scan(config: dict, category: str, pages: int):
    """执行品类 Best Sellers 扫描"""
    print(f"\n{'='*60}")
    print(f"🔍 扫描品类：{category}（{pages} 页）")
    print(f"{'='*60}\n")

    # 1. 初始化数据库
    init_db()

    # 2. 数据采集
    rf_config = config.get("rainforest", {})
    collector = RainforestCollector(
        api_key=rf_config.get("api_key", ""),
        marketplace=rf_config.get("marketplace", "us"),
    )
    products = collector.get_best_sellers(category, pages)
    print(f"\n📊 采集到 {len(products)} 个产品\n")

    if not products:
        print("❌ 未获取到产品数据")
        return

    # 3. Keepa 数据丰富
    keepa_config = config.get("keepa", {})
    keepa = KeepaCollector(api_key=keepa_config.get("api_key", ""))
    print("📈 获取价格和 BSR 历史数据...")
    for i, p in enumerate(products):
        keepa.enrich_product(p)
        if (i + 1) % 10 == 0:
            print(f"  已处理 {i+1}/{len(products)}")

    # 4. 利润计算
    print("\n💰 计算利润...")
    products = calculate_profit_batch(products)

    # 5. 筛选过滤
    before_filter = len(products)
    products = filter_products(products, config)
    print(f"🔍 筛选：{before_filter} → {len(products)} 个产品\n")

    # 6. 评分
    print("📊 评分中...")
    scorer = Scorer(config)
    products = scorer.score_products(products)

    # 7. AI 分析（仅分析 Top 10）
    print("\n🤖 AI 深度分析 Top 产品...")
    analyzer = AIAnalyzer(config)
    top_for_ai = min(10, len(products))
    for i, p in enumerate(products[:top_for_ai]):
        analyzer.analyze_product(p)
        print(f"  ✅ [{i+1}/{top_for_ai}] {p.asin} - 总分 {p.total_score}")

    # 8. 保存到数据库
    saved = save_products(products)
    save_scan("bestsellers", category, pages, before_filter, len(products))
    print(f"\n💾 保存 {saved} 个产品到数据库")

    # 9. 打印 Top 结果
    _print_top_results(products[:15])


def run_search(config: dict, keyword: str, pages: int):
    """执行关键词搜索"""
    print(f"\n{'='*60}")
    print(f"🔎 搜索关键词：{keyword}（{pages} 页）")
    print(f"{'='*60}\n")

    init_db()

    rf_config = config.get("rainforest", {})
    collector = RainforestCollector(
        api_key=rf_config.get("api_key", ""),
        marketplace=rf_config.get("marketplace", "us"),
    )
    products = collector.search_products(keyword, pages)
    print(f"\n📊 搜索到 {len(products)} 个产品\n")

    if not products:
        print("❌ 未搜索到产品")
        return

    # Keepa + 利润 + 筛选 + 评分 + AI（同 scan 流程）
    keepa_config = config.get("keepa", {})
    keepa = KeepaCollector(api_key=keepa_config.get("api_key", ""))
    print("📈 获取历史数据...")
    for i, p in enumerate(products):
        keepa.enrich_product(p)

    print("💰 计算利润...")
    products = calculate_profit_batch(products)

    before_filter = len(products)
    products = filter_products(products, config)
    print(f"🔍 筛选：{before_filter} → {len(products)} 个产品\n")

    scorer = Scorer(config)
    products = scorer.score_products(products)

    analyzer = AIAnalyzer(config)
    print("🤖 AI 分析 Top 产品...")
    top_for_ai = min(10, len(products))
    for i, p in enumerate(products[:top_for_ai]):
        analyzer.analyze_product(p)
        print(f"  ✅ [{i+1}/{top_for_ai}] {p.asin} - 总分 {p.total_score}")

    saved = save_products(products)
    save_scan("search", keyword, pages, before_filter, len(products))
    print(f"\n💾 保存 {saved} 个产品到数据库")

    _print_top_results(products[:15])


def run_report(config: dict, top: int = 20):
    """从数据库生成评分报告"""
    print(f"\n{'='*60}")
    print(f"📊 Top {top} 产品报告")
    print(f"{'='*60}\n")

    products = get_top_products(top)
    if not products:
        print("❌ 数据库中没有产品数据，请先执行 scan 或 search")
        return

    _print_top_results_from_db(products)


def run_export(config: dict, top: int = 20, output: str = ""):
    """导出 Markdown 报告"""
    products = get_top_products(top)
    if not products:
        print("❌ 数据库中没有产品数据")
        return

    # 确保输出目录存在
    if not output:
        reports_dir = os.path.join(PROJECT_ROOT, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = os.path.join(reports_dir, f"report_{date_str}.md")

    report = _generate_markdown_report(products)

    with open(output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 报告已导出：{output}")


def run_analyze(config: dict, asin: str):
    """深度分析单个产品"""
    print(f"\n{'='*60}")
    print(f"🔬 深度分析产品：{asin}")
    print(f"{'='*60}\n")

    product = get_product_by_asin(asin)
    if not product:
        print(f"❌ 数据库中未找到产品 {asin}，请先 scan/search")
        return

    # AI 深度分析
    analyzer = AIAnalyzer(config)
    if not product.get("ai_analysis"):
        # 如果还没有 AI 分析，做一次
        from src.models.product import Product as ProductModel
        p = _dict_to_product(product)
        analyzer.analyze_product(p)
        product["ai_analysis"] = p.ai_analysis

    # 打印详细分析
    _print_product_detail(product)


def _print_top_results(products: list):
    """打印 Top 结果摘要"""
    print(f"\n{'='*60}")
    print(f"🏆 Top 推荐产品")
    print(f"{'='*60}")
    print(f"{'排名':<4} {'ASIN':<12} {'总分':<6} {'售价':<8} {'毛利':<8} {'标题摘要'}")
    print(f"{'-'*80}")

    for i, p in enumerate(products):
        title_short = p.title[:40] + "..." if len(p.title) > 40 else p.title
        print(
            f"{i+1:<4} {p.asin:<12} {p.total_score:<6.1f} "
            f"${p.price:<7.2f} ${p.gross_profit:<7.2f} {title_short}"
        )


def _print_top_results_from_db(products: list):
    """打印数据库中的 Top 结果"""
    print(f"{'排名':<4} {'ASIN':<12} {'总分':<6} {'售价':<8} {'毛利率':<8} {'标题摘要'}")
    print(f"{'-'*80}")

    for i, p in enumerate(products):
        title = p.get("title", "")
        title_short = title[:40] + "..." if len(title) > 40 else title
        print(
            f"{i+1:<4} {p.get('asin',''):<12} {p.get('total_score',0):<6.1f} "
            f"${p.get('price',0):<7.2f} {p.get('profit_margin',0):<7.1f}% {title_short}"
        )


def _print_product_detail(product: dict):
    """打印产品详细分析"""
    print(f"\n📦 {product.get('title', 'N/A')}")
    print(f"   ASIN: {product.get('asin')}")
    print(f"   品牌: {product.get('brand')}")
    print(f"   品类: {product.get('category')}")
    print(f"   售价: ${product.get('price', 0):.2f}")
    print(f"   评分: {product.get('rating', 0)}/5.0")
    print(f"   评论: {product.get('reviews_count', 0)}")
    print(f"   BSR: #{product.get('bsr', 0)}")
    print(f"   月销量估算: {product.get('monthly_sales_est', 0)}")
    print(f"\n{'─'*40}")
    print(f"   📊 需求分: {product.get('demand_score', 0):.1f}/100")
    print(f"   📊 竞争分: {product.get('competition_score', 0):.1f}/100")
    print(f"   📊 利润分: {product.get('profit_score', 0):.1f}/100")
    print(f"   📊 机会分: {product.get('opportunity_score', 0):.1f}/100")
    print(f"   📊 总分: {product.get('total_score', 0):.1f}/100")
    print(f"\n{'─'*40}")
    print(f"   💰 售价: ${product.get('price', 0):.2f}")
    print(f"   💰 佣金: ${product.get('referral_fee', 0):.2f}")
    print(f"   💰 FBA费: ${product.get('fba_fee', 0):.2f}")
    print(f"   💰 仓储费: ${product.get('storage_fee', 0):.2f}/月")
    print(f"   💰 采购成本: ${product.get('estimated_cost', 0):.2f}")
    print(f"   💰 毛利: ${product.get('gross_profit', 0):.2f} ({product.get('profit_margin', 0):.1f}%)")

    ai_analysis = product.get("ai_analysis", "")
    if ai_analysis:
        print(f"\n{'─'*40}")
        print(f"   🤖 AI 分析：")
        for line in ai_analysis.split("\n"):
            print(f"   {line}")


def _generate_markdown_report(products: list) -> str:
    """生成 Markdown 格式报告"""
    lines = [
        f"# 亚马逊选品报告",
        f"",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"产品数量：{len(products)}",
        f"",
        f"---",
        f"",
        f"## 📊 推荐产品排行",
        f"",
        f"| 排名 | ASIN | 总分 | 售价 | 毛利率 | 月销量 | 标题 |",
        f"|:---:|:---|:---:|:---:|:---:|:---:|:---|",
    ]

    for i, p in enumerate(products):
        title = p.get("title", "")[:50]
        lines.append(
            f"| {i+1} | `{p.get('asin','')}` | "
            f"{p.get('total_score',0):.1f} | "
            f"${p.get('price',0):.2f} | "
            f"{p.get('profit_margin',0):.1f}% | "
            f"{p.get('monthly_sales_est',0)} | "
            f"{title} |"
        )

    # 详细分析
    lines.extend(["", "---", "", "## 📦 产品详细分析", ""])

    for i, p in enumerate(products):
        lines.extend([
            f"### {i+1}. {p.get('title', 'N/A')}",
            f"",
            f"- **ASIN**: {p.get('asin')}",
            f"- **品牌**: {p.get('brand')}",
            f"- **品类**: {p.get('category')}",
            f"- **售价**: ${p.get('price', 0):.2f}",
            f"- **评分**: {p.get('rating', 0)}/5.0 ({p.get('reviews_count', 0)} 评论)",
            f"- **BSR**: #{p.get('bsr', 0)}",
            f"- **月销量**: ~{p.get('monthly_sales_est', 0)}",
            f"",
            f"**评分明细**：需求 {p.get('demand_score',0):.1f} | "
            f"竞争 {p.get('competition_score',0):.1f} | "
            f"利润 {p.get('profit_score',0):.1f} | "
            f"机会 {p.get('opportunity_score',0):.1f} | "
            f"**总分 {p.get('total_score',0):.1f}**",
            f"",
            f"**利润分析**：",
            f"- 毛利：${p.get('gross_profit',0):.2f}（毛利率 {p.get('profit_margin',0):.1f}%）",
            f"- 佣金：${p.get('referral_fee',0):.2f} | FBA：${p.get('fba_fee',0):.2f} | 仓储：${p.get('storage_fee',0):.2f}/月",
            f"",
        ])

        ai_analysis = p.get("ai_analysis", "")
        if ai_analysis:
            lines.extend([f"**AI 分析**：", f"", ai_analysis, ""])

    return "\n".join(lines)


def _dict_to_product(data: dict):
    """将数据库字典转换为 Product 对象"""
    from src.models.product import Product
    dims = data.get("dimensions", "")
    if isinstance(dims, str) and "x" in dims:
        parts = dims.split("x")
        dimensions = tuple(float(x.strip()) for x in parts)
    else:
        dimensions = (20.0, 10.0, 5.0)

    return Product(
        asin=data.get("asin", ""),
        title=data.get("title", ""),
        brand=data.get("brand", ""),
        category=data.get("category", ""),
        price=data.get("price", 0),
        rating=data.get("rating", 0),
        reviews_count=data.get("reviews_count", 0),
        bsr=data.get("bsr", 99999),
        monthly_sales_est=data.get("monthly_sales_est", 0),
        monthly_revenue_est=data.get("monthly_revenue_est", 0),
        seller_count=data.get("seller_count", 1),
        buy_box_seller=data.get("buy_box_seller", ""),
        weight_grams=data.get("weight_grams", 500),
        dimensions=dimensions,
        listing_quality_score=data.get("listing_quality_score", 50),
        date_first_available=data.get("date_first_available", ""),
        demand_score=data.get("demand_score", 0),
        competition_score=data.get("competition_score", 0),
        profit_score=data.get("profit_score", 0),
        opportunity_score=data.get("opportunity_score", 0),
        total_score=data.get("total_score", 0),
        gross_profit=data.get("gross_profit", 0),
        profit_margin=data.get("profit_margin", 0),
        referral_fee=data.get("referral_fee", 0),
        fba_fee=data.get("fba_fee", 0),
        storage_fee=data.get("storage_fee", 0),
        estimated_cost=data.get("estimated_cost", 0),
    )


def main():
    parser = argparse.ArgumentParser(
        description="亚马逊辅助选品系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m src.main scan --category "Home & Kitchen" --pages 2
  python -m src.main search --keyword "garlic press"
  python -m src.main report --top 20
  python -m src.main export --top 20
  python -m src.main analyze --asin B09XYZ001
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # scan 命令
    scan_parser = subparsers.add_parser("scan", help="扫描品类 Best Sellers")
    scan_parser.add_argument("--category", default="Home & Kitchen", help="品类名称")
    scan_parser.add_argument("--pages", type=int, default=2, help="扫描页数")

    # search 命令
    search_parser = subparsers.add_parser("search", help="关键词搜索产品")
    search_parser.add_argument("--keyword", required=True, help="搜索关键词")
    search_parser.add_argument("--pages", type=int, default=1, help="搜索页数")

    # report 命令
    report_parser = subparsers.add_parser("report", help="查看评分报告")
    report_parser.add_argument("--top", type=int, default=20, help="显示前 N 个")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出 Markdown 报告")
    export_parser.add_argument("--top", type=int, default=20, help="导出前 N 个")
    export_parser.add_argument("--output", default="", help="输出文件路径")

    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="深度分析单个产品")
    analyze_parser.add_argument("--asin", required=True, help="产品 ASIN")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    config = load_config()

    if args.command == "scan":
        run_scan(config, args.category, args.pages)
    elif args.command == "search":
        run_search(config, args.keyword, args.pages)
    elif args.command == "report":
        run_report(config, args.top)
    elif args.command == "export":
        run_export(config, args.top, args.output)
    elif args.command == "analyze":
        run_analyze(config, args.asin)


if __name__ == "__main__":
    main()
