"""Keepa API 数据采集器

获取价格历史、BSR 历史趋势、促销状态等信息。
无 API key 时使用 demo 模式。
"""

import random
from typing import Dict, List, Optional, Tuple

from ..models.product import Product


class KeepaCollector:
    """Keepa 数据采集器

    提供价格历史和 BSR 历史数据，帮助判断：
    - 产品是否在促销期
    - 价格趋势（稳定/上涨/下跌）
    - BSR 趋势（排名改善/恶化）
    """

    BASE_URL = "https://api.keepa.com/product"

    def __init__(self, api_key: str):
        """初始化采集器

        Args:
            api_key: Keepa API key，留空使用 demo 模式
        """
        self.api_key = api_key
        self.is_demo = not api_key or api_key == "YOUR_API_KEY"

    def get_price_history(self, asin: str) -> Tuple[List[float], bool]:
        """获取近 30 天价格历史

        Args:
            asin: 产品 ASIN

        Returns:
            (价格列表, 是否在促销中)
        """
        if self.is_demo:
            return self._demo_price_history(asin)

        # 真实 API 调用
        try:
            import requests

            params = {"key": self.api_key, "domain": 1, "asin": asin}
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            products = data.get("products", [])
            if not products:
                return [], False

            # 解析 Keepa 价格数据（CSV 格式，每 3 小时一个数据点）
            csv_data = products[0].get("csv", [])
            if not csv or len(csv) < 1:
                return [], False

            # AMAZON_NEW 价格索引为 1
            amazon_prices = csv_data[1] if len(csv_data) > 1 else []
            prices = []
            # 只取最近 30 天的数据（约 240 个数据点，每 3 小时一个）
            recent = amazon_prices[-240:] if amazon_prices else []
            for p in recent:
                if p > 0:  # Keepa 用 0 表示无数据
                    prices.append(p / 100)  # Keepa 价格以分为单位

            is_promo = self._detect_promotion(prices)
            return prices, is_promo

        except Exception as e:
            print(f"  ⚠️ Keepa 价格查询失败 ({asin}): {e}")
            return self._demo_price_history(asin)

    def get_bsr_history(self, asin: str) -> List[int]:
        """获取近 30 天 BSR 历史

        Args:
            asin: 产品 ASIN

        Returns:
            BSR 列表
        """
        if self.is_demo:
            return self._demo_bsr_history(asin)

        try:
            import requests

            params = {"key": self.api_key, "domain": 1, "asin": asin}
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            products = data.get("products", [])
            if not products:
                return []

            csv_data = products[0].get("csv", [])
            # BSR 数据索引为 3
            bsr_data = csv_data[3] if len(csv_data) > 3 else []
            bsr_list = []
            recent = bsr_data[-240:] if bsr_data else []
            for b in recent:
                if b > 0:
                    bsr_list.append(b)

            return bsr_list

        except Exception as e:
            print(f"  ⚠️ Keepa BSR 查询失败 ({asin}): {e}")
            return self._demo_bsr_history(asin)

    def enrich_product(self, product: Product) -> Product:
        """用 Keepa 数据丰富产品信息

        Args:
            product: 产品对象

        Returns:
            丰富后的产品对象
        """
        prices, is_promo = self.get_price_history(product.asin)
        bsr_list = self.get_bsr_history(product.asin)

        product.price_history = prices
        product.bsr_history = bsr_list
        product.is_on_promotion = is_promo

        return product

    def _detect_promotion(self, prices: List[float]) -> bool:
        """检测是否在促销期

        判断逻辑：如果最近 3 天价格低于近 30 天平均价格的 15%，
        认为在促销中。
        """
        if len(prices) < 10:
            return False
        avg_price = sum(prices) / len(prices)
        recent_avg = sum(prices[-3:]) / 3
        return recent_avg < avg_price * 0.85

    @staticmethod
    def _demo_price_history(asin: str) -> Tuple[List[float], bool]:
        """生成模拟价格历史"""
        base_price = hash(asin) % 30 + 15  # 基于ASIN生成基准价格
        prices = []
        for i in range(30):
            daily_variation = random.uniform(-2, 2)
            prices.append(round(base_price + daily_variation, 2))

        # 随机决定是否在促销
        is_promo = random.random() < 0.2  # 20% 概率在促销
        if is_promo:
            for i in range(-5, 0):
                prices[i] = round(prices[i] * 0.7, 2)

        return prices, is_promo

    @staticmethod
    def _demo_bsr_history(asin: str) -> List[int]:
        """生成模拟 BSR 历史"""
        base_bsr = (hash(asin) % 80000) + 1000
        bsr_list = []
        for i in range(30):
            variation = random.uniform(-500, 500)
            bsr_list.append(max(100, int(base_bsr + variation)))
        return bsr_list
