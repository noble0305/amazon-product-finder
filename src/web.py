"""亚马逊选品系统 Web 服务"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime

from scripts.init_db import (
    init_db, get_top_products, get_product_by_asin,
    save_products, save_scan,
)
from src.collectors.rainforest import RainforestCollector
from src.collectors.keepa import KeepaCollector
from src.analyzer.scorer import Scorer, filter_products
from src.analyzer.profit import calculate_profit_batch
from src.analyzer.ai_analyzer import AIAnalyzer
from src.models.product import Product

import yaml

app = Flask(__name__)

# ─── 页面模板 ───────────────────────────────────────────────

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>亚马逊选品系统</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; color: #333; }
.header { background: linear-gradient(135deg, #232f3e 0%, #131921 100%); color: #fff; padding: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,.15); }
.header h1 { font-size: 24px; font-weight: 600; }
.header p { opacity: .7; font-size: 14px; margin-top: 4px; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 24px; margin-bottom: 20px; }
.card h2 { font-size: 18px; margin-bottom: 16px; color: #232f3e; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 20px; }
.stat { background: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
.stat .num { font-size: 32px; font-weight: 700; color: #ff9900; }
.stat .label { font-size: 13px; color: #888; margin-top: 4px; }
.form-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: end; }
.form-group { display: flex; flex-direction: column; }
.form-group label { font-size: 13px; color: #666; margin-bottom: 4px; }
input, select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; min-width: 200px; }
input:focus, select:focus { outline: none; border-color: #ff9900; }
.btn { padding: 9px 20px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; transition: .2s; }
.btn-primary { background: #ff9900; color: #fff; }
.btn-primary:hover { background: #e88a00; }
.btn-secondary { background: #232f3e; color: #fff; }
.btn-secondary:hover { background: #37475a; }
.btn-sm { padding: 5px 12px; font-size: 12px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { background: #fafafa; text-align: left; padding: 12px; border-bottom: 2px solid #eee; color: #666; font-weight: 600; }
td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
tr:hover { background: #fffbf0; }
.score { display: inline-block; width: 40px; height: 40px; line-height: 40px; border-radius: 50%; text-align: center; font-weight: 700; font-size: 14px; color: #fff; }
.score-high { background: #27ae60; }
.score-mid { background: #f39c12; }
.score-low { background: #e74c3c; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
.badge-green { background: #d4edda; color: #155724; }
.badge-yellow { background: #fff3cd; color: #856404; }
.badge-red { background: #f8d7da; color: #721c24; }
.loading { display: none; text-align: center; padding: 40px; }
.loading.show { display: block; }
.spinner { border: 3px solid #f0f0f0; border-top: 3px solid #ff9900; border-radius: 50%; width: 36px; height: 36px; animation: spin 1s linear infinite; margin: 0 auto 12px; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.actions { display: flex; gap: 8px; margin-top: 16px; }
.empty { text-align: center; padding: 40px; color: #999; }
.detail-link { color: #ff9900; text-decoration: none; }
.detail-link:hover { text-decoration: underline; }
footer { text-align: center; padding: 20px; color: #999; font-size: 13px; }
</style>
</head>
<body>
<div class="header">
  <div class="container">
    <h1>🛒 亚马逊选品系统</h1>
    <p>数据驱动 + AI 分析 · Demo 模式</p>
  </div>
</div>

<div class="container">
  <!-- 统计卡片 -->
  <div class="stats">
    <div class="stat"><div class="num">{{ stats.total }}</div><div class="label">数据库产品</div></div>
    <div class="stat"><div class="num">{{ stats.recommended }}</div><div class="label">推荐产品 (≥70分)</div></div>
    <div class="stat"><div class="num">{{ stats.avg_score }}</div><div class="label">平均评分</div></div>
    <div class="stat"><div class="num">{{ stats.avg_margin }}</div><div class="label">平均毛利率</div></div>
  </div>

  <!-- 扫描/搜索 -->
  <div class="card">
    <h2>🔍 数据采集</h2>
    <div class="form-row">
      <div class="form-group">
        <label>品类扫描</label>
        <select id="category">
          <option value="Home & Kitchen">Home & Kitchen</option>
          <option value="Sports & Outdoors">Sports & Outdoors</option>
          <option value="Pet Supplies">Pet Supplies</option>
          <option value="Beauty & Personal Care">Beauty & Personal Care</option>
          <option value="Office Products">Office Products</option>
          <option value="Tools & Home Improvement">Tools & Home Improvement</option>
        </select>
      </div>
      <div class="form-group">
        <label>页数</label>
        <input type="number" id="pages" value="2" min="1" max="5" style="min-width:80px">
      </div>
      <button class="btn btn-primary" onclick="doScan()">扫描 Best Sellers</button>
    </div>
    <div style="margin-top:12px;display:flex;gap:12px;align-items:end;flex-wrap:wrap">
      <div class="form-group">
        <label>关键词搜索</label>
        <input type="text" id="keyword" placeholder="如 garlic press">
      </div>
      <button class="btn btn-secondary" onclick="doSearch()">搜索</button>
    </div>
  </div>

  <!-- 加载状态 -->
  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p id="loadingText">正在扫描...</p>
  </div>

  <!-- 产品列表 -->
  <div class="card" id="results" style="display:{{ 'block' if products else 'none' }}">
    <h2>🏆 推荐产品排行 <span style="font-size:13px;color:#888">（按总分降序）</span></h2>
    {% if products %}
    <div style="overflow-x:auto">
    <table>
      <thead>
        <tr>
          <th>#</th><th>ASIN</th><th>总分</th><th>售价</th><th>毛利</th><th>毛利率</th><th>月销量</th><th>BSR</th><th>评分</th><th>卖家</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
      {% for p in products %}
        <tr>
          <td>{{ loop.index }}</td>
          <td><code>{{ p.asin }}</code></td>
          <td><span class="score {{ 'score-high' if p.total_score >= 75 else ('score-mid' if p.total_score >= 60 else 'score-low') }}">{{ p.total_score }}</span></td>
          <td>${{ "%.2f"|format(p.price) }}</td>
          <td>${{ "%.2f"|format(p.gross_profit) }}</td>
          <td><span class="badge {{ 'badge-green' if p.profit_margin >= 30 else ('badge-yellow' if p.profit_margin >= 20 else 'badge-red') }}">{{ "%.1f"|format(p.profit_margin) }}%</span></td>
          <td>{{ p.monthly_sales_est }}</td>
          <td>#{{ p.bsr }}</td>
          <td>{{ p.rating }}/5.0</td>
          <td>{{ p.seller_count }}</td>
          <td><a class="detail-link" href="/detail/{{ p.asin }}?return=1">详情 →</a></td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    <div class="actions">
      <a href="/export" class="btn btn-primary">📥 导出报告</a>
      <a href="/api/export" class="btn btn-secondary" download>📄 下载 Markdown</a>
    </div>
    {% else %}
    <div class="empty">暂无产品数据，请先扫描或搜索</div>
    {% endif %}
  </div>
</div>

<footer>亚马逊辅助选品系统 · Demo 模式 · 数据仅供演示</footer>

<script>
async function doScan() {
  const cat = document.getElementById('category').value;
  const pages = document.getElementById('pages').value;
  showLoading('正在扫描 ' + cat + ' ...');
  try {
    const resp = await fetch('/api/scan?category=' + encodeURIComponent(cat) + '&pages=' + pages);
    const data = await resp.json();
    if (data.ok) { window.location.reload(); }
    else { alert('扫描失败: ' + data.error); hideLoading(); }
  } catch(e) { alert('请求失败: ' + e.message); hideLoading(); }
}

async function doSearch() {
  const kw = document.getElementById('keyword').value.trim();
  if (!kw) { alert('请输入关键词'); return; }
  showLoading('正在搜索 "' + kw + '" ...');
  try {
    const resp = await fetch('/api/search?keyword=' + encodeURIComponent(kw) + '&pages=1');
    const data = await resp.json();
    if (data.ok) { window.location.reload(); }
    else { alert('搜索失败: ' + data.error); hideLoading(); }
  } catch(e) { alert('请求失败: ' + e.message); hideLoading(); }
}

function showLoading(text) {
  document.getElementById('loadingText').textContent = text;
  document.getElementById('loading').classList.add('show');
  document.getElementById('results').style.display = 'none';
}
function hideLoading() {
  document.getElementById('loading').classList.remove('show');
  document.getElementById('results').style.display = 'block';
}
</script>
</body>
</html>"""

