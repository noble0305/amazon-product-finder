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


def get_db_path() -> str:
    """获取数据库路径"""
    # 数据库文件在项目目录的 db/ 下
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

    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {get_db_path()}")


def save_products(products: list) -> int:
    """保存产品到数据库（存在则更新）

    Args:
        products: 产品列表

    Returns:
        保存的产品数量
    """
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
                    storage_fee, estimated_cost, gross_profit, profit_margin, is_on_promotion
                ) VALUES (
                    :asin, :title, :brand, :category, :price, :rating, :reviews_count,
                    :bsr, :monthly_sales_est, :monthly_revenue_est, :seller_count,
                    :buy_box_seller, :weight_grams, :dimensions, :listing_quality_score,
                    :date_first_available, :demand_score, :competition_score, :profit_score,
                    :opportunity_score, :total_score, :ai_analysis, :referral_fee, :fba_fee,
                    :storage_fee, :estimated_cost, :gross_profit, :profit_margin, :is_on_promotion
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
                    profit_margin=excluded.profit_margin, updated_at=CURRENT_TIMESTAMP
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
        """
        INSERT INTO scans (scan_type, query, pages, products_found, products_filtered)
        VALUES (?, ?, ?, ?, ?)
        """,
        (scan_type, query, pages, found, filtered),
    )
    conn.commit()
    conn.close()


def get_top_products(limit: int = 20) -> list:
    """获取评分最高的产品

    Args:
        limit: 返回数量

    Returns:
        产品列表（字典格式）
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM products
        ORDER BY total_score DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_product_by_asin(asin: str) -> dict:
    """根据 ASIN 获取产品

    Args:
        asin: 产品 ASIN

    Returns:
        产品字典（未找到返回空字典）
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE asin = ?", (asin,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


if __name__ == "__main__":
    init_db()
