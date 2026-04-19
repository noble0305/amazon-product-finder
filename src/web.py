"""亚马逊选品系统 Web 服务"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime

from scripts.init_db import (
    init_db, get_top_products, get_product_by_asin, get_products_by_asins,
    save_products, save_scan, save_price_snapshot,
    get_favorites, add_favorite, remove_favorite, is_favorite,
    get_price_history, get_favorite_groups,
    create_price_alert, get_price_alerts, delete_price_alert, check_price_alerts,
    create_bsr_alert, get_bsr_alerts, delete_bsr_alert, check_bsr_alerts,
    import_products_from_list,
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

COMMON_HEAD = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;background:#f8f9fb;color:#1e293b;min-height:100vh}
a{color:#6366f1;text-decoration:none}
a:hover{text-decoration:underline}
.header{background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#a78bfa 100%);border-bottom:1px solid rgba(99,102,241,.2);padding:20px 0;position:sticky;top:0;z-index:100}
.header h1{font-size:22px;font-weight:700;color:#fff}
.header p{opacity:.85;font-size:13px;margin-top:2px;color:#e0e7ff}
.container{max-width:1280px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #e9ecef;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.card h2{font-size:17px;margin-bottom:16px;color:#4338ca;font-weight:600}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:20px}
.stat{background:linear-gradient(135deg,rgba(99,60,200,.15),rgba(139,92,246,.08));border:1px solid rgba(139,92,246,.15);border-radius:10px;padding:18px;text-align:center}
.stat .num{font-size:30px;font-weight:700;color:#6366f1}
.stat .label{font-size:12px;color:#64748b;margin-top:4px}
.form-row{display:flex;gap:12px;flex-wrap:wrap;align-items:end}
.form-group{display:flex;flex-direction:column}
.form-group label{font-size:12px;color:#475569;margin-bottom:4px}
input,select{padding:9px 14px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;color:#1e293b;font-size:14px;min-width:200px;font-family:inherit}
input:focus,select:focus{outline:none;border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,.12)}
.btn{padding:9px 20px;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:.2s;font-family:inherit}
.btn-primary{background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff}
.btn-primary:hover{background:linear-gradient(135deg,#818cf8,#6366f1);transform:translateY(-1px)}
.btn-secondary{background:#fff;color:#4f46e5;border:1px solid #e2e8f0}
.btn-secondary:hover{background:rgba(139,92,246,.25)}
.btn-danger{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.25)}
.btn-danger:hover{background:rgba(239,68,68,.25)}
.btn-sm{padding:5px 12px;font-size:11px}
.btn:disabled{opacity:.4;cursor:not-allowed}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f8fafc;text-align:left;padding:12px;border-bottom:2px solid #e2e8f0;color:#6366f1;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.5px}
td{padding:10px 12px;border-bottom:1px solid rgba(139,92,246,.06)}
tr:hover{background:#faf5ff}
.score{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%;font-weight:700;font-size:13px;color:#fff}
.score-high{background:linear-gradient(135deg,#059669,#10b981)}
.score-mid{background:linear-gradient(135deg,#d97706,#f59e0b)}
.score-low{background:linear-gradient(135deg,#dc2626,#ef4444)}
.badge{display:inline-block;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600}
.badge-green{background:rgba(16,185,129,.15);color:#059669}
.badge-yellow{background:rgba(245,158,11,.15);color:#d97706}
.badge-red{background:rgba(239,68,68,.15);color:#dc2626}
.loading{display:none;text-align:center;padding:40px}
.loading.show{display:block}
.spinner{border:3px solid rgba(139,92,246,.15);border-top:3px solid #8b5cf6;border-radius:50%;width:36px;height:36px;animation:spin 1s linear infinite;margin:0 auto 12px}
@keyframes spin{100%{transform:rotate(360deg)}}
.actions{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
.empty{text-align:center;padding:40px;color:#94a3b8}
.detail-link{color:#6366f1;font-weight:500}
.detail-link:hover{color:#4f46e5}
footer{text-align:center;padding:24px;color:#94a3b8;font-size:12px}
.tab-bar{display:flex;gap:4px;margin-bottom:20px;background:rgba(30,22,60,.4);border-radius:10px;padding:4px;border:1px solid rgba(139,92,246,.1)}
.tab{padding:10px 20px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:.2s;color:#475569;border:none;background:none;font-family:inherit}
.tab:hover{color:#6366f1;background:#f1f5f9}
.tab.active{background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff}
.tab-panel{display:none}
.tab-panel.active{display:block}
.fav-btn{cursor:pointer;font-size:18px;opacity:.4;transition:.2s;border:none;background:none}
.fav-btn:hover,.fav-btn.active{opacity:1}
.checkbox-col{width:30px;text-align:center}
.checkbox-col input[type=checkbox]{min-width:auto;width:16px;height:16px;accent-color:#7c3aed}
code{background:rgba(139,92,246,.1);padding:2px 6px;border-radius:4px;font-size:12px;color:#c4b5fd}
</style>
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
""" + COMMON_HEAD + """
<title>亚马逊选品系统</title>
</head>
<body>
<div class="header">
  <div class="container">
    <h1>🛒 亚马逊选品系统</h1>
    <p>数据驱动 + AI 分析</p>
  </div>
</div>

<div class="container">
  <!-- Tab 导航 -->
  <div class="tab-bar">
    <button class="tab active" onclick="switchTab('overview')">📊 概览</button>
    <button class="tab" onclick="switchTab('favorites')">⭐ 收藏夹</button>
    <button class="tab" onclick="switchTab('category-report')">📈 品类报告</button>
    <button class="tab" onclick="switchTab('trend-monitor')">📈 趋势监控</button>
    <button class="tab" onclick="switchTab('data-import')">📤 数据导入</button>
  </div>

  <!-- ═══ 概览 Tab ═══ -->
  <div class="tab-panel active" id="tab-overview">
    <div class="stats">
      <div class="stat"><div class="num">{{ stats.total }}</div><div class="label">数据库产品</div></div>
      <div class="stat"><div class="num">{{ stats.recommended }}</div><div class="label">推荐 (≥70分)</div></div>
      <div class="stat"><div class="num">{{ stats.avg_score }}</div><div class="label">平均评分</div></div>
      <div class="stat"><div class="num">{{ stats.avg_margin }}</div><div class="label">平均毛利率</div></div>
    </div>

    <div class="card">
      <h2>🔍 数据采集</h2>
      <div class="form-row">
        <div class="form-group">
          <label>站点</label>
          <select id="marketplace">
            <option value="us">🇺🇸 美国 amazon.com</option>
            <option value="uk">🇬🇧 英国 amazon.co.uk</option>
            <option value="de">🇩🇪 德国 amazon.de</option>
            <option value="fr">🇫🇷 法国 amazon.fr</option>
            <option value="jp">🇯🇵 日本 amazon.co.jp</option>
            <option value="au">🇦🇺 澳洲 amazon.com.au</option>
            <option value="ca">🇨🇦 加拿大 amazon.ca</option>
            <option value="it">🇮🇹 意大利 amazon.it</option>
            <option value="es">🇪🇸 西班牙 amazon.es</option>
            <option value="in">🇮🇳 印度 amazon.in</option>
            <option value="br">🇧🇷 巴西 amazon.com.br</option>
            <option value="mx">🇲🇽 墨西哥 amazon.com.mx</option>
            <option value="sg">🇸🇬 新加坡 amazon.sg</option>
            <option value="ae">🇦🇪 阿联酋 amazon.ae</option>
            <option value="nl">🇳🇱 荷兰 amazon.nl</option>
            <option value="se">🇸🇪 瑞典 amazon.se</option>
            <option value="be">🇧🇪 比利时 amazon.com.be</option>
          </select>
        </div>
        <div class="form-group">
          <label>品类扫描</label>
          <select id="category">
            <option value="">⏳ 加载中...</option>
          </select>
        </div>
        <div class="form-group">
          <label>数据源</label>
          <select id="datasource">
            <option value="rainforest">🌊 Rainforest API（推荐）</option>
            <option value="playwright">🕷️ Playwright 直爬（可能触发验证码）</option>
          </select>
        </div>
        <div class="form-group">
          <label>页数</label>
          <input type="number" id="pages" value="2" min="1" max="5" style="min-width:80px">
        </div>
        <div class="form-group">
          <label>榜单类型</label>
          <select id="scan_type">
            <option value="bestsellers">🏆 Best Sellers 畅销榜</option>
            <option value="new_releases">🆕 New Releases 新品榜</option>
            <option value="movers_shakers">🚀 Movers & Shakers 飙升榜</option>
          </select>
        </div>
        <button class="btn btn-primary" onclick="doScan()">🔍 扫描榜单</button>
      </div>
      <div style="margin-top:12px;display:flex;gap:12px;align-items:end;flex-wrap:wrap">
        <div class="form-group"><label>关键词搜索</label><input type="text" id="keyword" placeholder="如 garlic press"></div>
        <div class="form-group">
          <label>数据源</label>
          <select id="datasource-search">
            <option value="rainforest">🌊 Rainforest API（推荐）</option>
            <option value="playwright">🕷️ Playwright 直爬（可能触发验证码）</option>
          </select>
        </div>
        <button class="btn btn-secondary" onclick="doSearch()">搜索</button>
      </div>
    </div>

    <div class="loading" id="loading">
      <div class="spinner"></div>
      <p id="loadingText">正在扫描...</p>
    </div>

    <div class="card" id="results" style="display:{{ 'block' if products else 'none' }}">
      <h2>🏆 推荐产品排行 <span style="font-size:12px;color:#6b5f82">（按总分降序）</span></h2>
      {% if products %}
      <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th class="checkbox-col"><input type="checkbox" id="selectAll" onchange="toggleAll(this)"></th>
            <th>#</th><th>图片</th><th>ASIN</th><th>总分</th><th>售价</th><th>毛利</th><th>毛利率</th><th>月销量</th><th>BSR</th><th>评分</th><th>收藏</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
        {% for p in products %}
        <tr>
          <td class="checkbox-col"><input type="checkbox" class="asin-cb" value="{{ p.asin }}"></td>
          <td>{{ loop.index }}</td>
          <td>{% if p.image_url %}<a href="https://www.{{ p.get('amazon_domain', 'amazon.com') }}/dp/{{ p.asin }}" target="_blank" rel="noopener"><img src="{{ p.image_url }}" alt="{{ p.title }}" style="width:50px;height:50px;object-fit:cover;border-radius:6px;border:1px solid #e2e8f0;" onerror="this.src='https://via.placeholder.com/50x50/f1f5f9/94a3b8?text=📦'" /></a>{% else %}<a href="https://www.{{ p.get('amazon_domain', 'amazon.com') }}/dp/{{ p.asin }}" target="_blank" rel="noopener" style="display:inline-block;width:50px;height:50px;background:#f1f5f9;border-radius:6px;text-align:center;line-height:50px;font-size:20px;text-decoration:none">📦</a>{% endif %}</td>
          <td><a href="https://www.{{ p.get('amazon_domain', 'amazon.com') }}/dp/{{ p.asin }}" target="_blank" rel="noopener" style="color:#6366f1;font-weight:500"><code>{{ p.asin }}</code></a></td>
          <td><span class="score {{ 'score-high' if p.total_score >= 75 else ('score-mid' if p.total_score >= 60 else 'score-low') }}">{{ p.total_score }}</span></td>
          <td>${{ "%.2f"|format(p.price) }}</td>
          <td>${{ "%.2f"|format(p.gross_profit) }}</td>
          <td><span class="badge {{ 'badge-green' if p.profit_margin >= 30 else ('badge-yellow' if p.profit_margin >= 20 else 'badge-red') }}">{{ "%.1f"|format(p.profit_margin) }}%</span></td>
          <td>{{ p.monthly_sales_est }}</td>
          <td>#{{ p.bsr }}</td>
          <td>{{ p.rating }}/5.0</td>
          <td><button class="fav-btn {{ 'active' if p.asin in fav_asins else '' }}" onclick="toggleFav('{{ p.asin }}',this)">⭐</button></td>
          <td style="white-space:nowrap"><button class="btn btn-sm btn-secondary" style="padding:2px 6px;font-size:14px" onclick="quickAlert('{{ p.asin }}','{{ "%.2f"|format(p.price) }}')" title="快速预警">🔔</button> <a class="detail-link" href="/detail/{{ p.asin }}">详情 →</a></td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
      </div>
      <div class="actions">
        <a href="/export" class="btn btn-primary">📥 导出报告</a>
        <a href="/api/export" class="btn btn-secondary" download>📄 下载 Markdown</a>
        <button class="btn btn-secondary" onclick="compareSelected()">📊 对比选中</button>
      </div>
      {% else %}
      <div class="empty">暂无产品数据，请先扫描或搜索</div>
      {% endif %}
    </div>
  </div>

  <!-- ═══ 收藏夹 Tab ═══ -->
  <div class="tab-panel" id="tab-favorites">
    <div class="card">
      <h2>⭐ 我的收藏</h2>
      <div id="fav-content"><div class="empty">加载中...</div></div>
    </div>
  </div>

  <!-- ═══ 趋势监控 Tab ═══ -->
  <div class="tab-panel" id="tab-trend-monitor">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <!-- 价格预警 -->
      <div class="card">
        <h2>🔔 价格预警</h2>
        <div class="form-row" style="margin-bottom:16px">
          <div class="form-group"><label>ASIN</label><input type="text" id="alert-asin" placeholder="输入 ASIN" style="min-width:140px"></div>
          <div class="form-group"><label>预警类型</label>
            <select id="alert-type" style="min-width:150px" onchange="onAlertTypeChange()">
              <option value="price_drop">📉 价格下跌</option>
              <option value="price_surge">📈 价格上涨</option>
              <option value="below_target">🎯 低于目标价</option>
            </select>
          </div>
          <div class="form-group" id="threshold-group"><label>阈值 (%)</label><input type="number" id="alert-threshold" value="10" min="1" max="50" style="min-width:80px"></div>
          <div class="form-group" id="target-group" style="display:none"><label>目标价格 ($)</label><input type="number" id="alert-target" step="0.01" style="min-width:100px"></div>
          <button class="btn btn-primary" onclick="addAlert()">添加</button>
        </div>
        <div id="alerts-list"></div>
      </div>

      <!-- BSR 监控 -->
      <div class="card">
        <h2>📊 BSR 异动监控</h2>
        <div class="form-row" style="margin-bottom:16px">
          <div class="form-group"><label>ASIN</label><input type="text" id="bsr-alert-asin" placeholder="输入 ASIN" style="min-width:140px"></div>
          <div class="form-group"><label>变动类型</label>
            <select id="bsr-alert-type" style="min-width:150px">
              <option value="bsr_surge">🚀 排名上升</option>
              <option value="bsr_drop">📉 排名下降</option>
            </select>
          </div>
          <div class="form-group"><label>阈值 (%)</label><input type="number" id="bsr-threshold" value="20" min="1" max="100" style="min-width:80px"></div>
          <button class="btn btn-primary" onclick="addBsrAlert()">添加</button>
        </div>
        <div id="bsr-alerts-list"></div>
      </div>
    </div>

    <!-- 触发历史 -->
    <div class="card">
      <h2>📋 预警触发记录</h2>
      <div style="display:flex;gap:10px;margin-bottom:16px">
        <button class="btn btn-primary" onclick="checkAllAlerts()">🔍 立即检查所有预警</button>
      </div>
      <div id="triggered-list"><div class="empty">点击上方按钮检查预警</div></div>
    </div>

    <!-- BSR 趋势小图表 -->
    <div class="card">
      <h2>📉 BSR 趋势概览</h2>
      <div class="form-row" style="margin-bottom:12px">
        <div class="form-group"><label>ASIN</label><input type="text" id="bsr-trend-asin" placeholder="输入 ASIN 查看 BSR 趋势" style="min-width:200px"></div>
        <button class="btn btn-secondary" onclick="loadBsrChart()">查看趋势</button>
      </div>
      <div id="bsr-chart-area"></div>
    </div>
  </div>

  <!-- ═══ 数据导入 Tab ═══ -->
  <div class="tab-panel" id="tab-data-import">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <!-- 文件上传 -->
      <div class="card">
        <h2>📁 文件上传导入</h2>
        <div id="drop-zone" style="border:2px dashed #c4b5fd;border-radius:12px;padding:40px 20px;text-align:center;cursor:pointer;transition:.2s;background:#faf5ff" onmouseover="this.style.borderColor='#6366f1';this.style.background='rgba(99,102,241,.05)'" onmouseout="this.style.borderColor='#c4b5fd';this.style.background='#faf5ff'" onclick="document.getElementById('file-input').click()" ondragover="event.preventDefault();this.style.borderColor='#6366f1';this.style.background='rgba(99,102,241,.08)'" ondragleave="this.style.borderColor='#c4b5fd';this.style.background='#faf5ff'" ondrop="handleDrop(event)">
          <div style="font-size:40px;margin-bottom:8px">📄</div>
          <div style="font-size:14px;color:#475569">拖拽文件到此处或点击选择</div>
          <div style="font-size:12px;color:#94a3b8;margin-top:4px">支持 .csv / .xlsx（最大 10MB）</div>
          <input type="file" id="file-input" accept=".csv,.xlsx" style="display:none" onchange="handleFileUpload(this.files[0])">
        </div>
        <div id="file-preview" style="margin-top:16px;display:none"></div>
        <div id="column-mapping" style="margin-top:16px;display:none"></div>
        <div id="import-actions" style="margin-top:16px;display:none">
          <div class="form-row" style="margin-bottom:12px">
            <div class="form-group">
              <label>合并策略</label>
              <select id="merge-strategy" style="min-width:150px">
                <option value="merge">🔄 合并（仅更新非空字段）</option>
                <option value="overwrite">✏️ 覆盖（完全替换）</option>
                <option value="skip">⏭️ 跳过已存在</option>
              </select>
            </div>
          </div>
          <button class="btn btn-primary" onclick="confirmImport()" id="confirm-import-btn">✅ 确认导入</button>
          <div id="import-progress" style="margin-top:12px;display:none">
            <div style="background:#e9ecef;border-radius:6px;height:8px;overflow:hidden"><div id="progress-bar" style="background:linear-gradient(135deg,#6366f1,#4f46e5);height:100%;width:0%;transition:width .3s"></div></div>
            <div style="font-size:12px;color:#64748b;margin-top:4px" id="progress-text">导入中...</div>
          </div>
        </div>
      </div>

      <!-- 粘贴导入 -->
      <div class="card">
        <h2>📋 粘贴数据导入</h2>
        <textarea id="paste-data" style="width:100%;min-height:200px;padding:12px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;font-family:monospace;resize:vertical" placeholder="粘贴从亚马逊后台复制的表格数据...\n支持逗号、制表符、分号分隔"></textarea>
        <div style="margin-top:12px">
          <button class="btn btn-secondary" onclick="parsePasteData()">🔍 解析数据</button>
        </div>
        <div id="paste-preview" style="margin-top:16px;display:none"></div>
        <div id="paste-mapping" style="margin-top:16px;display:none"></div>
        <div id="paste-actions" style="margin-top:16px;display:none">
          <div class="form-row" style="margin-bottom:12px">
            <div class="form-group">
              <label>合并策略</label>
              <select id="paste-merge-strategy" style="min-width:150px">
                <option value="merge">🔄 合并</option>
                <option value="overwrite">✏️ 覆盖</option>
                <option value="skip">⏭️ 跳过</option>
              </select>
            </div>
          </div>
          <button class="btn btn-primary" onclick="confirmPasteImport()">✅ 确认导入</button>
          <div id="paste-progress" style="margin-top:12px;display:none">
            <div style="background:#e9ecef;border-radius:6px;height:8px;overflow:hidden"><div id="paste-progress-bar" style="background:linear-gradient(135deg,#6366f1,#4f46e5);height:100%;width:0%;transition:width .3s"></div></div>
            <div style="font-size:12px;color:#64748b;margin-top:4px" id="paste-progress-text">导入中...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导入历史 -->
    <div class="card" style="margin-top:20px">
      <h2>📜 导入历史</h2>
      <div id="import-history"><div class="empty">暂无导入记录</div></div>
    </div>
  </div>

  <!-- ═══ 品类报告 Tab ═══ -->
  <div class="tab-panel" id="tab-category-report">
    <div class="card">
      <h2>📈 AI 品类报告</h2>
      <div class="form-row">
        <div class="form-group"><label>站点</label>
          <select id="report-marketplace">
            <option value="us">🇺🇸 美国 amazon.com</option>
            <option value="uk">🇬🇧 英国 amazon.co.uk</option>
            <option value="de">🇩🇪 德国 amazon.de</option>
            <option value="fr">🇫🇷 法国 amazon.fr</option>
            <option value="jp">🇯🇵 日本 amazon.co.jp</option>
            <option value="au">🇦🇺 澳洲 amazon.com.au</option>
            <option value="ca">🇨🇦 加拿大 amazon.ca</option>
            <option value="it">🇮🇹 意大利 amazon.it</option>
            <option value="es">🇪🇸 西班牙 amazon.es</option>
            <option value="in">🇮🇳 印度 amazon.in</option>
            <option value="br">🇧🇷 巴西 amazon.com.br</option>
            <option value="mx">🇲🇽 墨西哥 amazon.com.mx</option>
            <option value="sg">🇸🇬 新加坡 amazon.sg</option>
            <option value="ae">🇦🇪 阿联酋 amazon.ae</option>
            <option value="nl">🇳🇱 荷兰 amazon.nl</option>
            <option value="se">🇸🇪 瑞典 amazon.se</option>
            <option value="be">🇧🇪 比利时 amazon.com.be</option>
          </select>
        </div>
        <div class="form-group"><label>品类名称</label>
          <select id="report-category">
            <option value="">⏳ 加载中...</option>
          </select>
        </div>
        <div class="form-group">
          <label>数据源</label>
          <select id="report-datasource">
            <option value="rainforest">🌊 Rainforest API（推荐）</option>
            <option value="playwright">🕷️ Playwright 直爬（可能触发验证码）</option>
          </select>
        </div>
        <button class="btn btn-primary" onclick="genCategoryReport()">📊 生成报告</button>
      </div>
      <div id="category-report-content" style="margin-top:20px"></div>
    </div>
  </div>
</div>

<footer>亚马逊辅助选品系统 · 数据仅供演示</footer>

<script>
const favAsins = new Set({{ fav_asins | tojson }});

const MARKETPLACE_DOMAINS = {
  "us":"amazon.com","uk":"amazon.co.uk","de":"amazon.de","fr":"amazon.fr",
  "it":"amazon.it","es":"amazon.es","ca":"amazon.ca","jp":"amazon.co.jp",
  "au":"amazon.com.au","br":"amazon.com.br","mx":"amazon.com.mx",
  "in":"amazon.in","sg":"amazon.sg","ae":"amazon.ae","sa":"amazon.sa",
  "nl":"amazon.nl","se":"amazon.se","pl":"amazon.pl","be":"amazon.com.be"
};

const STATIC_CATEGORIES = [
  {id:"home-garden",name:"Home & Kitchen"},{id:"beauty",name:"Beauty & Personal Care"},
  {id:"hpc",name:"Health & Household"},{id:"sporting-goods",name:"Sports & Outdoors"},
  {id:"toys-and-games",name:"Toys & Games"},{id:"electronics",name:"Electronics"},
  {id:"fashion",name:"Clothing, Shoes & Jewelry"},{id:"automotive",name:"Automotive"},
  {id:"baby-products",name:"Baby"},{id:"pet-supplies",name:"Pet Supplies"},
  {id:"office-products",name:"Office Products"},{id:"tools",name:"Tools & Home Improvement"},
  {id:"garden",name:"Garden & Outdoors"},{id:"kitchen",name:"Kitchen & Dining"},
  {id:"strip-books",name:"Books"},{id:"musical-instruments",name:"Musical Instruments"},
  {id:"arts-crafts",name:"Arts, Crafts & Sewing"},{id:"grocery",name:"Grocery & Gourmet Food"},
  {id:"industrial",name:"Industrial & Scientific"},{id:"software",name:"Software"},
  {id:"videogames",name:"Video Games"},{id:"wireless",name:"Cell Phones & Accessories"},
  {id:"pc",name:"Computers"},{id:"appliances",name:"Appliances"},
  {id:"lawn-garden",name:"Patio, Lawn & Garden"},{id:"lugagge",name:"Luggage & Travel Gear"},
  {id:"handmade",name:"Handmade"}
];

function getDomain() {
  const mp = document.getElementById('marketplace').value;
  return MARKETPLACE_DOMAINS[mp] || 'amazon.com';
}

async function loadCategories(selectId, mp) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  sel.innerHTML = '<option value="">⏳ 加载中...</option>';
  try {
    const resp = await fetch('/api/categories?marketplace=' + (mp || document.getElementById('marketplace').value));
    const data = await resp.json();
    if (data.ok && data.categories.length > 0) {
      sel.innerHTML = '';
      data.categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.name;
        opt.textContent = c.name;
        sel.appendChild(opt);
      });
    } else {
      fillStaticCategories(sel);
    }
  } catch(e) {
    fillStaticCategories(sel);
  }
}

function fillStaticCategories(sel) {
  sel.innerHTML = '';
  STATIC_CATEGORIES.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = c.name;
    sel.appendChild(opt);
  });
}

// 页面加载时加载品类
loadCategories('category');
loadCategories('report-category');

// 站点切换时重新加载品类
document.getElementById('marketplace').addEventListener('change', function() {
  loadCategories('category', this.value);
});
document.getElementById('report-marketplace').addEventListener('change', function() {
  loadCategories('report-category', this.value);
});

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'favorites') loadFavorites();
}

async function doScan() {
  const btn = event ? event.target : document.querySelector('.btn-primary');
  if (btn) btn.disabled = true;
  const cat = document.getElementById('category').value;
  const pages = document.getElementById('pages').value;
  const mp = document.getElementById('marketplace').value;
  const ds = document.getElementById('datasource').value;
  const lt = document.getElementById('scan_type').value;
  const typeNames = {bestsellers:'Best Sellers 畅销榜', new_releases:'New Releases 新品榜', movers_shakers:'Movers & Shakers 飙升榜'};
  showLoading('正在扫描 ' + typeNames[lt] + ' — ' + cat + ' (' + (ds === 'playwright' ? 'Playwright' : 'Rainforest') + ') ...');
  try {
    const resp = await fetch('/api/scan?category=' + encodeURIComponent(cat) + '&pages=' + pages + '&marketplace=' + mp + '&datasource=' + ds + '&list_type=' + lt);
    const data = await resp.json();
    if (data.ok) { hideLoading(); renderScanResults(data.products, data.scan_time, data.source, typeNames[lt] + ' — ' + cat); }
    else { alert('扫描失败: ' + data.error); hideLoading(); }
  } catch(e) { alert('请求失败: ' + e.message); hideLoading(); }
  finally { if (btn) btn.disabled = false; }
}

async function doSearch() {
  const kw = document.getElementById('keyword').value.trim();
  if (!kw) { alert('请输入关键词'); return; }
  const searchBtn = event ? event.target : null;
  if (searchBtn) searchBtn.disabled = true;
  const mp = document.getElementById('marketplace').value;
  const ds = document.getElementById('datasource-search').value;
  showLoading('正在搜索 "' + kw + '" (' + (ds === 'playwright' ? 'Playwright' : 'Rainforest') + ') ...');
  try {
    const resp = await fetch('/api/search?keyword=' + encodeURIComponent(kw) + '&pages=1&marketplace=' + mp + '&datasource=' + ds);
    const data = await resp.json();
    if (data.ok) { hideLoading(); renderScanResults(data.products, data.scan_time, data.source, '搜索 "' + kw + '"'); }
    else { alert('搜索失败: ' + data.error); hideLoading(); }
  } catch(e) { alert('请求失败: ' + e.message); hideLoading(); }
  finally { if (searchBtn) searchBtn.disabled = false; }
}

function renderScanResults(products, scanTime, source, title) {
  var el = document.getElementById('results');
  var favAsins = [{% for a in fav_asins %}'{{ a }}',{% endfor %}];
  var mp = document.getElementById('marketplace').value;
  var domains = {{ RainforestCollector.MARKETPLACE_DOMAINS | tojson }};
  var domain = domains[mp] || 'amazon.com';
  var sourceLabels = {rainforest:'Rainforest', playwright:'Playwright', demo:'Demo'};
  var sourceColors = {rainforest:'badge-green', playwright:'badge-yellow', demo:'badge-red'};
  var sourceLabel = sourceLabels[source] || source;
  var sourceColor = sourceColors[source] || 'badge-green';

  var h = '<h2>🔍 ' + (title || '本次扫描结果') + ' <span style="font-size:12px;color:#6b5f82">（' + products.length + ' 个产品）</span>';
  h += ' <button class="btn btn-secondary btn-sm" onclick="window.location.reload()" style="margin-left:8px">← 返回排行榜</button></h2>';
  h += '<p style="font-size:12px;color:#64748b;margin-bottom:12px">采集时间: ' + scanTime + ' · 数据来源: <span class="badge ' + sourceColor + '">' + sourceLabel + '</span></p>';

  if (!products || !products.length) {
    el.innerHTML = h + '<div class="empty">未获取到产品</div>';
    el.style.display = 'block';
    return;
  }

  h += '<div style="overflow-x:auto"><table>';
  h += '<thead><tr><th class="checkbox-col"><input type="checkbox" id="selectAll" onchange="toggleAll(this)"></th>';
  h += '<th>#</th><th>图片</th><th>ASIN</th><th>来源</th><th>总分</th><th>售价</th><th>毛利</th><th>毛利率</th><th>月销量</th><th>BSR</th><th>评分</th><th>收藏</th><th>操作</th></tr></thead><tbody>';

  for (var i = 0; i < products.length; i++) {
    var p = products[i];
    var imgHtml = p.image_url
      ? '<a href="https://www.' + domain + '/dp/' + p.asin + '" target="_blank"><img src="' + p.image_url + '" alt="" style="width:50px;height:50px;object-fit:cover;border-radius:6px;border:1px solid #e2e8f0;" onerror="this.src=\\'https://via.placeholder.com/50x50/f1f5f9/94a3b8?text=📦\\'"></a>'
      : '<a href="https://www.' + domain + '/dp/' + p.asin + '" target="_blank" style="display:inline-block;width:50px;height:50px;background:#f1f5f9;border-radius:6px;text-align:center;line-height:50px;font-size:20px;text-decoration:none">📦</a>';
    var scoreClass = p.total_score >= 75 ? 'score-high' : (p.total_score >= 60 ? 'score-mid' : 'score-low');
    var marginClass = p.profit_margin >= 30 ? 'badge-green' : (p.profit_margin >= 20 ? 'badge-yellow' : 'badge-red');
    var favClass = favAsins.indexOf(p.asin) >= 0 ? 'active' : '';
    var ds = p.data_source || source;
    var dsLabel = sourceLabels[ds] || ds;
    var dsColor = sourceColors[ds] || 'badge-green';

    h += '<tr>';
    h += '<td class="checkbox-col"><input type="checkbox" class="asin-cb" value="' + p.asin + '"></td>';
    h += '<td>' + (i + 1) + '</td>';
    h += '<td>' + imgHtml + '</td>';
    h += '<td><a href="https://www.' + domain + '/dp/' + p.asin + '" target="_blank" style="color:#6366f1;font-weight:500"><code>' + p.asin + '</code></a></td>';
    h += '<td><span class="badge ' + dsColor + '">' + dsLabel + '</span></td>';
    h += '<td><span class="score ' + scoreClass + '">' + (p.total_score || 0) + '</span></td>';
    h += '<td>$' + (p.price || 0).toFixed(2) + '</td>';
    h += '<td>$' + (p.gross_profit || 0).toFixed(2) + '</td>';
    h += '<td><span class="badge ' + marginClass + '">' + (p.profit_margin || 0).toFixed(1) + '%</span></td>';
    h += '<td>' + (p.monthly_sales_est || 0) + '</td>';
    h += '<td>#' + (p.bsr || '-') + '</td>';
    h += '<td>' + (p.rating || 0) + '/5.0</td>';
    h += '<td><button class="fav-btn ' + favClass + '" onclick="toggleFav(\'' + p.asin + '\',this)">⭐</button></td>';
    h += '<td style="white-space:nowrap"><button class="btn btn-sm btn-secondary" style="padding:2px 6px;font-size:14px" onclick="quickAlert(\'' + p.asin + '\',\'' + (p.price || 0).toFixed(2) + '\')" title="快速预警">🔔</button> <a class="detail-link" href="/detail/' + p.asin + '">详情 →</a></td>';
    h += '</tr>';
  }
  h += '</tbody></table></div>';
  h += '<div class="actions"><a href="/export" class="btn btn-primary">📥 导出报告</a><a href="/api/export" class="btn btn-secondary" download>📄 下载 Markdown</a><button class="btn btn-secondary" onclick="compareSelected()">📊 对比选中</button></div>';

  el.innerHTML = h;
  el.style.display = 'block';
}

function showLoading(t) { document.getElementById('loadingText').textContent = t; document.getElementById('loading').classList.add('show'); document.getElementById('results').style.display = 'none'; }
function hideLoading() { document.getElementById('loading').classList.remove('show'); document.getElementById('results').style.display = 'block'; }

function toggleAll(cb) { document.querySelectorAll('.asin-cb').forEach(c => c.checked = cb.checked); }

function getSelected() {
  return Array.from(document.querySelectorAll('.asin-cb:checked')).map(c => c.value);
}

async function compareSelected() {
  const asins = getSelected();
  if (asins.length < 2) { alert('请至少选择 2 个产品进行对比'); return; }
  const form = document.createElement('form');
  form.method = 'POST'; form.action = '/compare';
  asins.forEach(a => { const i = document.createElement('input'); i.type='hidden'; i.name='asins'; i.value=a; form.appendChild(i); });
  document.body.appendChild(form); form.submit();
}

async function toggleFav(asin, btn) {
  const isFav = favAsins.has(asin);
  const resp = await fetch(isFav ? '/api/favorite/' + asin : '/api/favorite/add', {
    method: isFav ? 'DELETE' : 'POST',
    headers: {'Content-Type': 'application/json'},
    body: isFav ? null : JSON.stringify({asin})
  });
  const data = await resp.json();
  if (data.ok) {
    if (isFav) { favAsins.delete(asin); btn.classList.remove('active'); }
    else { favAsins.add(asin); btn.classList.add('active'); }
  }
}

async function loadFavorites() {
  const resp = await fetch('/api/favorites');
  const data = await resp.json();
  const el = document.getElementById('fav-content');
  if (!data.favorites || data.favorites.length === 0) { el.innerHTML = '<div class="empty">暂无收藏</div>'; return; }
  let html = '<table><thead><tr><th>ASIN</th><th>标题</th><th>分组</th><th>售价</th><th>总分</th><th>操作</th></tr></thead><tbody>';
  data.favorites.forEach(f => {
    const p = data.products[f.asin] || {};
    html += `<tr>
      <td><code>${f.asin}</code></td>
      <td>${p.title || '-'}</td>
      <td>${f.group_name}</td>
      <td>${p.price ? '$' + p.price.toFixed(2) : '-'}</td>
      <td>${p.total_score || '-'}</td>
      <td><a class="detail-link" href="/detail/${f.asin}">详情</a> <button class="btn btn-danger btn-sm" onclick="removeFav('${f.asin}')">移除</button></td>
    </tr>`;
  });
  html += '</tbody></table>';
  el.innerHTML = html;
}

async function removeFav(asin) {
  await fetch('/api/favorite/' + asin, {method:'DELETE'});
  loadFavorites();
}

function onAlertTypeChange() {
  const t = document.getElementById('alert-type').value;
  document.getElementById('threshold-group').style.display = t === 'below_target' ? 'none' : '';
  document.getElementById('target-group').style.display = t === 'below_target' ? '' : 'none';
}

async function addAlert() {
  const asin = document.getElementById('alert-asin').value.trim();
  if (!asin) { alert('请输入 ASIN'); return; }
  const alert_type = document.getElementById('alert-type').value;
  const threshold = parseFloat(document.getElementById('alert-threshold').value) || 10;
  const target = parseFloat(document.getElementById('alert-target').value) || null;
  const resp = await fetch('/api/alerts', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({asin, alert_type, threshold_pct: threshold, target_price: target})
  });
  const data = await resp.json();
  if (data.ok) { document.getElementById('alert-asin').value = ''; loadAlerts(); }
  else { alert(data.error || '添加失败'); }
}

async function loadAlerts() {
  const resp = await fetch('/api/alerts');
  const data = await resp.json();
  const el = document.getElementById('alerts-list');
  if (!data.alerts || data.alerts.length === 0) { el.innerHTML = '<div class="empty">暂无价格预警规则</div>'; return; }
  const typeMap = {price_drop: '📉 价格下跌', price_surge: '📈 价格上涨', below_target: '🎯 低于目标价'};
  let html = '<table><thead><tr><th>ASIN</th><th>类型</th><th>阈值/目标</th><th>状态</th><th>创建时间</th><th>触发时间</th><th>操作</th></tr></thead><tbody>';
  data.alerts.forEach(a => {
    const active = a.is_active ? '<span class="badge badge-green">正常</span>' : '<span class="badge badge-red">已暂停</span>';
    const threshold = a.alert_type === 'below_target' ? '$' + (a.target_price || 0).toFixed(2) : a.threshold_pct + '%';
    html += '<tr><td><code>' + a.asin + '</code></td><td>' + (typeMap[a.alert_type] || a.alert_type) + '</td><td>' + threshold + '</td><td>' + active + '</td><td>' + (a.created_at || '').slice(0, 16) + '</td><td>' + (a.triggered_at ? a.triggered_at.slice(0, 16) : '-') + '</td><td><button class="btn btn-danger btn-sm" onclick="delAlert(' + a.id + ')">删除</button></td></tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;
}

async function delAlert(id) {
  await fetch('/api/alerts/' + id, {method: 'DELETE'});
  loadAlerts();
}

async function addBsrAlert() {
  const asin = document.getElementById('bsr-alert-asin').value.trim();
  if (!asin) { alert('请输入 ASIN'); return; }
  const alert_type = document.getElementById('bsr-alert-type').value;
  const threshold = parseFloat(document.getElementById('bsr-threshold').value) || 20;
  const resp = await fetch('/api/bsr-alerts', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({asin, alert_type, threshold_pct: threshold})
  });
  const data = await resp.json();
  if (data.ok) { document.getElementById('bsr-alert-asin').value = ''; loadBsrAlerts(); }
  else { alert(data.error || '添加失败'); }
}

async function loadBsrAlerts() {
  const resp = await fetch('/api/bsr-alerts');
  const data = await resp.json();
  const el = document.getElementById('bsr-alerts-list');
  if (!data.alerts || data.alerts.length === 0) { el.innerHTML = '<div class="empty">暂无 BSR 监控规则</div>'; return; }
  const typeMap = {bsr_surge: '🚀 排名上升', bsr_drop: '📉 排名下降'};
  let html = '<table><thead><tr><th>ASIN</th><th>类型</th><th>阈值</th><th>状态</th><th>创建时间</th><th>触发时间</th><th>操作</th></tr></thead><tbody>';
  data.alerts.forEach(a => {
    const active = a.is_active ? '<span class="badge badge-green">正常</span>' : '<span class="badge badge-red">已暂停</span>';
    html += '<tr><td><code>' + a.asin + '</code></td><td>' + (typeMap[a.alert_type] || a.alert_type) + '</td><td>' + a.threshold_pct + '%</td><td>' + active + '</td><td>' + (a.created_at || '').slice(0, 16) + '</td><td>' + (a.triggered_at ? a.triggered_at.slice(0, 16) : '-') + '</td><td><button class="btn btn-danger btn-sm" onclick="delBsrAlert(' + a.id + ')">删除</button></td></tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;
}

async function delBsrAlert(id) {
  await fetch('/api/bsr-alerts/' + id, {method: 'DELETE'});
  loadBsrAlerts();
}

async function checkAllAlerts() {
  const el = document.getElementById('triggered-list');
  el.innerHTML = '<div class="loading show"><div class="spinner"></div><p>正在检查预警...</p></div>';
  const [priceResp, bsrResp] = await Promise.all([fetch('/api/alerts/check'), fetch('/api/bsr-alerts/check')]);
  const priceData = await priceResp.json();
  const bsrData = await bsrResp.json();
  const all = [...(priceData.triggered || []).map(t => ({...t, _type: 'price'})), ...(bsrData.triggered || []).map(t => ({...t, _type: 'bsr'}))];
  if (all.length === 0) { el.innerHTML = '<div class="empty" style="color:#10b981">✅ 所有预警正常，暂无触发</div>'; return; }
  const typeMap = {price_drop: '📉 价格下跌', price_surge: '📈 价格上涨', below_target: '🎯 低于目标价', bsr_surge: '🚀 BSR排名上升', bsr_drop: '📉 BSR排名下降'};
  let html = '<table><thead><tr><th>类型</th><th>ASIN</th><th>详情</th></tr></thead><tbody>';
  all.forEach(t => {
    let detail = '';
    if (t._type === 'price') {
      detail = '当前 $' + (t.current_price||0).toFixed(2) + ' → 变动 ' + t.change_pct + '%';
      if (t.alert_type === 'below_target') detail = '当前 $' + (t.current_price||0).toFixed(2) + ' < 目标 $' + (t.target_price||0).toFixed(2);
    } else {
      detail = '当前 #' + t.current_bsr + ' (之前 #' + t.prev_bsr + ') → 变动 ' + t.change_pct + '%';
    }
    html += '<tr><td><span class="badge badge-red">' + (typeMap[t.alert_type]||t.alert_type) + '</span></td><td><code>' + t.asin + '</code></td><td>' + detail + '</td></tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;
  // refresh lists
  loadAlerts(); loadBsrAlerts();
}

function quickAlert(asin, price) {
  // Switch to trend monitor tab
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab')[3].classList.add('active');
  document.getElementById('tab-trend-monitor').classList.add('active');
  document.getElementById('alert-asin').value = asin;
  document.getElementById('alert-type').value = 'below_target';
  onAlertTypeChange();
  document.getElementById('alert-target').value = (parseFloat(price) * 0.9).toFixed(2);
  loadAlerts(); loadBsrAlerts();
}

async function loadBsrChart() {
  const asin = document.getElementById('bsr-trend-asin').value.trim();
  if (!asin) { alert('请输入 ASIN'); return; }
  const resp = await fetch('/api/trend/' + asin);
  const data = await resp.json();
  const el = document.getElementById('bsr-chart-area');
  const history = data.history || [];
  if (history.length < 2) { el.innerHTML = '<div class="empty">暂无足够数据</div>'; return; }
  // CSS bar chart for BSR
  const bsrValues = history.map(h => h.bsr).filter(v => v && v > 0);
  if (bsrValues.length < 2) { el.innerHTML = '<div class="empty">暂无 BSR 数据</div>'; return; }
  const maxBsr = Math.max(...bsrValues);
  let html = '<div style="display:flex;align-items:flex-end;gap:4px;height:120px;padding:10px 0">';
  history.forEach((h, i) => {
    if (!h.bsr || h.bsr <= 0) return;
    const height = Math.max(8, (h.bsr / maxBsr) * 100);
    const color = i === history.length - 1 ? '#6366f1' : '#c4b5fd';
    html += '<div title="BSR #' + h.bsr + '" style="flex:1;max-width:30px;height:' + height + '%;background:' + color + ';border-radius:3px 3px 0 0;min-height:4px;transition:height .3s"></div>';
  });
  html += '</div>';
  html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8"><span>' + history[0].recorded_at.slice(5,10) + '</span><span>BSR #' + bsrValues[bsrValues.length-1] + '</span><span>' + history[history.length-1].recorded_at.slice(5,10) + '</span></div>';
  el.innerHTML = html;
}

// Load alerts when switching to trend tab
const origSwitchTab = switchTab;
switchTab = function(name) {
  origSwitchTab(name);
  if (name === 'trend-monitor') { loadAlerts(); loadBsrAlerts(); }
};

async function genCategoryReport() {
  const cat = document.getElementById('report-category').value;
  const mp = document.getElementById('report-marketplace').value;
  const ds = document.getElementById('report-datasource').value;
  const el = document.getElementById('category-report-content');
  el.innerHTML = '<div class="loading show"><div class="spinner"></div><p>正在生成 ' + cat + ' 品类报告...</p></div>';
  try {
    const resp = await fetch('/api/report/category', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({category: cat, marketplace: mp})
    });
    const data = await resp.json();
    if (data.ok) el.innerHTML = '<div style="background:rgba(30,22,60,.4);border-radius:8px;padding:20px;white-space:pre-wrap;line-height:1.8;font-size:14px">' + data.report + '</div>';
    else el.innerHTML = '<div class="empty">' + data.error + '</div>';
  } catch(e) { el.innerHTML = '<div class="empty">生成失败: ' + e.message + '</div>'; }
}

// ═══ 数据导入功能 ═══
let importData = [];
let importMapping = {};
let pasteData = [];
let pasteMapping = {};
let importHistory = JSON.parse(localStorage.getItem('importHistory') || '[]');

const FIELD_OPTIONS = [
  {value:'', label:'— 跳过 —'},
  {value:'asin', label:'ASIN'},
  {value:'title', label:'商品名称'},
  {value:'brand', label:'品牌'},
  {value:'category', label:'品类'},
  {value:'price', label:'价格'},
  {value:'rating', label:'评分'},
  {value:'reviews_count', label:'评论数'},
  {value:'bsr', label:'BSR排名'},
  {value:'monthly_sales_est', label:'月销量'},
  {value:'monthly_revenue_est', label:'月营收'},
  {value:'search_volume', label:'搜索量'},
  {value:'click_share', label:'点击份额'},
  {value:'conversion_rate', label:'转化率'},
  {value:'date_first_available', label:'上架日期'},
  {value:'seller_count', label:'卖家数量'},
  {value:'image_url', label:'图片URL'},
];

const AUTO_MAP = {
  'asin':'asin','ASIN':'asin','title':'title','商品名称':'title','item_name':'title','product_title':'title',
  'brand':'brand','品牌':'brand','category':'category','品类':'category','分类':'category',
  'price':'price','价格':'price','average_price':'price','avg_price':'price','平均价格':'price',
  'rating':'rating','评分':'rating','星级':'rating','stars':'rating',
  'reviews_count':'reviews_count','评论数':'reviews_count','reviews':'reviews_count','评论数量':'reviews_count',
  'bsr':'bsr','排名':'bsr','rank':'bsr','best_sellers_rank':'bsr',
  'monthly_sales_est':'monthly_sales_est','月销量':'monthly_sales_est','estimated_monthly_sales':'monthly_sales_est',
  'monthly_revenue_est':'monthly_revenue_est','月营收':'monthly_revenue_est',
  'search_volume':'search_volume','搜索量':'search_volume','search_volume_90d':'search_volume',
  'click_share':'click_share','点击份额':'click_share','click_share_%':'click_share',
  'conversion_rate':'conversion_rate','转化率':'conversion_rate','商品转化率':'conversion_rate',
  'date_first_available':'date_first_available','发布日期':'date_first_available','上架日期':'date_first_available',
  'seller_count':'seller_count','卖家数量':'seller_count',
  'image_url':'image_url','图片':'image_url','image':'image_url',
};

function autoMapColumns(cols) {
  const mapping = {};
  cols.forEach(c => { mapping[c] = AUTO_MAP[c] || ''; });
  return mapping;
}

function renderMapping(cols, containerId, mappingObj, source) {
  const el = document.getElementById(containerId);
  el.style.display = 'block';
  let html = '<h3 style="font-size:14px;margin-bottom:10px;color:#4338ca">📋 列映射</h3>';
  html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;max-height:300px;overflow-y:auto">';
  cols.forEach(col => {
    const auto = mappingObj[col] || '';
    html += '<div style="display:flex;align-items:center;gap:6px"><span style="font-size:12px;color:#64748b;min-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + col + '">' + col + '</span>';
    html += '<select data-col="' + col + '" style="font-size:12px;padding:3px 6px;min-width:0;flex:1" onchange="' + source + 'Mapping[\\x27' + col + '\\x27]=this.value">';
    FIELD_OPTIONS.forEach(opt => {
      html += '<option value="' + opt.value + '"' + (auto === opt.value ? ' selected' : '') + '>' + opt.label + '</option>';
    });
    html += '</select></div>';
  });
  html += '</div>';
  el.innerHTML = html;
}

function renderPreview(rows, cols, containerId) {
  const el = document.getElementById(containerId);
  el.style.display = 'block';
  const preview = rows.slice(0, 5);
  let html = '<div style="font-size:12px;color:#64748b;margin-bottom:8px">共 ' + rows.length + ' 行数据，预览前 5 行：</div>';
  html += '<div style="overflow-x:auto"><table style="font-size:12px"><thead><tr>';
  cols.forEach(c => { html += '<th>' + c + '</th>'; });
  html += '</tr></thead><tbody>';
  preview.forEach(r => {
    html += '<tr>';
    cols.forEach(c => { html += '<td>' + (r[c] || '') + '</td>'; });
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  el.innerHTML = html;
}

function handleDrop(e) {
  e.preventDefault();
  e.currentTarget.style.borderColor = '#c4b5fd';
  e.currentTarget.style.background = '#faf5ff';
  const file = e.dataTransfer.files[0];
  if (file) handleFileUpload(file);
}

async function handleFileUpload(file) {
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) { alert('文件超过 10MB 限制'); return; }
  const formData = new FormData();
  formData.append('file', file);
  try {
    const resp = await fetch('/api/import/upload?preview=true', { method: 'POST', body: formData });
    const data = await resp.json();
    if (!data.ok) { alert('解析失败: ' + data.error); return; }
    importData = data.rows;
    importMapping = autoMapColumns(data.columns);
    renderPreview(data.rows, data.columns, 'file-preview');
    renderMapping(data.columns, 'column-mapping', importMapping, 'import');
    document.getElementById('import-actions').style.display = 'block';
  } catch(e) { alert('上传失败: ' + e.message); }
}

async function confirmImport() {
  const strategy = document.getElementById('merge-strategy').value;
  const mapping = {};
  document.querySelectorAll('#column-mapping select').forEach(sel => {
    mapping[sel.dataset.col] = sel.value;
  });
  const btn = document.getElementById('confirm-import-btn');
  btn.disabled = true;
  document.getElementById('import-progress').style.display = 'block';
  document.getElementById('progress-bar').style.width = '30%';
  try {
    const resp = await fetch('/api/import/confirm', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ columns_mapping: mapping, merge_strategy: strategy, data: importData })
    });
    document.getElementById('progress-bar').style.width = '100%';
    const data = await resp.json();
    if (data.ok) {
      document.getElementById('progress-text').textContent = '✅ 导入完成！新增 ' + data.result.imported + ' / 更新 ' + data.result.updated + ' / 跳过 ' + data.result.skipped;
      importHistory.unshift({ time: new Date().toLocaleString(), source: '文件上传', count: data.result.imported + data.result.updated });
      importHistory = importHistory.slice(0, 5);
      localStorage.setItem('importHistory', JSON.stringify(importHistory));
      renderImportHistory();
    } else {
      document.getElementById('progress-text').textContent = '❌ ' + data.error;
    }
  } catch(e) {
    document.getElementById('progress-text').textContent = '❌ ' + e.message;
  }
  btn.disabled = false;
}

async function parsePasteData() {
  const raw = document.getElementById('paste-data').value.trim();
  if (!raw) { alert('请粘贴数据'); return; }
  try {
    const resp = await fetch('/api/import/paste', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ raw_text: raw, merge_strategy: 'merge' })
    });
    const data = await resp.json();
    if (!data.ok) { alert('解析失败: ' + data.error); return; }
    pasteData = data.rows;
    pasteMapping = autoMapColumns(data.columns);
    renderPreview(data.rows, data.columns, 'paste-preview');
    renderMapping(data.columns, 'paste-mapping', pasteMapping, 'paste');
    document.getElementById('paste-actions').style.display = 'block';
  } catch(e) { alert('解析失败: ' + e.message); }
}

async function confirmPasteImport() {
  const strategy = document.getElementById('paste-merge-strategy').value;
  const mapping = {};
  document.querySelectorAll('#paste-mapping select').forEach(sel => {
    mapping[sel.dataset.col] = sel.value;
  });
  document.getElementById('paste-progress').style.display = 'block';
  document.getElementById('paste-progress-bar').style.width = '30%';
  try {
    const resp = await fetch('/api/import/confirm', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ columns_mapping: mapping, merge_strategy: strategy, data: pasteData })
    });
    document.getElementById('paste-progress-bar').style.width = '100%';
    const data = await resp.json();
    if (data.ok) {
      document.getElementById('paste-progress-text').textContent = '✅ 导入完成！新增 ' + data.result.imported + ' / 更新 ' + data.result.updated + ' / 跳过 ' + data.result.skipped;
      importHistory.unshift({ time: new Date().toLocaleString(), source: '粘贴导入', count: data.result.imported + data.result.updated });
      importHistory = importHistory.slice(0, 5);
      localStorage.setItem('importHistory', JSON.stringify(importHistory));
      renderImportHistory();
    } else {
      document.getElementById('paste-progress-text').textContent = '❌ ' + data.error;
    }
  } catch(e) {
    document.getElementById('paste-progress-text').textContent = '❌ ' + e.message;
  }
}

function renderImportHistory() {
  const el = document.getElementById('import-history');
  if (importHistory.length === 0) { el.innerHTML = '<div class="empty">暂无导入记录</div>'; return; }
  let html = '<table><thead><tr><th>时间</th><th>来源</th><th>导入数量</th></tr></thead><tbody>';
  importHistory.forEach(h => {
    html += '<tr><td>' + h.time + '</td><td>' + h.source + '</td><td>' + h.count + '</td></tr>';
  });
  html += '</tbody></table>';
  el.innerHTML = html;
}
renderImportHistory();
</script>
</body>
</html>"""

