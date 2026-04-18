"""Rainforest API 数据采集器

支持从 Rainforest API 采集亚马逊 Best Sellers 和搜索结果。
无 API key 时自动切换到 demo 模式（模拟数据）。
"""

import random
import time
from typing import List, Optional

import requests

from ..models.product import Product


# Demo 模式用的模拟产品数据
DEMO_PRODUCTS = [
    {
        "asin": "B09XYZ001",
        "title": "Stainless Steel Garlic Press - Premium Kitchen Gadget with Ergonomic Handle, Rust-Proof Mincer for Garlic and Ginger",
        "brand": "KitchenPro",
        "category": "Home & Kitchen",
        "price": 24.99,
        "rating": 4.3,
        "reviews_count": 2847,
        "bsr": 1523,
        "monthly_sales_est": 1200,
        "monthly_revenue_est": 29988.0,
        "seller_count": 3,
        "buy_box_seller": "Amazon.com",
        "weight_grams": 340,
        "dimensions": (20.3, 7.6, 5.1),
        "listing_quality_score": 82,
        "date_first_available": "2023-03-15",
    },
    {
        "asin": "B09XYZ002",
        "title": "Portable Blender for Shakes and Smoothies - USB Rechargeable Personal Blender with 6 Blades, 16oz Travel Cup",
        "brand": "BlendGo",
        "category": "Home & Kitchen",
        "price": 29.97,
        "rating": 4.1,
        "reviews_count": 892,
        "bsr": 3421,
        "monthly_sales_est": 850,
        "monthly_revenue_est": 25474.5,
        "seller_count": 5,
        "buy_box_seller": "BlendGo Official",
        "weight_grams": 520,
        "dimensions": (22.9, 10.2, 10.2),
        "listing_quality_score": 75,
        "date_first_available": "2023-07-20",
    },
    {
        "asin": "B09XYZ003",
        "title": "Electric Milk Frother Handheld - USB Rechargeable Coffee Foam Maker with Stand, Stainless Steel Whisk",
        "brand": "FoamMaster",
        "category": "Home & Kitchen",
        "price": 17.99,
        "rating": 4.5,
        "reviews_count": 5623,
        "bsr": 892,
        "monthly_sales_est": 2100,
        "monthly_revenue_est": 37779.0,
        "seller_count": 2,
        "buy_box_seller": "Amazon.com",
        "weight_grams": 180,
        "dimensions": (25.4, 5.1, 5.1),
        "listing_quality_score": 88,
        "date_first_available": "2022-11-10",
    },
    {
        "asin": "B09XYZ004",
        "title": "Silicone Kitchen Utensils Set - 12-Piece Heat-Resistant Cooking Tools with Wooden Handle, Non-Stick Cookware",
        "brand": "CookEssential",
        "category": "Home & Kitchen",
        "price": 32.99,
        "rating": 4.2,
        "reviews_count": 1256,
        "bsr": 2876,
        "monthly_sales_est": 680,
        "monthly_revenue_est": 22433.2,
        "seller_count": 4,
        "buy_box_seller": "CookEssential",
        "weight_grams": 890,
        "dimensions": (38.1, 15.2, 10.2),
        "listing_quality_score": 70,
        "date_first_available": "2023-05-01",
    },
    {
        "asin": "B09XYZ005",
        "title": "Electric Wine Opener Set - Automatic Corkscrew with Foil Cutter, Aerators and Vacuum Stopper",
        "brand": "WineJoy",
        "category": "Home & Kitchen",
        "price": 22.49,
        "rating": 4.4,
        "reviews_count": 3421,
        "bsr": 1934,
        "monthly_sales_est": 950,
        "monthly_revenue_est": 21365.5,
        "seller_count": 3,
        "buy_box_seller": "Amazon.com",
        "weight_grams": 450,
        "dimensions": (25.4, 10.2, 10.2),
        "listing_quality_score": 85,
        "date_first_available": "2022-08-22",
    },
    {
        "asin": "B09XYZ006",
        "title": "Mini Desk Organizer - Bamboo Desktop Storage Shelf with Drawers for Office Supplies",
        "brand": "DeskHelper",
        "category": "Office Products",
        "price": 19.99,
        "rating": 4.0,
        "reviews_count": 387,
        "bsr": 8432,
        "monthly_sales_est": 420,
        "monthly_revenue_est": 8395.8,
        "seller_count": 2,
        "buy_box_seller": "DeskHelper Direct",
        "weight_grams": 680,
        "dimensions": (30.5, 20.3, 12.7),
        "listing_quality_score": 65,
        "date_first_available": "2024-01-15",
    },
    {
        "asin": "B09XYZ007",
        "title": "LED Desk Lamp with Wireless Charger - Dimmable Eye-Caring Reading Light with USB Charging Port",
        "brand": "LumiTech",
        "category": "Office Products",
        "price": 36.99,
        "rating": 4.3,
        "reviews_count": 1872,
        "bsr": 4231,
        "monthly_sales_est": 580,
        "monthly_revenue_est": 21454.2,
        "seller_count": 6,
        "buy_box_seller": "LumiTech Store",
        "weight_grams": 1200,
        "dimensions": (45.7, 20.3, 15.2),
        "listing_quality_score": 78,
        "date_first_available": "2023-02-28",
    },
    {
        "asin": "B09XYZ008",
        "title": "Resistance Bands Set - 5-Piece Exercise Loop Bands for Workout, Yoga, Physical Therapy",
        "brand": "FitBand Pro",
        "category": "Sports & Outdoors",
        "price": 15.99,
        "rating": 4.6,
        "reviews_count": 8934,
        "bsr": 623,
        "monthly_sales_est": 3200,
        "monthly_revenue_est": 51168.0,
        "seller_count": 2,
        "buy_box_seller": "Amazon.com",
        "weight_grams": 280,
        "dimensions": (25.4, 15.2, 5.1),
        "listing_quality_score": 92,
        "date_first_available": "2021-06-10",
    },
    {
        "asin": "B09XYZ009",
        "title": "Waterproof Phone Pouch - Universal Dry Bag for Swimming, Beach, Kayaking with Lanyard",
        "brand": "AquaSafe",
        "category": "Sports & Outdoors",
        "price": 12.99,
        "rating": 4.2,
        "reviews_count": 4521,
        "bsr": 2341,
        "monthly_sales_est": 1800,
        "monthly_revenue_est": 23382.0,
        "seller_count": 8,
        "buy_box_seller": "AquaSafe LLC",
        "weight_grams": 60,
        "dimensions": (22.9, 12.7, 1.3),
        "listing_quality_score": 72,
        "date_first_available": "2023-04-12",
    },
    {
        "asin": "B09XYZ010",
        "title": "Portable Neck Fan - USB Rechargeable Bladeless Personal Fan with 3 Speeds, Quiet Operation",
        "brand": "CoolBreeze",
        "category": "Home & Kitchen",
        "price": 26.99,
        "rating": 3.9,
        "reviews_count": 523,
        "bsr": 6789,
        "monthly_sales_est": 380,
        "monthly_revenue_est": 10256.2,
        "seller_count": 7,
        "buy_box_seller": "CoolBreeze Direct",
        "weight_grams": 320,
        "dimensions": (20.3, 15.2, 7.6),
        "listing_quality_score": 55,
        "date_first_available": "2024-02-05",
    },
    {
        "asin": "B09XYZ011",
        "title": "Bamboo Toothbrush Set of 8 - Eco-Friendly Biodegradable BPA-Free Soft Bristle Brushes",
        "brand": "EcoSmile",
        "category": "Beauty & Personal Care",
        "price": 14.99,
        "rating": 4.4,
        "reviews_count": 2341,
        "bsr": 1567,
        "monthly_sales_est": 1500,
        "monthly_revenue_est": 22485.0,
        "seller_count": 4,
        "buy_box_seller": "EcoSmile",
        "weight_grams": 150,
        "dimensions": (19.1, 5.1, 2.5),
        "listing_quality_score": 80,
        "date_first_available": "2022-05-18",
    },
    {
        "asin": "B09XYZ012",
        "title": "Pet Hair Remover - Reusable Lint Roller for Furniture, Clothes and Car Seats",
        "brand": "FurFree",
        "category": "Pet Supplies",
        "price": 18.99,
        "rating": 4.1,
        "reviews_count": 1567,
        "bsr": 3892,
        "monthly_sales_est": 720,
        "monthly_revenue_est": 13672.8,
        "seller_count": 3,
        "buy_box_seller": "FurFree Official",
        "weight_grams": 200,
        "dimensions": (17.8, 10.2, 5.1),
        "listing_quality_score": 73,
        "date_first_available": "2023-09-10",
    },
]