DETAIL_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ p.title }} - 产品详情</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; color: #333; }
.header { background: linear-gradient(135deg, #232f3e 0%, #131921 100%); color: #fff; padding: 20px 0; }
.header a { color: #ff9900; text-decoration: none; }
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
.card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 24px; margin-bottom: 20px; }
.card h2 { font-size: 18px; margin-bottom: 16px; color: #232f3e; }
.back { display: inline-block; margin-bottom: 16px; color: #ff9900; text-decoration: none; font-size: 14px; }
.back:hover { text-decoration: underline; }
.info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.info-item label { display: block; font-size: 12px; color: #888; margin-bottom: 2px; }
.info-item .val { font-size: 18px; font-weight: 600; }
.score-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.score-bar .bar { flex: 1; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
.score-bar .bar .fill { height: 100%; border-radius: 4px; transition: width .3s; }
.score-bar .label { width: 60px; font-size: 13px; color: #666; }
.score-bar .num { width: 40px; text-align: right; font-weight: 600; font-size: 14px; }
.analysis { background: #fafafa; border-radius: 6px; padding: 16px; font-size: 14px; line-height: 1.8; white-space: pre-wrap; }
.analysis h3 { margin-top: 12px; margin-bottom: 4px; color: #232f3e; }
</style>
</head>
<body>
<div class="header">
  <div class="container">
    <a href="/">← 返回列表</a>
    <h1 style="margin-top:8px;font-size:20px">📦 {{ p.title }}</h1>
  </div>
</div>

<div class="container">
  <!-- 基本信息 -->
  <div class="card">
    <h2>📋 基本信息</h2>
    <div class="info-grid">
      <div class="info-item"><label>ASIN</label><div class="val">{{ p.asin }}</div></div>
      <div class="info-item"><label>品牌</label><div class="val">{{ p.brand or 'N/A' }}</div></div>
      <div class="info-item"><label>品类</label><div class="val">{{ p.category or 'N/A' }}</div></div>
      <div class="info-item"><label>售价</label><div class="val" style="color:#27ae60">${{ "%.2f"|format(p.price) }}</div></div>
      <div class="info-item"><label>评分</label><div class="val">{{ p.rating }}/5.0</div></div>
      <div class="info-item"><label>评论数</label><div class="val">{{ p.reviews_count }}</div></div>
      <div class="info-item"><label>BSR 排名</label><div class="val">#{{ p.bsr }}</div></div>
      <div class="info-item"><label>月销量估算</label><div class="val">{{ p.monthly_sales_est }}</div></div>
      <div class="info-item"><label>卖家数量</label><div class="val">{{ p.seller_count }}</div></div>
      <div class="info-item"><label>首次上架</label><div class="val">{{ p.date_first_available or 'N/A' }}</div></div>
    </div>
  </div>

  <!-- 评分 -->
  <div class="card">
    <h2>📊 多维评分</h2>
    <div class="score-bar">
      <span class="label">需求</span>
      <div class="bar"><div class="fill" style="width:{{ p.demand_score }}%;background:#3498db"></div></div>
      <span class="num">{{ p.demand_score }}</span>
    </div>
    <div class="score-bar">
      <span class="label">竞争</span>
      <div class="bar"><div class="fill" style="width:{{ p.competition_score }}%;background:#2ecc71"></div></div>
      <span class="num">{{ p.competition_score }}</span>
    </div>
    <div class="score-bar">
      <span class="label">利润</span>
      <div class="bar"><div class="fill" style="width:{{ p.profit_score }}%;background:#f39c12"></div></div>
      <span class="num">{{ p.profit_score }}</span>
    </div>
    <div class="score-bar">
      <span class="label">机会</span>
      <div class="bar"><div class="fill" style="width:{{ p.opportunity_score }}%;background:#9b59b6"></div></div>
      <span class="num">{{ p.opportunity_score }}</span>
    </div>
    <div style="margin-top:16px;text-align:center;font-size:28px;font-weight:700;color:{{ '#27ae60' if p.total_score >= 75 else ('#f39c12' if p.total_score >= 60 else '#e74c3c') }}">
      总分 {{ p.total_score }}
    </div>
  </div>

  <!-- 利润 -->
  <div class="card">
    <h2>💰 利润分析</h2>
    <div class="info-grid">
      <div class="info-item"><label>售价</label><div class="val">${{ "%.2f"|format(p.price) }}</div></div>
      <div class="info-item"><label>佣金 (15%)</label><div class="val">-${{ "%.2f"|format(p.referral_fee) }}</div></div>
      <div class="info-item"><label>FBA 配送费</label><div class="val">-${{ "%.2f"|format(p.fba_fee) }}</div></div>
      <div class="info-item"><label>月仓储费</label><div class="val">-${{ "%.2f"|format(p.storage_fee) }}</div></div>
      <div class="info-item"><label>采购成本 (估)</label><div class="val">-${{ "%.2f"|format(p.estimated_cost) }}</div></div>
      <div class="info-item"><label>毛利</label><div class="val" style="color:#27ae60">${{ "%.2f"|format(p.gross_profit) }}</div></div>
    </div>
    <div style="margin-top:16px;text-align:center;font-size:24px;font-weight:700">
      毛利率 <span style="color:{{ '#27ae60' if p.profit_margin >= 30 else '#e74c3c' }}">{{ "%.1f"|format(p.profit_margin) }}%</span>
    </div>
  </div>

  <!-- AI 分析 -->
  <div class="card">
    <h2>🤖 AI 分析</h2>
    {% if p.ai_analysis %}
    <div class="analysis">{{ p.ai_analysis }}</div>
    {% else %}
    <div style="text-align:center;color:#999;padding:20px">暂无 AI 分析，请配置 AI API Key 后重新扫描</div>
    {% endif %}
  </div>
</div>
</body>
</html>"""


# ─── 辅助函数 ───────────────────────────────────────────────

def load_config() -> dict:
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    if not os.path.exists(config_path):
        config_path = os.path.join(PROJECT_ROOT, "config.example.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def _run_pipeline(products, config, scan_type, query, pages):
    """通用处理流水线"""
    # Keepa 丰富
    keepa = KeepaCollector(api_key=config.get("keepa", {}).get("api_key", ""))
    for p in products:
        keepa.enrich_product(p)

    # 利润
    products = calculate_profit_batch(products)

    # 筛选
    before = len(products)
    products = filter_products(products, config)

    # 评分
    scorer = Scorer(config)
    products = scorer.score_products(products)

    # AI 分析 Top 10
    analyzer = AIAnalyzer(config)
    for p in products[:10]:
        analyzer.analyze_product(p)

    # 保存
    saved = save_products(products)
    save_scan(scan_type, query, pages, before, len(products))

    return products


# ─── 路由 ───────────────────────────────────────────────────

@app.route("/")
def index():
    products = get_top_products(50)
    stats = {"total": len(products), "recommended": 0, "avg_score": 0, "avg_margin": 0}
    if products:
        recs = [p for p in products if p.get("total_score", 0) >= 70]
        stats["recommended"] = len(recs)
        stats["avg_score"] = round(sum(p.get("total_score", 0) for p in products) / len(products), 1)
        margins = [p.get("profit_margin", 0) for p in products if p.get("profit_margin")]
        stats["avg_margin"] = f"{round(sum(margins) / len(margins), 1)}%" if margins else "0%"
    return render_template_string(INDEX_HTML, products=products, stats=stats)


@app.route("/detail/<asin>")
def detail(asin):
    p = get_product_by_asin(asin)
    if not p:
        return "产品未找到，请先扫描", 404
    return render_template_string(DETAIL_HTML, p=p)


@app.route("/api/scan")
def api_scan():
    config = load_config()
    category = request.args.get("category", "Home & Kitchen")
    pages = int(request.args.get("pages", 2))
    try:
        rf = config.get("rainforest", {})
        collector = RainforestCollector(
            api_key=rf.get("api_key", ""), marketplace=rf.get("marketplace", "us")
        )
        products = collector.get_best_sellers(category, pages)
        if not products:
            return jsonify({"ok": False, "error": "未获取到产品"})
        _run_pipeline(products, config, "bestsellers", category, pages)
        return jsonify({"ok": True, "count": len(products)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/search")
def api_search():
    config = load_config()
    keyword = request.args.get("keyword", "")
    pages = int(request.args.get("pages", 1))
    if not keyword:
        return jsonify({"ok": False, "error": "请输入关键词"})
    try:
        rf = config.get("rainforest", {})
        collector = RainforestCollector(
            api_key=rf.get("api_key", ""), marketplace=rf.get("marketplace", "us")
        )
        products = collector.search_products(keyword, pages)
        if not products:
            return jsonify({"ok": False, "error": "未搜索到产品"})
        _run_pipeline(products, config, "search", keyword, pages)
        return jsonify({"ok": True, "count": len(products)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/export")
def export_page():
    """在浏览器展示报告"""
    from src.main import _generate_markdown_report
    products = get_top_products(30)
    if not products:
        return "暂无数据"
    report = _generate_markdown_report(products)
    return f"<pre style='padding:24px;font-size:14px;line-height:1.6;white-space:pre-wrap'>{report}</pre>"


@app.route("/api/export")
def export_download():
    from src.main import _generate_markdown_report
    products = get_top_products(30)
    report = _generate_markdown_report(products)
    from flask import Response
    return Response(
        report,
        mimetype="text/markdown",
        headers={"Content-Disposition": "attachment; filename=report.md"},
    )


# ─── 启动 ───────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n🚀 亚马逊选品系统已启动")
    print("   打开浏览器访问：http://127.0.0.1:5000\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
