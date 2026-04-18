"""AI 深度分析器

调用 AI API 对产品进行深度分析，包括：
- 差评痛点挖掘
- 改进建议
- 市场机会评估
- 竞争策略建议

无 AI API key 时使用基于规则的分析。
"""

from typing import Optional

from ..models.product import Product


# 基于规则的分析模板
RULE_BASED_TEMPLATES = {
    "listing_improvement": (
        "## Listing 优化建议\n"
        "- 当前 Listing 质量评分：{quality_score}/100\n"
        "- {quality_advice}\n"
        "- 建议优化产品图片，确保有 5 张以上高质量图片\n"
        "- 标题应包含核心关键词，长度建议 150-200 字符\n"
    ),
    "price_strategy": (
        "## 定价策略\n"
        "- 当前售价：${price}\n"
        "- 估算毛利：${profit}（毛利率 {margin}%）\n"
        "- {price_advice}\n"
    ),
    "competition_analysis": (
        "## 竞争分析\n"
        "- 当前卖家数量：{sellers}\n"
        "- 评论数量：{reviews}\n"
        "- {competition_advice}\n"
    ),
    "opportunity_assessment": (
        "## 机会评估\n"
        "- 月估算销量：{sales}/月\n"
        "- 月估算营收：${revenue}\n"
        "- {opportunity_advice}\n"
    ),
}


def _get_quality_advice(score: float) -> str:
    """根据 Listing 质量评分给出建议"""
    if score >= 85:
        return "Listing 质量优秀，保持当前水平即可"
    elif score >= 70:
        return "Listing 质量尚可，建议优化图片和描述"
    elif score >= 55:
        return "Listing 质量一般，存在较大优化空间，这是切入该市场的好机会"
    else:
        return "Listing 质量较差，存在巨大的优化空间，强烈建议进入"


def _get_price_advice(product: Product) -> str:
    """根据价格和利润给出定价建议"""
    if product.profit_margin >= 35:
        return "利润空间充足，可以适当降价抢占市场份额"
    elif product.profit_margin >= 20:
        return "利润空间适中，建议通过优化供应链提高毛利"
    elif product.profit_margin >= 10:
        return "利润空间偏薄，需要严格控制成本或提高售价"
    else:
        return "利润空间过小，不建议进入该品类"


def _get_competition_advice(product: Product) -> str:
    """根据竞争情况给出建议"""
    parts = []
    if product.seller_count <= 2:
        parts.append("卖家数量少，竞争压力小")
    elif product.seller_count <= 5:
        parts.append("卖家数量适中，有一定竞争")
    else:
        parts.append("卖家数量多，竞争激烈")

    if product.reviews_count < 200:
        parts.append("评论数较少，新卖家容易追赶")
    elif product.reviews_count < 1000:
        parts.append("评论数中等，需要一定的投入才能追赶")
    else:
        parts.append("评论数很多，评论壁垒较高")

    return "，".join(parts)


def _get_opportunity_advice(product: Product) -> str:
    """根据机会维度给出建议"""
    parts = []
    if product.monthly_sales_est >= 800:
        parts.append("市场需求旺盛")
    elif product.monthly_sales_est >= 300:
        parts.append("市场需求稳定")

    if product.is_on_promotion:
        parts.append("⚠️ 注意：当前产品在促销中，价格可能低于常态")

    if product.listing_quality_score < 70:
        parts.append("现有产品 Listing 质量差，有明显的超越机会")

    if not parts:
        parts.append("建议进一步分析差评痛点，寻找差异化切入点")

    return "；".join(parts)


