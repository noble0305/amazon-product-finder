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
                    image_url
                ) VALUES (
                    :asin, :title, :brand, :category, :price, :rating, :reviews_count,
                    :bsr, :monthly_sales_est, :monthly_revenue_est, :seller_count,
                    :buy_box_seller, :weight_grams, :dimensions, :listing_quality_score,
                    :date_first_available, :demand_score, :competition_score, :profit_score,
                    :opportunity_score, :total_score, :ai_analysis, :referral_fee, :fba_fee,
                    :storage_fee, :estimated_cost, :gross_profit, :profit_margin, :is_on_promotion,
                    :image_url
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


def get_top_products(limit: int = 20) -> list:
    """获取评分最高的产品"""
    conn = get_connection()
    cursor = conn.cursor()
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
