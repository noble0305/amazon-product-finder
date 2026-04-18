"""多维度评分引擎

对产品进行需求、竞争、利润、机会四个维度的评分，
并计算加权总分。
"""

from ..models.product import Product


class Scorer:
    """评分引擎

    评分维度和权重：
    - 需求分 × 0.35：BSR、月销量、评分
    - 竞争分 × 0.30：评论数、卖家数
    - 利润分 × 0.25：售价区间、毛利率、FBA费用占比
    - 机会分 × 0.10：Listing质量、改进空间
    """

    def __init__(self, config: dict):
        """初始化评分引擎

        Args:
            config: 评分配置，包含权重和筛选条件
        """
        scoring = config.get("scoring", {})
        self.demand_weight = scoring.get("demand_weight", 0.35)
        self.competition_weight = scoring.get("competition_weight", 0.30)
        self.profit_weight = scoring.get("profit_weight", 0.25)
        self.opportunity_weight = scoring.get("opportunity_weight", 0.10)

    def score_product(self, product: Product) -> Product:
        """对单个产品进行评分

        Args:
            product: 产品对象（需先完成利润计算）

        Returns:
            评分后的产品对象
        """
        product.demand_score = self._calc_demand_score(product)
        product.competition_score = self._calc_competition_score(product)
        product.profit_score = self._calc_profit_score(product)
        product.opportunity_score = self._calc_opportunity_score(product)

        # 加权总分
        product.total_score = round(
            product.demand_score * self.demand_weight
            + product.competition_score * self.competition_weight
            + product.profit_score * self.profit_weight
            + product.opportunity_score * self.opportunity_weight,
            2,
        )

        return product

    def score_products(self, products: list) -> list:
        """批量评分

        Args:
            products: 产品列表

        Returns:
            评分后的产品列表（按总分降序排列）
        """
        scored = [self.score_product(p) for p in products]
        scored.sort(key=lambda p: p.total_score, reverse=True)
        return scored

    @staticmethod
    def _calc_demand_score(product: Product) -> float:
        """计算需求分（0-100）

        评估指标：
        - BSR 排名越低越好
        - 月销量越高越好
        - 评分在 3.5-4.5 之间最佳
        """
        score = 50.0  # 基础分

        # BSR 评分（排名越低分越高）
        if product.bsr <= 1000:
            score += 25
        elif product.bsr <= 5000:
            score += 20
        elif product.bsr <= 15000:
            score += 15
        elif product.bsr <= 30000:
            score += 10
        elif product.bsr <= 50000:
            score += 5
        else:
            score -= 5

        # 月销量评分
        if product.monthly_sales_est >= 1000:
            score += 15
        elif product.monthly_sales_est >= 500:
            score += 12
        elif product.monthly_sales_est >= 300:
            score += 8
        elif product.monthly_sales_est >= 100:
            score += 5

        # 评分区间（3.5-4.5 最佳，说明有需求但不是完全成熟）
        if 3.5 <= product.rating <= 4.5:
            score += 10
        elif 4.0 <= product.rating <= 4.8:
            score += 8
        elif product.rating >= 4.5:
            score += 5
        else:
            score -= 5

        return max(0, min(100, round(score, 2)))

    @staticmethod
    def _calc_competition_score(product: Product) -> float:
        """计算竞争分（0-100，分数越高表示竞争越小）

        评估指标：
        - 评论数越少竞争越小
        - 卖家数越少竞争越小
        """
        score = 50.0

        # 评论数量（越少竞争越小，得分越高）
        if product.reviews_count < 50:
            score += 25
        elif product.reviews_count < 200:
            score += 20
        elif product.reviews_count < 500:
            score += 15
        elif product.reviews_count < 1000:
            score += 5
        else:
            score -= 10

        # 卖家数量
        if product.seller_count <= 2:
            score += 15
        elif product.seller_count <= 5:
            score += 10
        elif product.seller_count <= 10:
            score += 3
        else:
            score -= 5

        # 月销量与评论比（高销量低评论 = 竞争不激烈但需求大）
        if product.reviews_count > 0:
            sales_review_ratio = product.monthly_sales_est / product.reviews_count
            if sales_review_ratio > 2:
                score += 10
            elif sales_review_ratio > 1:
                score += 5

        return max(0, min(100, round(score, 2)))

    @staticmethod
    def _calc_profit_score(product: Product) -> float:
        """计算利润分（0-100）

        评估指标：
        - 售价在 $15-50 最佳
        - 毛利率越高越好
        - FBA 费用占比越低越好
        """
        score = 40.0

        # 售价区间
        if 15 <= product.price <= 50:
            score += 20
        elif 10 <= product.price <= 75:
            score += 10
        else:
            score -= 5

        # 毛利率
        if product.profit_margin >= 40:
            score += 20
        elif product.profit_margin >= 30:
            score += 15
        elif product.profit_margin >= 20:
            score += 10
        elif product.profit_margin >= 10:
            score += 5
        else:
            score -= 10

        # FBA 费用占售价比例
        if product.price > 0:
            fba_ratio = product.fba_fee / product.price * 100
            if fba_ratio < 15:
                score += 10
            elif fba_ratio < 25:
                score += 5
            elif fba_ratio < 35:
                score += 0
            else:
                score -= 5

        return max(0, min(100, round(score, 2)))

    @staticmethod
    def _calc_opportunity_score(product: Product) -> float:
        """计算机会分（0-100）

        评估指标：
        - Listing 质量差但卖得好 = 有改进空间
        - 近期上架的新品占比
        - 促销状态（促销中可能不是真实价格）
        """
        score = 50.0

        # Listing 质量与销量的反差（质量差但销量高 = 有改进空间）
        if product.listing_quality_score < 70 and product.monthly_sales_est > 300:
            score += 20
        elif product.listing_quality_score < 80 and product.monthly_sales_est > 200:
            score += 10
        elif product.listing_quality_score >= 85:
            score -= 5  # Listing 已经很好，改进空间不大

        # 新品加分（上架不到 6 个月）
        if product.date_first_available:
            try:
                from datetime import datetime
                date_str = product.date_first_available
                if len(date_str) >= 10:
                    date_available = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    days_on_market = (datetime.now() - date_available).days
                    if days_on_market < 90:
                        score += 15
                    elif days_on_market < 180:
                        score += 10
                    elif days_on_market < 365:
                        score += 5
            except (ValueError, TypeError):
                pass

        # 促销中的产品扣分（价格可能不是常态）
        if product.is_on_promotion:
            score -= 10

        # 评论中有明确改进空间（评论数 > 100 且评分 < 4.0）
        if product.reviews_count > 100 and product.rating < 4.0:
            score += 10

        return max(0, min(100, round(score, 2)))


def filter_products(products: list, config: dict) -> list:
    """根据筛选条件过滤产品

    Args:
        products: 产品列表
        config: 配置（包含 filters 部分）

    Returns:
        过滤后的产品列表
    """
    filters = config.get("filters", {})
    filtered = []

    for p in products:
        # 价格范围
        min_price = filters.get("min_price", 0)
        max_price = filters.get("max_price", float("inf"))
        if not (min_price <= p.price <= max_price):
            continue

        # 评论数范围
        min_reviews = filters.get("min_reviews", 0)
        max_reviews = filters.get("max_reviews", float("inf"))
        if not (min_reviews <= p.reviews_count <= max_reviews):
            continue

        # 最低评分
        min_rating = filters.get("min_rating", 0)
        if p.rating < min_rating:
            continue

        # 最大 BSR
        max_bsr = filters.get("max_bsr", float("inf"))
        if p.bsr > max_bsr:
            continue

        filtered.append(p)

    return filtered
