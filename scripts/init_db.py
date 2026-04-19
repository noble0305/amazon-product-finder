"""数据库初始化脚本

创建 SQLite 数据库和表结构，用于存储产品数据。
"""

import sqlite3
import os


# 数据库表结构
CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT UNIQUE NOT NULL,
    title TEXT,
    brand TEXT,
    category TEXT,
    price REAL,
    rating REAL,
    reviews_count INTEGER,
    bsr INTEGER,
    monthly_sales_est INTEGER,
    monthly_revenue_est REAL,
    seller_count INTEGER,
    buy_box_seller TEXT,
    weight_grams REAL,
    dimensions TEXT,
    listing_quality_score REAL,
    date_first_available TEXT,
    demand_score REAL DEFAULT 0,
    competition_score REAL DEFAULT 0,
    profit_score REAL DEFAULT 0,
    opportunity_score REAL DEFAULT 0,
    total_score REAL DEFAULT 0,
    ai_analysis TEXT,
    referral_fee REAL DEFAULT 0,
    fba_fee REAL DEFAULT 0,
    storage_fee REAL DEFAULT 0,
    estimated_cost REAL DEFAULT 0,
    gross_profit REAL DEFAULT 0,
    profit_margin REAL DEFAULT 0,
    is_on_promotion INTEGER DEFAULT 0,
    image_url TEXT DEFAULT '',
    marketplace TEXT DEFAULT 'us',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SCANS_TABLE = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_type TEXT NOT NULL,
    query TEXT,
    pages INTEGER DEFAULT 1,
    products_found INTEGER DEFAULT 0,
    products_filtered INTEGER DEFAULT 0,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_COMPARISONS_TABLE = """
CREATE TABLE IF NOT EXISTS comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    asins TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_FAVORITES_TABLE = """
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT UNIQUE NOT NULL,
    group_name TEXT DEFAULT '默认',
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PRICE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT NOT NULL,
    price REAL,
    bsr INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PRICE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS price_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    target_price REAL,
    threshold_pct REAL DEFAULT 10,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    UNIQUE(asin, alert_type, target_price)
);
"""

CREATE_BSR_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS bsr_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    threshold_pct REAL DEFAULT 20,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    UNIQUE(asin, alert_type)
);
"""


def get_db_path() -> str:
    """获取数据库路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(base_dir, "db")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "products.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库，创建所有表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(CREATE_PRODUCTS_TABLE)
    cursor.execute(CREATE_SCANS_TABLE)
    cursor.execute(CREATE_COMPARISONS_TABLE)
    cursor.execute(CREATE_FAVORITES_TABLE)
    cursor.execute(CREATE_PRICE_HISTORY_TABLE)
    cursor.execute(CREATE_PRICE_ALERTS_TABLE)
    cursor.execute(CREATE_BSR_ALERTS_TABLE)

    # 迁移：确保 marketplace 列存在
    try:
        cursor.execute("SELECT marketplace FROM products LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE products ADD COLUMN marketplace TEXT DEFAULT 'us'")
        print("  ✅ 已添加 marketplace 列")

    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {get_db_path()}")


def save_products(products: list) -> int:
    """保存产品到数据库（存在则更新）"""
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0

    for p in products:
        data = p.to_dict()
        try:
            cursor.execute(
                """
                INSERT INTO products (
                    asin, title, brand, category, price, rating, reviews_count,
                    bsr, monthly_sales_est, monthly_revenue_est, seller_count,
                    buy_box_seller, weight_grams, dimensions, listing_quality_score,
                    date_first_available, demand_score, competition_score, profit_score,
                    opportunity_score, total_score, ai_analysis, referral_fee, fba_fee,
                    storage_fee, estimated_cost, gross_profit, profit_margin, is_on_promotion,
                    image_url, marketplace
                ) VALUES (
                    :asin, :title, :brand, :category, :price, :rating, :reviews_count,
                    :bsr, :monthly_sales_est, :monthly_revenue_est, :seller_count,
                    :buy_box_seller, :weight_grams, :dimensions, :listing_quality_score,
                    :date_first_available, :demand_score, :competition_score, :profit_score,
                    :opportunity_score, :total_score, :ai_analysis, :referral_fee, :fba_fee,
                    :storage_fee, :estimated_cost, :gross_profit, :profit_margin, :is_on_promotion,
                    :image_url, :marketplace
                )
                ON CONFLICT(asin) DO UPDATE SET
                    title=excluded.title, brand=excluded.brand, price=excluded.price,
                    rating=excluded.rating, reviews_count=excluded.reviews_count,
                    bsr=excluded.bsr, monthly_sales_est=excluded.monthly_sales_est,
                    monthly_revenue_est=excluded.monthly_revenue_est,
                    seller_count=excluded.seller_count, total_score=excluded.total_score,
                    demand_score=excluded.demand_score, competition_score=excluded.competition_score,
                    profit_score=excluded.profit_score, opportunity_score=excluded.opportunity_score,
                    ai_analysis=excluded.ai_analysis, gross_profit=excluded.gross_profit,
                    profit_margin=excluded.profit_margin, image_url=excluded.image_url,
                    updated_at=CURRENT_TIMESTAMP
                """,
                data,
            )
            saved += 1
        except sqlite3.Error as e:
            print(f"  ⚠️ 保存产品 {p.asin} 失败: {e}")

    conn.commit()
    conn.close()
    return saved


def save_scan(scan_type: str, query: str, pages: int,
              found: int, filtered: int) -> None:
    """保存扫描记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scans (scan_type, query, pages, products_found, products_filtered) VALUES (?, ?, ?, ?, ?)",
        (scan_type, query, pages, found, filtered),
    )
    conn.commit()
    conn.close()