DETAIL_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
""" + COMMON_HEAD + """
<title>{{ p.title }} - 产品详情</title>
</head>
<body>
<div class="header">
  <div class="container">
    <a href="/">← 返回列表</a>
    <h1 style="margin-top:8px;font-size:18px">📦 {{ p.title }}</h1>
  </div>
</div>

<div class="container">
  <div class="card">
    <h2>📋 基本信息</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px">
      <div><label style="font-size:12px;color:#8b7fa8">ASIN</label><div style="font-size:17px;font-weight:600">{{ p.asin }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">品牌</label><div style="font-size:17px;font-weight:600">{{ p.brand or 'N/A' }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">品类</label><div style="font-size:17px;font-weight:600">{{ p.category or 'N/A' }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">售价</label><div style="font-size:17px;font-weight:600;color:#6ee7b7">${{ "%.2f"|format(p.price) }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">评分</label><div style="font-size:17px;font-weight:600">{{ p.rating }}/5.0</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">评论数</label><div style="font-size:17px;font-weight:600">{{ p.reviews_count }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">BSR 排名</label><div style="font-size:17px;font-weight:600">#{{ p.bsr }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">月销量估算</label><div style="font-size:17px;font-weight:600">{{ p.monthly_sales_est }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">卖家数量</label><div style="font-size:17px;font-weight:600">{{ p.seller_count }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">首次上架</label><div style="font-size:17px;font-weight:600">{{ p.date_first_available or 'N/A' }}</div></div>
    </div>
  </div>

  <div class="card">
    <h2>📊 多维评分</h2>
    <div style="max-width:500px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <span style="width:50px;font-size:13px;color:#8b7fa8">需求</span>
        <div style="flex:1;height:8px;background:rgba(139,92,246,.1);border-radius:4px;overflow:hidden"><div style="width:{{ p.demand_score }}%;height:100%;background:#60a5fa;border-radius:4px"></div></div>
        <span style="width:35px;text-align:right;font-weight:600;font-size:14px">{{ p.demand_score }}</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <span style="width:50px;font-size:13px;color:#8b7fa8">竞争</span>
        <div style="flex:1;height:8px;background:rgba(139,92,246,.1);border-radius:4px;overflow:hidden"><div style="width:{{ p.competition_score }}%;height:100%;background:#34d399;border-radius:4px"></div></div>
        <span style="width:35px;text-align:right;font-weight:600;font-size:14px">{{ p.competition_score }}</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <span style="width:50px;font-size:13px;color:#8b7fa8">利润</span>
        <div style="flex:1;height:8px;background:rgba(139,92,246,.1);border-radius:4px;overflow:hidden"><div style="width:{{ p.profit_score }}%;height:100%;background:#fbbf24;border-radius:4px"></div></div>
        <span style="width:35px;text-align:right;font-weight:600;font-size:14px">{{ p.profit_score }}</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <span style="width:50px;font-size:13px;color:#8b7fa8">机会</span>
        <div style="flex:1;height:8px;background:rgba(139,92,246,.1);border-radius:4px;overflow:hidden"><div style="width:{{ p.opportunity_score }}%;height:100%;background:#a78bfa;border-radius:4px"></div></div>
        <span style="width:35px;text-align:right;font-weight:600;font-size:14px">{{ p.opportunity_score }}</span>
      </div>
    </div>
    <div style="margin-top:16px;text-align:center;font-size:28px;font-weight:700;color:{{ '#6ee7b7' if p.total_score >= 75 else ('#fcd34d' if p.total_score >= 60 else '#fca5a5') }}">
      总分 {{ p.total_score }}
    </div>
  </div>

  <!-- 雷达图 + 价格趋势 -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div class="card">
      <h2>🎯 评分雷达图</h2>
      <canvas id="radarChart"></canvas>
    </div>
    <div class="card">
      <h2>📈 价格趋势</h2>
      <canvas id="trendChart"></canvas>
    </div>
  </div>

  <div class="card">
    <h2>💰 利润分析</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px">
      <div><label style="font-size:12px;color:#8b7fa8">售价</label><div style="font-size:17px;font-weight:600">${{ "%.2f"|format(p.price) }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">佣金 (15%)</label><div style="font-size:17px;font-weight:600;color:#fca5a5">-${{ "%.2f"|format(p.referral_fee) }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">FBA 配送费</label><div style="font-size:17px;font-weight:600;color:#fca5a5">-${{ "%.2f"|format(p.fba_fee) }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">月仓储费</label><div style="font-size:17px;font-weight:600;color:#fca5a5">-${{ "%.2f"|format(p.storage_fee) }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">采购成本 (估)</label><div style="font-size:17px;font-weight:600;color:#fca5a5">-${{ "%.2f"|format(p.estimated_cost) }}</div></div>
      <div><label style="font-size:12px;color:#8b7fa8">毛利</label><div style="font-size:17px;font-weight:600;color:#6ee7b7">${{ "%.2f"|format(p.gross_profit) }}</div></div>
    </div>
    <div style="margin-top:16px;text-align:center;font-size:24px;font-weight:700">
      毛利率 <span style="color:{{ '#6ee7b7' if p.profit_margin >= 30 else '#fca5a5' }}">{{ "%.1f"|format(p.profit_margin) }}%</span>
    </div>
  </div>

  <div class="card">
    <h2>🔔 快速创建预警</h2>
    <div class="form-row">
      <div class="form-group"><label>ASIN</label><input type="text" value="{{ p.asin }}" readonly style="min-width:140px;background:#f8fafc"></div>
      <div class="form-group"><label>预警类型</label>
        <select id="detail-alert-type" style="min-width:150px">
          <option value="price_drop">📉 价格下跌</option>
          <option value="price_surge">📈 价格上涨</option>
          <option value="below_target">🎯 低于目标价</option>
        </select>
      </div>
      <div class="form-group"><label>阈值/目标</label><input type="number" id="detail-alert-val" value="10" step="0.01" style="min-width:100px"></div>
      <button class="btn btn-primary" onclick="createDetailAlert()">创建预警</button>
    </div>
  </div>

  <div class="card">
    <h2>🤖 AI 分析</h2>
    {% if p.ai_analysis %}
    <div style="background:rgba(30,22,60,.4);border-radius:8px;padding:16px;font-size:14px;line-height:1.8;white-space:pre-wrap">{{ p.ai_analysis }}</div>
    {% else %}
    <div class="empty">暂无 AI 分析，请配置 AI API Key 后重新扫描</div>
    {% endif %}
  </div>
</div>

<script>
// 雷达图
new Chart(document.getElementById('radarChart'), {
  type: 'radar',
  data: {
    labels: ['需求', '竞争', '利润', '机会'],
    datasets: [{
      data: [{{ p.demand_score }}, {{ p.competition_score }}, {{ p.profit_score }}, {{ p.opportunity_score }}],
      backgroundColor: 'rgba(139,92,246,.2)',
      borderColor: '#8b5cf6',
      pointBackgroundColor: '#8b5cf6',
      borderWidth: 2
    }]
  },
  options: {
    responsive: true,
    scales: { r: { min: 0, max: 100, ticks: { color: '#8b7fa8', backdropColor: 'transparent' }, grid: { color: 'rgba(139,92,246,.15)' }, pointLabels: { color: '#c4b5fd', font: { size: 13 } } } },
    plugins: { legend: { display: false } }
  }
});

// 价格趋势
const trendData = {{ trend_data | tojson }};
if (trendData.length > 1) {
  new Chart(document.getElementById('trendChart'), {
    type: 'line',
    data: {
      labels: trendData.map(d => d.recorded_at ? d.recorded_at.slice(5,16) : ''),
      datasets: [{
        label: '价格',
        data: trendData.map(d => d.price),
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139,92,246,.1)',
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#8b5cf6'
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: { ticks: { color: '#8b7fa8', maxRotation: 45 }, grid: { color: 'rgba(139,92,246,.06)' } },
        y: { ticks: { color: '#8b7fa8', callback: v => '$' + v }, grid: { color: 'rgba(139,92,246,.1)' } }
      },
      plugins: { legend: { labels: { color: '#c4b5fd' } } }
    }
  });
} else {
  document.getElementById('trendChart').parentElement.innerHTML += '<div class="empty">暂无足够的价格历史数据</div>';
}

async function createDetailAlert() {
  const asin = '{{ p.asin }}';
  const alert_type = document.getElementById('detail-alert-type').value;
  const val = parseFloat(document.getElementById('detail-alert-val').value);
  let body;
  if (alert_type === 'below_target') {
    body = {asin, alert_type, target_price: val};
  } else {
    body = {asin, alert_type, threshold_pct: val};
  }
  const resp = await fetch('/api/alerts', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const data = await resp.json();
  if (data.ok) alert('预警创建成功！');
  else alert(data.error || '创建失败');
}
</script>
</body>
</html>"""

COMPARE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
""" + COMMON_HEAD + """
<title>竞品对比</title>
</head>
<body>
<div class="header">
  <div class="container">
    <a href="/">← 返回列表</a>
    <h1 style="margin-top:8px;font-size:20px">📊 竞品对比分析</h1>
  </div>
</div>

<div class="container">
  {% if products|length >= 2 %}
  <div class="card">
    <h2>🎯 综合评分雷达图</h2>
    <div style="max-width:600px;margin:0 auto"><canvas id="compareRadar"></canvas></div>
  </div>

  <div class="card">
    <h2>📋 横向对比</h2>
    <div style="overflow-x:auto">
    <table>
      <thead>
        <tr><th>指标</th>{% for p in products %}<th>{{ p.asin }}<br><span style="font-weight:400;font-size:11px">{{ (p.title or '')[:30] }}</span></th>{% endfor %}</tr>
      </thead>
      <tbody>
        <tr><td>售价</td>{% for p in products %}<td>${{ "%.2f"|format(p.price) }}</td>{% endfor %}</tr>
        <tr><td>毛利</td>{% for p in products %}<td>${{ "%.2f"|format(p.gross_profit) }}</td>{% endfor %}</tr>
        <tr><td>毛利率</td>{% for p in products %}<td>{{ "%.1f"|format(p.profit_margin) }}%</td>{% endfor %}</tr>
        <tr><td>月销量</td>{% for p in products %}<td>{{ p.monthly_sales_est }}</td>{% endfor %}</tr>
        <tr><td>BSR</td>{% for p in products %}<td>#{{ p.bsr }}</td>{% endfor %}</tr>
        <tr><td>评分</td>{% for p in products %}<td>{{ p.rating }}/5.0</td>{% endfor %}</tr>
        <tr><td>评论数</td>{% for p in products %}<td>{{ p.reviews_count }}</td>{% endfor %}</tr>
        <tr><td>卖家数</td>{% for p in products %}<td>{{ p.seller_count }}</td>{% endfor %}</tr>
        <tr><td>需求分</td>{% for p in products %}<td>{{ p.demand_score }}</td>{% endfor %}</tr>
        <tr><td>竞争分</td>{% for p in products %}<td>{{ p.competition_score }}</td>{% endfor %}</tr>
        <tr><td>利润分</td>{% for p in products %}<td>{{ p.profit_score }}</td>{% endfor %}</tr>
        <tr><td>机会分</td>{% for p in products %}<td>{{ p.opportunity_score }}</td>{% endfor %}</tr>
        <tr><td style="font-weight:700">总分</td>{% for p in products %}<td style="font-weight:700;font-size:16px;color:{{ '#6ee7b7' if p.total_score >= 75 else '#fcd34d' }}">{{ p.total_score }}</td>{% endfor %}</tr>
        <tr><td>操作</td>{% for p in products %}<td><a class="detail-link" href="/detail/{{ p.asin }}">详情 →</a></td>{% endfor %}</tr>
      </tbody>
    </table>
    </div>
  </div>
  {% else %}
  <div class="card"><div class="empty">请至少选择 2 个产品进行对比</div></div>
  {% endif %}
</div>

{% if products|length >= 2 %}
<script>
const colors = ['#8b5cf6','#60a5fa','#34d399','#fbbf24','#f472b6','#fb923c'];
new Chart(document.getElementById('compareRadar'), {
  type: 'radar',
  data: {
    labels: ['需求','竞争','利润','机会'],
    datasets: [
      {% for p in products %}
      { label: '{{ p.asin }}', data: [{{ p.demand_score }},{{ p.competition_score }},{{ p.profit_score }},{{ p.opportunity_score }}],
        backgroundColor: colors[{{ loop.index0 }} % colors.length] + '33',
        borderColor: colors[{{ loop.index0 }} % colors.length],
        pointBackgroundColor: colors[{{ loop.index0 }} % colors.length],
        borderWidth: 2 },
      {% endfor %}
    ]
  },
  options: {
    responsive: true,
    scales: { r: { min: 0, max: 100, ticks: { color: '#8b7fa8', backdropColor: 'transparent' }, grid: { color: 'rgba(139,92,246,.15)' }, pointLabels: { color: '#c4b5fd', font: { size: 13 } } } },
    plugins: { legend: { labels: { color: '#c4b5fd' } } }
  }
});
</script>
{% endif %}
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
    keepa = KeepaCollector(api_key=config.get("keepa", {}).get("api_key", ""))
    for p in products:
        keepa.enrich_product(p)

    products = calculate_profit_batch(products)
    before = len(products)
    products = filter_products(products, config)

    scorer = Scorer(config)
    products = scorer.score_products(products)

    analyzer = AIAnalyzer(config)
    for p in products[:10]:
        analyzer.analyze_product(p)

    saved = save_products(products)
    save_scan(scan_type, query, pages, before, len(products))

    # 保存价格快照
    save_price_snapshot(products)

    return products


def _get_fav_asins():
    """获取所有收藏的 ASIN 集合"""
    favs = get_favorites()
    return [f['asin'] for f in favs]


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
    fav_asins = _get_fav_asins()
    marketplace = request.args.get("marketplace", "us")
    # 为产品添加 amazon_domain 用于链接生成
    from src.collectors.rainforest import RainforestCollector
    for p in products:
        mp = p.get('marketplace', 'us')
        p['amazon_domain'] = RainforestCollector.MARKETPLACE_DOMAINS.get(mp, 'amazon.com')
    return render_template_string(INDEX_HTML, products=products, stats=stats, fav_asins=fav_asins, marketplace=marketplace, RainforestCollector=RainforestCollector)


@app.route("/detail/<asin>")
def detail(asin):
    p = get_product_by_asin(asin)
    if not p:
        return "产品未找到，请先扫描", 404
    trend_data = get_price_history(asin)
    return render_template_string(DETAIL_HTML, p=p, trend_data=trend_data)


@app.route("/compare", methods=["GET", "POST"])
def compare():
    if request.method == "POST":
        asins = request.form.getlist("asins")
    else:
        asins = request.args.getlist("asins")
    products = get_products_by_asins(asins)
    return render_template_string(COMPARE_HTML, products=products)


@app.route("/api/scan")
def api_scan():
    config = load_config()
    category = request.args.get("category", "Home & Kitchen")
    pages = int(request.args.get("pages", 2))
    marketplace = request.args.get("marketplace", config.get("rainforest", {}).get("marketplace", "us"))
    list_type = request.args.get("list_type", "bestsellers")
    try:
        datasource = request.args.get("datasource", "rainforest")
        if datasource == "playwright":
            if list_type == "new_releases":
                from src.collectors.playwright_scraper import sync_get_new_releases
                products = sync_get_new_releases(marketplace, category, pages)
            elif list_type == "movers_shakers":
                from src.collectors.playwright_scraper import sync_get_movers_shakers
                products = sync_get_movers_shakers(marketplace, category, pages)
            else:
                from src.collectors.playwright_scraper import sync_get_best_sellers
                products = sync_get_best_sellers(marketplace, category, pages)
        else:
            rf = config.get("rainforest", {})
            try:
                collector = RainforestCollector(
                    api_key=rf.get("api_key", ""), marketplace=marketplace
                )
                if list_type == "new_releases":
                    products = collector.get_new_releases(category, pages) if hasattr(collector, 'get_new_releases') else []
                elif list_type == "movers_shakers":
                    products = collector.get_movers_shakers(category, pages) if hasattr(collector, 'get_movers_shakers') else []
                else:
                    products = collector.get_best_sellers(category, pages)
            except Exception as e:
                print(f"Rainforest 失败，自动降级到 Playwright: {e}")
                if list_type == "new_releases":
                    from src.collectors.playwright_scraper import sync_get_new_releases
                    products = sync_get_new_releases(marketplace, category, pages)
                elif list_type == "movers_shakers":
                    from src.collectors.playwright_scraper import sync_get_movers_shakers
                    products = sync_get_movers_shakers(marketplace, category, pages)
                else:
                    from src.collectors.playwright_scraper import sync_get_best_sellers
                    products = sync_get_best_sellers(marketplace, category, pages)
        if not products:
            return jsonify({"ok": False, "error": "未获取到产品"})
        for p in products:
            p.marketplace = marketplace
            if not p.data_source:
                p.data_source = "playwright" if datasource == "playwright" else "rainforest"
        _run_pipeline(products, config, list_type, category, pages)
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        products_data = []
        for p in products:
            d = p.to_dict()
            d["amazon_domain"] = RainforestCollector.MARKETPLACE_DOMAINS.get(marketplace, "amazon.com")
            d["image_url"] = p.get_image_url
            products_data.append(d)
        return jsonify({"ok": True, "count": len(products_data), "products": products_data, "scan_time": scan_time, "source": "playwright" if datasource == "playwright" else "rainforest"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/search")
def api_search():
    config = load_config()
    keyword = request.args.get("keyword", "")
    pages = int(request.args.get("pages", 1))
    marketplace = request.args.get("marketplace", config.get("rainforest", {}).get("marketplace", "us"))
    if not keyword:
        return jsonify({"ok": False, "error": "请输入关键词"})
    try:
        datasource = request.args.get("datasource", "rainforest")
        if datasource == "playwright":
            from src.collectors.playwright_scraper import sync_search
            products = sync_search(marketplace, keyword, pages)
        else:
            rf = config.get("rainforest", {})
            try:
                collector = RainforestCollector(
                    api_key=rf.get("api_key", ""), marketplace=marketplace
                )
                products = collector.search_products(keyword, pages)
            except Exception as e:
                print(f"Rainforest 失败，自动降级到 Playwright: {e}")
                from src.collectors.playwright_scraper import sync_search
                products = sync_search(marketplace, keyword, pages)
        if not products:
            return jsonify({"ok": False, "error": "未搜索到产品"})
        for p in products:
            p.marketplace = marketplace
            if not p.data_source:
                p.data_source = "playwright" if datasource == "playwright" else "rainforest"
        _run_pipeline(products, config, "search", keyword, pages)
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        products_data = []
        for p in products:
            d = p.to_dict()
            d["amazon_domain"] = RainforestCollector.MARKETPLACE_DOMAINS.get(marketplace, "amazon.com")
            d["image_url"] = p.get_image_url
            products_data.append(d)
        return jsonify({"ok": True, "count": len(products_data), "products": products_data, "scan_time": scan_time, "source": "playwright" if datasource == "playwright" else "rainforest"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/categories")
def api_categories():
    config = load_config()
    marketplace = request.args.get("marketplace", config.get("rainforest", {}).get("marketplace", "us"))
    datasource = request.args.get("datasource", "rainforest")
    if datasource == "playwright":
        try:
            from src.collectors.playwright_scraper import sync_get_categories
            cats = sync_get_categories(marketplace)
            return jsonify({"ok": True, "categories": cats})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e), "categories": []})
    rf = config.get("rainforest", {})
    collector = RainforestCollector(
        api_key=rf.get("api_key", ""), marketplace=marketplace
    )
    try:
        categories = collector.get_categories()
        return jsonify({"ok": True, "categories": categories})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "categories": []})


@app.route("/api/favorite/add", methods=["POST"])
def api_add_favorite():
    data = request.get_json() or request.form
    asin = data.get("asin")
    if not asin:
        return jsonify({"ok": False, "error": "缺少 asin"})
    group = data.get("group_name", "默认")
    notes = data.get("notes", "")
    ok = add_favorite(asin, group, notes)
    return jsonify({"ok": ok})


@app.route("/api/favorite/<asin>", methods=["DELETE"])
def api_remove_favorite(asin):
    ok = remove_favorite(asin)
    return jsonify({"ok": ok})


@app.route("/api/favorites")
def api_get_favorites():
    group = request.args.get("group")
    favs = get_favorites(group)
    # 获取对应产品信息
    asins = [f['asin'] for f in favs]
    products_list = get_products_by_asins(asins)
    products_map = {p['asin']: p for p in products_list}
    return jsonify({"ok": True, "favorites": favs, "products": products_map})


@app.route("/api/trend/<asin>")
def api_trend(asin):
    history = get_price_history(asin)
    return jsonify({"ok": True, "history": history})


@app.route("/api/alerts", methods=["GET", "POST"])
def api_alerts():
    if request.method == "POST":
        data = request.get_json() or request.form
        asin = data.get("asin", "").strip()
        alert_type = data.get("alert_type", "")
        if not asin or not alert_type:
            return jsonify({"ok": False, "error": "缺少 asin 或 alert_type"})
        threshold_pct = float(data.get("threshold_pct", 10))
        target_price = data.get("target_price")
        if target_price is not None:
            target_price = float(target_price)
        result = create_price_alert(asin, alert_type, target_price, threshold_pct)
        if "error" in result:
            return jsonify({"ok": False, "error": result["error"]})
        return jsonify({"ok": True, "alert": result})
    else:
        alerts = get_price_alerts()
        return jsonify({"ok": True, "alerts": alerts})


@app.route("/api/alerts/check")
def api_alerts_check():
    triggered = check_price_alerts()
    return jsonify({"ok": True, "triggered": triggered})


@app.route("/api/alerts/<int:alert_id>", methods=["DELETE"])
def api_delete_alert(alert_id):
    ok = delete_price_alert(alert_id)
    return jsonify({"ok": ok})


@app.route("/api/bsr-alerts", methods=["GET", "POST"])
def api_bsr_alerts():
    if request.method == "POST":
        data = request.get_json() or request.form
        asin = data.get("asin", "").strip()
        alert_type = data.get("alert_type", "")
        if not asin or not alert_type:
            return jsonify({"ok": False, "error": "缺少 asin 或 alert_type"})
        threshold_pct = float(data.get("threshold_pct", 20))
        result = create_bsr_alert(asin, alert_type, threshold_pct)
        if "error" in result:
            return jsonify({"ok": False, "error": result["error"]})
        return jsonify({"ok": True, "alert": result})
    else:
        alerts = get_bsr_alerts()
        return jsonify({"ok": True, "alerts": alerts})


@app.route("/api/bsr-alerts/check")
def api_bsr_alerts_check():
    triggered = check_bsr_alerts()
    return jsonify({"ok": True, "triggered": triggered})


@app.route("/api/bsr-alerts/<int:alert_id>", methods=["DELETE"])
def api_delete_bsr_alert(alert_id):
    ok = delete_bsr_alert(alert_id)
    return jsonify({"ok": ok})


@app.route("/api/report/category", methods=["POST"])
def api_category_report():
    data = request.get_json() or request.form
    category = data.get("category", "")
    marketplace = data.get("marketplace", "")
    if not category:
        return jsonify({"ok": False, "error": "请提供品类名称"})

    config = load_config()
    # 获取该品类的产品数据
    conn = __import__('scripts.init_db', fromlist=['get_connection']).get_connection()
    cursor = conn.cursor()
    if marketplace:
        cursor.execute(
            "SELECT * FROM products WHERE category LIKE ? AND marketplace = ? ORDER BY total_score DESC LIMIT 20",
            (f"%{category}%", marketplace),
        )
    else:
        cursor.execute(
            "SELECT * FROM products WHERE category LIKE ? ORDER BY total_score DESC LIMIT 20",
            (f"%{category}%",),
        )
    rows = cursor.fetchall()
    conn.close()
    products = [dict(r) for r in rows]

    if not products:
        # 如果没有精确匹配，用所有产品
        products = get_top_products(20)

    # 构建上下文
    context = f"""## 品类分析数据

品类：{category}
产品数量：{len(products)}

### 产品概览
"""
    for i, p in enumerate(products[:15], 1):
        context += f"""
{i}. {p.get('title', 'N/A')[:60]}
   - ASIN: {p.get('asin')} | 售价: ${p.get('price', 0):.2f} | 评分: {p.get('rating', 0)}/5.0
   - BSR: #{p.get('bsr', 'N/A')} | 月销量: {p.get('monthly_sales_est', 'N/A')} | 卖家数: {p.get('seller_count', 'N/A')}
   - 毛利率: {p.get('profit_margin', 0):.1f}% | 总分: {p.get('total_score', 0)}
"""

    # 使用 AI 生成报告
    analyzer = AIAnalyzer(config)
    prompt = f"""请基于以下亚马逊{category}品类的产品数据，生成一份完整的品类分析报告。报告要求：

{context}

请按以下结构输出（中文）：

## 📊 {category} 品类报告

### 一、市场概况
- 市场规模和趋势
- 平均售价和价格区间
- 消费者需求特征

### 二、竞争格局
- 头部品牌/卖家分析
- 竞争激烈程度评估
- 进入壁垒分析

### 三、机会点
- 细分市场机会
- 差异化方向
- 价格策略建议

### 四、推荐策略
- 新卖家切入建议
- 产品开发方向
- 风险提示"""

    try:
        from openai import OpenAI
        ai_config = config.get("ai", {})
        client = OpenAI(
            api_key=ai_config.get("api_key", ""),
            base_url=ai_config.get("base_url", "https://api.openai.com/v1"),
        )
        resp = client.chat.completions.create(
            model=ai_config.get("model", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7,
        )
        report = resp.choices[0].message.content
        return jsonify({"ok": True, "report": report})
    except Exception as e:
        # 回退：生成简易报告
        avg_price = sum(p.get('price', 0) for p in products) / len(products) if products else 0
        avg_score = sum(p.get('total_score', 0) for p in products) / len(products) if products else 0
        report = f"""## 📊 {category} 品类报告

### 一、市场概况
- 采集产品数：{len(products)}
- 平均售价：${avg_price:.2f}
- 平均总分：{avg_score:.1f}

### 二、竞争格局
- {'竞争较激烈' if avg_score < 60 else '竞争适中' if avg_score < 75 else '竞争较小'}

### 三、机会点
- {'建议关注细分市场' if len(products) > 5 else '数据较少，建议扩大采集范围'}

### 四、推荐策略
- 优先关注总分 ≥ 70 的产品
- 关注毛利率 ≥ 30% 的品类

---
⚠️ AI 服务未配置或调用失败（{str(e)}），以上为简易分析。请配置 config.yaml 中的 ai 设置以获取完整报告。"""
        return jsonify({"ok": True, "report": report})


@app.route("/export")
def export_page():
    from src.main import _generate_markdown_report
    products = get_top_products(30)
    if not products:
        return "暂无数据"
    report = _generate_markdown_report(products)
    return f"<pre style='padding:24px;font-size:14px;line-height:1.6;white-space:pre-wrap;color:#1e293b;background:#fff'>{report}</pre>"


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


@app.route("/api/import/upload", methods=["POST"])
def api_import_upload():
    """文件上传导入（preview=true 时只预览）"""
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "请选择文件"})
    f = request.files['file']
    if not f.filename:
        return jsonify({"ok": False, "error": "文件名为空"})
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ('.csv', '.xlsx'):
        return jsonify({"ok": False, "error": "仅支持 .csv 和 .xlsx 格式"})

    try:
        if ext == '.csv':
            import pandas as pd
            import io
            df = pd.read_csv(io.BytesIO(f.read()), encoding='utf-8-sig')
        else:
            import pandas as pd
            import io
            df = pd.read_excel(io.BytesIO(f.read()), engine='openpyxl')

        df = df.fillna('')
        columns = list(df.columns)
        rows = [dict(zip(columns, [str(v) if v != '' else '' for v in row])) for row in df.values.tolist()]

        if request.args.get('preview') == 'true':
            return jsonify({"ok": True, "columns": columns, "rows": rows, "total": len(rows)})

        # Direct import without preview
        result = import_products_from_list(rows, "merge")
        return jsonify({"ok": True, "result": result})
    except ImportError:
        return jsonify({"ok": False, "error": "缺少 pandas 或 openpyxl 库"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/import/confirm", methods=["POST"])
def api_import_confirm():
    """确认导入"""
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "无效请求数据"})
    columns_mapping = data.get('columns_mapping', {})
    merge_strategy = data.get('merge_strategy', 'merge')
    raw_data = data.get('data', [])

    if not raw_data:
        return jsonify({"ok": False, "error": "无数据"})

    # Convert data according to mapping
    products = []
    for row in raw_data:
        mapped = {}
        for csv_col, value in row.items():
            field = columns_mapping.get(csv_col)
            if field:
                # Type conversion
                if field in ('price', 'rating', 'gross_profit', 'profit_margin', 'fba_fee', 'referral_fee', 'storage_fee', 'estimated_cost', 'monthly_revenue_est', 'click_share', 'conversion_rate'):
                    try: mapped[field] = float(str(value).replace('%', '').replace('$', '').replace(',', '').strip() or 0)
                    except: mapped[field] = 0
                elif field in ('reviews_count', 'bsr', 'monthly_sales_est', 'seller_count', 'search_volume'):
                    try: mapped[field] = int(float(str(value).replace(',', '').replace('#', '').strip() or 0))
                    except: mapped[field] = 0
                elif field in ('weight_grams', 'listing_quality_score', 'demand_score', 'competition_score', 'profit_score', 'opportunity_score', 'total_score'):
                    try: mapped[field] = float(str(value).strip() or 0)
                    except: mapped[field] = 0
                else:
                    mapped[field] = str(value).strip()
        if mapped.get('asin'):
            mapped['data_source'] = 'opportunity_explorer'
            products.append(mapped)

    if not products:
        return jsonify({"ok": False, "error": "无有效数据（需要 ASIN 列）"})

    result = import_products_from_list(products, merge_strategy)
    return jsonify({"ok": True, "result": result})


@app.route("/api/import/paste", methods=["POST"])
def api_import_paste():
    """粘贴数据导入"""
    data = request.get_json()
    if not data or not data.get('raw_text'):
        return jsonify({"ok": False, "error": "请提供数据"})

    raw = data['raw_text'].strip()
    lines = raw.split('\n')
    if len(lines) < 2:
        return jsonify({"ok": False, "error": "数据不足（至少需要表头和一行数据）"})

    # Auto-detect delimiter
    first_line = lines[0]
    tab_count = first_line.count('\t')
    comma_count = first_line.count(',')
    semi_count = first_line.count(';')
    if tab_count >= comma_count and tab_count >= semi_count:
        delimiter = '\t'
    elif semi_count > comma_count:
        delimiter = ';'
    else:
        delimiter = ','

    try:
        import csv
        import io
        reader = csv.DictReader(io.StringIO(raw), delimiter=delimiter)
        columns = reader.fieldnames or []
        rows = []
        for row in reader:
            rows.append({k: (v or '').strip() for k, v in row.items()})

        return jsonify({"ok": True, "columns": columns, "rows": rows, "total": len(rows)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ─── 启动 ───────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n🚀 亚马逊选品系统已启动")
    print("   打开浏览器访问：http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5002)