def _generate_demo_products(category: str, keyword: Optional[str],
                            pages: int) -> List[Product]:
    """生成模拟产品数据用于 demo 模式

    Args:
        category: 品类名称
        keyword: 搜索关键词
        pages: 页数

    Returns:
        模拟产品列表
    """
    products = []

    # 根据关键词或品类筛选基础数据
    base_products = DEMO_PRODUCTS.copy()
    if keyword:
        # 关键词搜索时，微调标题
        for p in base_products:
            if keyword.lower() not in p["title"].lower():
                continue
            products.append(Product(**p))

    if not products:
        # 没有精确匹配时，使用全部 demo 数据
        for p in base_products:
            products.append(Product(**p))

    # 根据页数扩充数据
    if pages > 1:
        for page in range(1, pages):
            for p in base_products:
                # 生成变体：微调价格和排名
                variant = p.copy()
                variant["asin"] = f"B09XY{page:02d}{variant['asin'][-3:]}"
                variant["price"] = round(
                    variant["price"] * random.uniform(0.85, 1.15), 2
                )
                variant["bsr"] = int(variant["bsr"] * random.uniform(0.8, 1.5))
                variant["reviews_count"] = int(
                    variant["reviews_count"] * random.uniform(0.5, 1.5)
                )
                variant["monthly_sales_est"] = int(
                    variant["monthly_sales_est"] * random.uniform(0.6, 1.4)
                )
                variant["monthly_revenue_est"] = round(
                    variant["price"] * variant["monthly_sales_est"], 2
                )
                products.append(Product(**variant))

    return products


