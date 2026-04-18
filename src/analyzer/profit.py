"""利润计算模块

基于 FBA 费用模型计算产品毛利和毛利率。
"""

from ..models.product import Product
from ..utils.fba_calculator import calculate_fba_total


def calculate_profit(product: Product, cost_ratio: float = 0.28) -> Product:
    """计算产品利润

    Args:
        product: 产品对象
        cost_ratio: 采购成本占售价的比例（默认 28%）

    Returns:
        更新了利润信息的产品对象
    """
    if product.price <= 0:
        return product

    # 1. 佣金（大部分品类 15%）
    referral_fee = round(product.price * 0.15, 2)

    # 2. FBA 配送费 + 仓储费
    if product.dimensions and len(product.dimensions) == 3:
        fba_fee, storage_fee = calculate_fba_total(
            product.dimensions[0],
            product.dimensions[1],
            product.dimensions[2],
            product.weight_kg,
        )
    else:
        # 没有尺寸信息时用默认值
        fba_fee, storage_fee = 4.50, 0.50

    # 3. 估算采购成本
    estimated_cost = round(product.price * cost_ratio, 2)

    # 4. 毛利 = 售价 - 佣金 - FBA费 - 仓储费 - 采购成本
    gross_profit = round(
        product.price - referral_fee - fba_fee - storage_fee - estimated_cost,
        2,
    )

    # 5. 毛利率
    profit_margin = round((gross_profit / product.price) * 100, 2) if product.price > 0 else 0

    # 更新产品对象
    product.referral_fee = referral_fee
    product.fba_fee = fba_fee
    product.storage_fee = storage_fee
    product.estimated_cost = estimated_cost
    product.gross_profit = gross_profit
    product.profit_margin = profit_margin

    return product


def calculate_profit_batch(products: list, cost_ratio: float = 0.28) -> list:
    """批量计算利润

    Args:
        products: 产品列表
        cost_ratio: 采购成本比例

    Returns:
        更新了利润信息的产品列表
    """
    return [calculate_profit(p, cost_ratio) for p in products]