class AIAnalyzer:
    """AI 深度分析器

    支持两种模式：
    - AI 模式：调用 OpenAI 兼容 API 进行深度分析
    - 规则模式：无 API key 时使用规则引擎分析
    """

    def __init__(self, config: dict):
        """初始化分析器

        Args:
            config: AI 配置
        """
        ai_config = config.get("ai", {})
        self.api_key = ai_config.get("api_key", "")
        self.base_url = ai_config.get("base_url", "")
        self.model = ai_config.get("model", "gpt-4o-mini")
        self.use_ai = bool(self.api_key)

    def analyze_product(self, product: Product) -> Product:
        """分析单个产品

        Args:
            product: 产品对象

        Returns:
            包含 AI 分析结果的产品对象
        """
        if self.use_ai:
            product.ai_analysis = self._ai_analyze(product)
        else:
            product.ai_analysis = self._rule_based_analyze(product)
        return product

    def _ai_analyze(self, product: Product) -> str:
        """使用 AI API 进行深度分析"""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url or None)

            prompt = f"""你是一个亚马逊选品专家。请分析以下产品，给出专业的选品建议。

## 产品信息
- ASIN: {product.asin}
- 标题: {product.title}
- 品牌: {product.brand}
- 售价: ${product.price}
- 评分: {product.rating}/5.0
- 评论数: {product.reviews_count}
- BSR 排名: #{product.bsr}
- 月销量估算: {product.monthly_sales_est}
- 卖家数量: {product.seller_count}
- Listing 质量评分: {product.listing_quality_score}/100
- 毛利率: {product.profit_margin}%

## 评分
- 需求分: {product.demand_score}/100
- 竞争分: {product.competition_score}/100
- 利润分: {product.profit_score}/100
- 机会分: {product.opportunity_score}/100
- 总分: {product.total_score}/100

请从以下角度分析：
1. **产品优劣势**：这个产品的核心竞争优势和劣势是什么？
2. **差评痛点**：根据评分和品类特点，推测用户可能的痛点
3. **改进建议**：如果是你来做这个产品，你会怎么改进？
4. **市场机会**：这个细分市场还有哪些切入机会？
5. **风险评估**：进入这个市场有哪些风险？
6. **最终建议**：是否推荐做这个产品？为什么？

请用中文回答，控制在 500 字以内。"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的亚马逊选品顾问。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            print(f"  ⚠️ AI 分析失败，回退到规则分析: {e}")
            return self._rule_based_analyze(product)

    def _rule_based_analyze(self, product: Product) -> str:
        """基于规则的分析（无 AI API 时使用）"""
        sections = []

        # 1. Listing 优化建议
        sections.append(
            RULE_BASED_TEMPLATES["listing_improvement"].format(
                quality_score=product.listing_quality_score,
                quality_advice=_get_quality_advice(product.listing_quality_score),
            )
        )

        # 2. 定价策略
        sections.append(
            RULE_BASED_TEMPLATES["price_strategy"].format(
                price=product.price,
                profit=product.gross_profit,
                margin=product.profit_margin,
                price_advice=_get_price_advice(product),
            )
        )

        # 3. 竞争分析
        sections.append(
            RULE_BASED_TEMPLATES["competition_analysis"].format(
                sellers=product.seller_count,
                reviews=product.reviews_count,
                competition_advice=_get_competition_advice(product),
            )
        )

        # 4. 机会评估
        sections.append(
            RULE_BASED_TEMPLATES["opportunity_assessment"].format(
                sales=product.monthly_sales_est,
                revenue=product.monthly_revenue_est,
                opportunity_advice=_get_opportunity_advice(product),
            )
        )

        # 5. 综合建议
        recommendation = self._get_final_recommendation(product)
        sections.append(f"## 综合建议\n{recommendation}")

        return "\n\n".join(sections)

    @staticmethod
    def _get_final_recommendation(product: Product) -> str:
        """给出最终建议"""
        if product.total_score >= 75:
            return (
                f"⭐ 强烈推荐！该产品总分 {product.total_score}，"
                "各维度表现优秀，建议深入研究并考虑进入。"
            )
        elif product.total_score >= 60:
            return (
                f"✅ 值得考虑。该产品总分 {product.total_score}，"
                "整体表现不错，但需要进一步评估供应链和差异化策略。"
            )
        elif product.total_score >= 45:
            return (
                f"⚠️ 需要谨慎。该产品总分 {product.total_score}，"
                "存在一些风险因素，建议深入调研后再决定。"
            )
        else:
            return (
                f"❌ 不推荐。该产品总分 {product.total_score}，"
                "各维度表现不佳，风险较高。"
            )