class RainforestCollector:
    """Rainforest API 数据采集器

    支持两种模式：
    - 真实模式：需要有效的 Rainforest API key
    - Demo 模式：无 API key 时自动启用，使用模拟数据
    """

    BASE_URL = "https://api.rainforestapi.com/request"

    def __init__(self, api_key: str, marketplace: str = "us"):
        """初始化采集器

        Args:
            api_key: Rainforest API key，留空使用 demo 模式
            marketplace: 站点（默认 us）
        """
        self.api_key = api_key
        self.marketplace = marketplace
        self.is_demo = not api_key or api_key == "YOUR_API_KEY"

    # 常用品类节点 ID 映射
    CATEGORY_MAP = {
        "home & kitchen": "home-garden",
        "kitchen": "kitchen",
        "home": "home-garden",
        "beauty": "beauty",
        "sports": "sporting-goods",
        "sports & outdoors": "sporting-goods",
        "electronics": "electronics",
        "office": "office-products",
        "office products": "office-products",
        "pet supplies": "pet-supplies",
        "pets": "pet-supplies",
        "toys": "toys-and-games",
        "garden": "lawn-garden",
        "tools": "industrial",
        "clothing": "apparel",
        "baby": "baby-products",
        "health": "hpc",
        "books": "books",
        "automotive": "automotive",
    }

    def get_best_sellers(self, category: str, pages: int = 1) -> List[Product]:
        """获取品类 Best Sellers

        Args:
            category: 品类名称（如 "Home & Kitchen"）
            pages: 抓取页数（每页约 48 个产品）

        Returns:
            产品列表
        """
        if self.is_demo:
            print(f"🎮 Demo 模式：生成 '{category}' 品类的模拟 Best Sellers 数据...")
            return _generate_demo_products(category, None, pages)

        # 尝试映射品类名称到 category_id
        cat_id = self.CATEGORY_MAP.get(category.lower().strip(), category)

        all_products = []
        for page in range(1, pages + 1):
            # 先尝试 bestsellers 接口
            params = {
                "api_key": self.api_key,
                "type": "bestsellers",
                "category_id": cat_id,
                "amazon_domain": "amazon.com",
                "page": page,
            }
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                products = self._parse_products(data, category)

                # 如果 bestsellers 为空，改用搜索
                if not products and page == 1:
                    print(f"  ℹ️ Best Sellers 未返回数据，改用搜索模式...")
                    return self.search_products(f"best sellers {category}", pages)

                all_products.extend(products)
                print(f"  ✅ 第 {page} 页：获取 {len(products)} 个产品")
                time.sleep(1)
            except requests.RequestException as e:
                print(f"  ⚠️ Best Sellers 请求失败：{e}")
                print(f"  ℹ️ 改用搜索模式...")
                if page == 1:
                    return self.search_products(f"popular {category}", pages)
                break

        if not all_products:
            print(f"  ℹ️ 改用关键词搜索...")
            return self.search_products(f"popular {category}", pages)

        return all_products

    def search_products(self, keyword: str, pages: int = 1) -> List[Product]:
        """关键词搜索产品

        Args:
            keyword: 搜索关键词
            pages: 抓取页数

        Returns:
            产品列表
        """
        if self.is_demo:
            print(f"🎮 Demo 模式：生成关键词 '{keyword}' 的模拟搜索结果...")
            return _generate_demo_products("", keyword, pages)

        all_products = []
        for page in range(1, pages + 1):
            params = {
                "api_key": self.api_key,
                "type": "search",
                "search_term": keyword,
                "amazon_domain": "amazon.com",
                "page": page,
            }
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                products = self._parse_products(data, "")
                all_products.extend(products)
                print(f"  ✅ 第 {page} 页：获取 {len(products)} 个产品")
                time.sleep(1)
            except requests.RequestException as e:
                print(f"  ❌ 第 {page} 页请求失败：{e}")
                break

        return all_products

    def _parse_products(self, data: dict, category: str) -> List[Product]:
        """解析 API 响应数据为 Product 列表

        Args:
            data: Rainforest API 响应 JSON
            category: 品类名称

        Returns:
            产品列表
        """
        products = []
        results = data.get("bestsellers", data.get("search_results", []))

        for item in results:
            try:
                product = Product(
                    asin=item.get("asin", ""),
                    title=item.get("title", ""),
                    brand=item.get("brand", ""),
                    category=category,
                    price=float(item.get("price", {}).get("value", 0)),
                    rating=float(item.get("rating", 0)),
                    reviews_count=int(item.get("ratings_total", 0)),
                    bsr=self._extract_bsr(item),
                    monthly_sales_est=self._estimate_sales(
                        item.get("ratings_total", 0)
                    ),
                    monthly_revenue_est=0,
                    seller_count=1,
                    buy_box_seller=item.get("brand", ""),
                    weight_grams=self._extract_weight(item),
                    dimensions=self._extract_dimensions(item),
                    listing_quality_score=self._assess_listing_quality(item),
                    date_first_available=item.get("date_first_available", ""),
                )
                product.monthly_revenue_est = round(
                    product.price * product.monthly_sales_est, 2
                )
                products.append(product)
            except (ValueError, TypeError) as e:
                print(f"  ⚠️ 解析产品失败 (ASIN: {item.get('asin', 'N/A')}): {e}")
                continue

        return products

    @staticmethod
    def _extract_bsr(item: dict) -> int:
        """提取 BSR 排名"""
        bsr_data = item.get("bestsellers_rank", [])
        if bsr_data:
            return int(bsr_data[0].get("rank", 99999))
        return 99999

    @staticmethod
    def _estimate_sales(ratings_total: int) -> int:
        """根据评论数估算月销量（经验公式：月销量 ≈ 评论数 × 8 / 月数）"""
        if ratings_total <= 0:
            return 0
        # 假设产品平均寿命 24 个月
        monthly = ratings_total * 8 / 24
        return int(max(monthly, 10))

    @staticmethod
    def _extract_weight(item: dict) -> float:
        """提取重量（克）"""
        weight_str = item.get("weight", "")
        if isinstance(weight_str, (int, float)):
            return float(weight_str)
        # 尝试解析 "340 g" 格式
        try:
            parts = str(weight_str).split()
            if len(parts) >= 2 and "g" in parts[1].lower():
                return float(parts[0])
            if len(parts) >= 2 and "lb" in parts[1].lower():
                return float(parts[0]) * 453.6
            if len(parts) >= 2 and "oz" in parts[1].lower():
                return float(parts[0]) * 28.35
        except (ValueError, IndexError):
            pass
        return 500.0  # 默认 500g

    @staticmethod
    def _extract_dimensions(item: dict) -> tuple:
        """提取尺寸（cm）"""
        dims = item.get("dimensions", "")
        if isinstance(dims, tuple):
            return dims
        # 尝试解析 "7.6 x 5.1 x 20.3 cm" 格式
        try:
            import re
            match = re.search(
                r"([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)", str(dims)
            )
            if match:
                return (float(match.group(1)), float(match.group(2)), float(match.group(3)))
        except (ValueError, AttributeError):
            pass
        return (20.0, 10.0, 5.0)  # 默认尺寸

    @staticmethod
    def _assess_listing_quality(item: dict) -> float:
        """评估 Listing 质量（0-100）"""
        score = 50  # 基础分

        # 有标题加分
        if len(item.get("title", "")) > 80:
            score += 15
        elif len(item.get("title", "")) > 50:
            score += 10

        # 有图片加分
        images = item.get("images", [])
        if len(images) >= 5:
            score += 15
        elif len(images) >= 3:
            score += 10

        # 有 A+ 内容加分
        if item.get("a-plus", False):
            score += 10

        # 评分高加分
        rating = float(item.get("rating", 0))
        if rating >= 4.0:
            score += 10
        elif rating >= 3.5:
            score += 5

        return min(score, 100)
