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
            <option value="rainforest">🌊 Rainforest API</option>
            <option value="playwright">🕷️ Playwright 直爬</option>
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
            <option value="rainforest">🌊 Rainforest API</option>
            <option value="playwright">🕷️ Playwright 直爬</option>
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
          <td><a class="detail-link" href="/detail/{{ p.asin }}">详情 →</a></td>
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
            <option value="rainforest">🌊 Rainforest API</option>
            <option value="playwright">🕷️ Playwright 直爬</option>
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
    if (data.ok) window.location.reload();
    else { alert('扫描失败: ' + data.error); hideLoading(); }
  } catch(e) { alert('请求失败: ' + e.message); hideLoading(); }
}

async function doSearch() {
  const kw = document.getElementById('keyword').value.trim();
  if (!kw) { alert('请输入关键词'); return; }
  const mp = document.getElementById('marketplace').value;
  const ds = document.getElementById('datasource-search').value;
  showLoading('正在搜索 "' + kw + '" (' + (ds === 'playwright' ? 'Playwright' : 'Rainforest') + ') ...');
  try {
    const resp = await fetch('/api/search?keyword=' + encodeURIComponent(kw) + '&pages=1&marketplace=' + mp + '&datasource=' + ds);
    const data = await resp.json();
    if (data.ok) window.location.reload();
    else { alert('搜索失败: ' + data.error); hideLoading(); }
  } catch(e) { alert('请求失败: ' + e.message); hideLoading(); }
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
    return render_template_string(INDEX_HTML, products=products, stats=stats, fav_asins=fav_asins, marketplace=marketplace)


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
        _run_pipeline(products, config, list_type, category, pages)
        return jsonify({"ok": True, "count": len(products)})
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
        _run_pipeline(products, config, "search", keyword, pages)
        return jsonify({"ok": True, "count": len(products)})
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


# ─── 启动 ───────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n🚀 亚马逊选品系统已启动")
    print("   打开浏览器访问：http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5002)