def save_price_snapshot(products: list) -> None:
    """保存价格快照到 price_history"""
    conn = get_connection()
    cursor = conn.cursor()
    for p in products:
        data = p.to_dict() if hasattr(p, 'to_dict') else p
        try:
            cursor.execute(
                "INSERT INTO price_history (asin, price, bsr) VALUES (?, ?, ?)",
                (data.get('asin'), data.get('price'), data.get('bsr')),
            )
        except sqlite3.Error:
            pass
    conn.commit()
    conn.close()


def get_top_products(limit: int = 20, marketplace: str = None) -> list:
    """获取评分最高的产品"""
    conn = get_connection()
    cursor = conn.cursor()
    if marketplace:
        cursor.execute("SELECT * FROM products WHERE marketplace = ? ORDER BY total_score DESC LIMIT ?", (marketplace, limit))
    else:
        cursor.execute("SELECT * FROM products ORDER BY total_score DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_product_by_asin(asin: str) -> dict:
    """根据 ASIN 获取产品"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE asin = ?", (asin,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_products_by_asins(asins: list) -> list:
    """根据多个 ASIN 获取产品"""
    if not asins:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(asins))
    cursor.execute(f"SELECT * FROM products WHERE asin IN ({placeholders})", asins)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_favorites(group: str = None) -> list:
    """获取收藏列表"""
    conn = get_connection()
    cursor = conn.cursor()
    if group and group != '全部':
        cursor.execute("SELECT * FROM favorites WHERE group_name = ? ORDER BY created_at DESC", (group,))
    else:
        cursor.execute("SELECT * FROM favorites ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_favorite(asin: str, group_name: str = '默认', notes: str = '') -> bool:
    """添加收藏"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO favorites (asin, group_name, notes) VALUES (?, ?, ?)",
            (asin, group_name, notes),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def remove_favorite(asin: str) -> bool:
    """移除收藏"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE asin = ?", (asin,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def is_favorite(asin: str) -> bool:
    """检查是否已收藏"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM favorites WHERE asin = ?", (asin,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_price_history(asin: str) -> list:
    """获取价格历史"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price, bsr, recorded_at FROM price_history WHERE asin = ? ORDER BY recorded_at ASC",
        (asin,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─── 价格预警 CRUD ────────────────────────────────────────────

def create_price_alert(asin: str, alert_type: str, target_price: float = None, threshold_pct: float = 10) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO price_alerts (asin, alert_type, target_price, threshold_pct) VALUES (?, ?, ?, ?)",
            (asin, alert_type, target_price, threshold_pct),
        )
        conn.commit()
        alert_id = cursor.lastrowid
        cursor.execute("SELECT * FROM price_alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}
    except sqlite3.IntegrityError:
        return {"error": "该预警规则已存在"}
    finally:
        conn.close()


def get_price_alerts(active_only: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM price_alerts WHERE is_active = 1 ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM price_alerts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_price_alert(alert_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM price_alerts WHERE id = ?", (alert_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def check_price_alerts() -> list:
    """检查所有活跃的价格预警，返回触发的预警列表"""
    alerts = get_price_alerts(active_only=True)
    triggered = []
    conn = get_connection()
    cursor = conn.cursor()

    for alert in alerts:
        asin = alert['asin']
        # 获取最近2条价格记录
        cursor.execute(
            "SELECT price, recorded_at FROM price_history WHERE asin = ? ORDER BY recorded_at DESC LIMIT 2",
            (asin,)
        )
        rows = cursor.fetchall()
        if len(rows) < 2:
            continue

        current_price = rows[0]['price']
        prev_price = rows[1]['price']

        if prev_price and prev_price > 0:
            change_pct = (current_price - prev_price) / prev_price * 100
        else:
            continue

        fired = False
        if alert['alert_type'] == 'price_drop' and change_pct < -alert['threshold_pct']:
            fired = True
        elif alert['alert_type'] == 'price_surge' and change_pct > alert['threshold_pct']:
            fired = True
        elif alert['alert_type'] == 'below_target' and alert['target_price'] and current_price < alert['target_price']:
            fired = True

        if fired:
            cursor.execute(
                "UPDATE price_alerts SET triggered_at = CURRENT_TIMESTAMP WHERE id = ?",
                (alert['id'],)
            )
            triggered.append({
                **alert,
                'current_price': current_price,
                'prev_price': prev_price,
                'change_pct': round(change_pct, 2),
            })

    conn.commit()
    conn.close()
    return triggered


# ─── BSR 预警 CRUD ──────────────────────────────────────────────

def create_bsr_alert(asin: str, alert_type: str, threshold_pct: float = 20) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO bsr_alerts (asin, alert_type, threshold_pct) VALUES (?, ?, ?)",
            (asin, alert_type, threshold_pct),
        )
        conn.commit()
        alert_id = cursor.lastrowid
        cursor.execute("SELECT * FROM bsr_alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}
    except sqlite3.IntegrityError:
        return {"error": "该 BSR 预警规则已存在"}
    finally:
        conn.close()


def get_bsr_alerts(active_only: bool = False) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if active_only:
        cursor.execute("SELECT * FROM bsr_alerts WHERE is_active = 1 ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM bsr_alerts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_bsr_alert(alert_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bsr_alerts WHERE id = ?", (alert_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def check_bsr_alerts() -> list:
    """检查所有活跃的 BSR 预警，返回触发的预警列表"""
    alerts = get_bsr_alerts(active_only=True)
    triggered = []
    conn = get_connection()
    cursor = conn.cursor()

    for alert in alerts:
        asin = alert['asin']
        cursor.execute(
            "SELECT bsr, recorded_at FROM price_history WHERE asin = ? ORDER BY recorded_at DESC LIMIT 2",
            (asin,)
        )
        rows = cursor.fetchall()
        if len(rows) < 2:
            continue

        current_bsr = rows[0]['bsr']
        prev_bsr = rows[1]['bsr']

        if prev_bsr and prev_bsr > 0:
            # BSR 下降 = 排名上升（好），BSR 上升 = 排名下降（差）
            change_pct = (current_bsr - prev_bsr) / prev_bsr * 100
        else:
            continue

        fired = False
        # bsr_drop = 排名下降（BSR 数值上升）
        if alert['alert_type'] == 'bsr_drop' and change_pct > alert['threshold_pct']:
            fired = True
        # bsr_surge = 排名上升（BSR 数值下降）
        elif alert['alert_type'] == 'bsr_surge' and change_pct < -alert['threshold_pct']:
            fired = True

        if fired:
            cursor.execute(
                "UPDATE bsr_alerts SET triggered_at = CURRENT_TIMESTAMP WHERE id = ?",
                (alert['id'],)
            )
            triggered.append({
                **alert,
                'current_bsr': current_bsr,
                'prev_bsr': prev_bsr,
                'change_pct': round(change_pct, 2),
            })

    conn.commit()
    conn.close()
    return triggered


def get_favorite_groups() -> list:
    """获取所有收藏分组"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT group_name FROM favorites ORDER BY group_name")
    rows = cursor.fetchall()
    conn.close()
    return [row['group_name'] for row in rows]


if __name__ == "__main__":
    init_db()
