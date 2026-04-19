"""产品数据模型"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    """亚马逊产品数据模型

    存储产品的所有关键信息，包括基础数据、尺寸重量、
    以及评分结果和 AI 分析结论。
    """
    # 基础信息
    asin: str
    title: str
    brand: str
    category: str
    price: float
    rating: float
    reviews_count: int
    bsr: int  # Best Sellers Rank
    monthly_sales_est: int  # 月销量估算
    monthly_revenue_est: float  # 月营收估算
    seller_count: int  # 卖家数量
    buy_box_seller: str  # Buy Box 卖家
    weight_grams: float  # 重量（克）
    dimensions: tuple  # (长, 宽, 高) cm
    listing_quality_score: float  # Listing 质量 0-100
    date_first_available: str  # 首次上架日期

    # 评分结果
    demand_score: float = 0  # 需求分
    competition_score: float = 0  # 竞争分
    profit_score: float = 0  # 利润分
    opportunity_score: float = 0  # 机会分
    total_score: float = 0  # 总分

    # AI 分析
    ai_analysis: str = ""

    # 利润详情
    referral_fee: float = 0  # 佣金
    fba_fee: float = 0  # FBA 费用
    storage_fee: float = 0  # 仓储费
    estimated_cost: float = 0  # 估算采购成本
    gross_profit: float = 0  # 毛利
    profit_margin: float = 0  # 毛利率

    # 商机探测器数据
    search_volume: int = 0  # 搜索量
    click_share: float = 0  # 点击份额 (%)
    conversion_rate: float = 0  # 商品转化率 (%)
    data_source: str = ""  # 数据来源：rainforest / playwright / opportunity_explorer

    # 站点
    marketplace: str = "us"  # 站点标识

    # 价格历史
    price_history: list = field(default_factory=list)  # 近30天价格列表
    bsr_history: list = field(default_factory=list)  # 近30天 BSR 列表
    is_on_promotion: bool = False  # 是否在促销
    image_url: str = ""  # 商品图片 URL

    @property
    def get_image_url(self) -> str:
        """获取图片 URL，三层兜底策略"""
        if self.image_url:
            return self.image_url
        if self.asin:
            return f"https://ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={self.asin}&Format=_SL250_&ID=AsinImage"
        return ""

    @property
    def volume_cm3(self) -> float:
        """计算体积（立方厘米）"""
        if self.dimensions and len(self.dimensions) == 3:
            return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]
        return 0

    @property
    def weight_kg(self) -> float:
        """重量（千克）"""
        return self.weight_grams / 1000

    def to_dict(self) -> dict:
        """转换为字典，用于数据库存储"""
        return {
            "asin": self.asin,
            "title": self.title,
            "brand": self.brand,
            "category": self.category,
            "price": self.price,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "bsr": self.bsr,
            "monthly_sales_est": self.monthly_sales_est,
            "monthly_revenue_est": self.monthly_revenue_est,
            "seller_count": self.seller_count,
            "buy_box_seller": self.buy_box_seller,
            "weight_grams": self.weight_grams,
            "dimensions": f"{self.dimensions[0]}x{self.dimensions[1]}x{self.dimensions[2]}" if self.dimensions else "",
            "listing_quality_score": self.listing_quality_score,
            "date_first_available": self.date_first_available,
            "demand_score": self.demand_score,
            "competition_score": self.competition_score,
            "profit_score": self.profit_score,
            "opportunity_score": self.opportunity_score,
            "total_score": self.total_score,
            "ai_analysis": self.ai_analysis,
            "referral_fee": self.referral_fee,
            "fba_fee": self.fba_fee,
            "storage_fee": self.storage_fee,
            "estimated_cost": self.estimated_cost,
            "gross_profit": self.gross_profit,
            "profit_margin": self.profit_margin,
            "is_on_promotion": 1 if self.is_on_promotion else 0,
            "image_url": self.image_url,
            "search_volume": self.search_volume,
            "click_share": self.click_share,
            "conversion_rate": self.conversion_rate,
            "data_source": self.data_source,
            "marketplace": self.marketplace,
        }
