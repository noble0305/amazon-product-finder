"""FBA 费用计算器

根据亚马逊 FBA 费用标准，按产品尺寸和重量计算配送费和仓储费。
参考：https://sellercentral.amazon.com/gp/help/external/GABBX6GZPA8MSZGW
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class SizeTier:
    """产品尺寸分级"""
    name: str
    max_length: float  # cm
    max_median: float  # cm (长+宽+高的中位数)
    max_girth: float  # cm (长+周长)

    @staticmethod
    def girth(length: float, width: float, height: float) -> float:
        """计算周长 = 2 × (最短边 + 次短边)"""
        sides = sorted([length, width, height])
        return 2 * (sides[0] + sides[1])


# 亚马逊 FBA 尺寸分级标准（2024 年费率，单位 cm/kg/USD）
SIZE_TIERS = [
    # 小标准尺寸
    SizeTier("小标准尺寸", max_length=33.02, max_median=33.02, max_girth=163.50),
    # 大标准尺寸
    SizeTier("大标准尺寸", max_length=45.72, max_median=45.72, max_girth=213.36),
    # 小超大尺寸
    SizeTier("小超大尺寸", max_length=152.40, max_median=152.40, max_girth=330.20),
    # 大超大尺寸
    SizeTier("大超大尺寸", max_length=274.32, max_median=274.32, max_girth=508.00),
]

# 小标准尺寸费率表（重量分段）
SMALL_STANDARD_RATES = [
    (0.227, 3.22),   # 0-8 oz
    (0.454, 3.40),   # 9-16 oz
]

# 大标准尺寸费率表
LARGE_STANDARD_RATES = [
    (0.227, 3.86),   # 0-8 oz
    (0.454, 4.08),   # 9-16 oz
    (0.680, 4.24),   # 17-24 oz
    (1.361, 4.75),   # 25-48 oz
    (2.268, 5.43),   # 49-72 oz
    (float("inf"), None),  # > 72 oz 需按超大计算
]

# 小超大尺寸费率
SMALL_OVERSIZE_RATES = [
    (2.268, 9.73),
    (float("inf"), None),
]

# 大超大尺寸费率
LARGE_OVERSIZE_RATES = [
    (2.268, 17.09),
    (float("inf"), None),
]


def classify_size_tier(length: float, width: float, height: float) -> str:
    """判断产品属于哪个尺寸级别

    Args:
        length: 长（cm）
        width: 宽（cm）
        height: 高（cm）

    Returns:
        尺寸级别名称
    """
    longest = max(length, width, height)
    median = sorted([length, width, height])[1]
    girth = SizeTier.girth(length, width, height)

    # 从最小的级别开始判断
    if longest <= 33.02 and median <= 33.02 and girth <= 163.50:
        return "小标准尺寸"
    if longest <= 45.72 and median <= 45.72 and girth <= 213.36:
        return "大标准尺寸"
    if longest <= 152.40 and median <= 152.40 and girth <= 330.20:
        return "小超大尺寸"
    return "大超大尺寸"


def calculate_fba_fee(length: float, width: float, height: float,
                      weight_kg: float) -> float:
    """计算 FBA 配送费

    Args:
        length: 长（cm）
        width: 宽（cm）
        height: 高（cm）
        weight_kg: 重量（kg）

    Returns:
        FBA 配送费（美元）
    """
    tier = classify_size_tier(length, width, height)
    weight_lb = weight_kg * 2.20462  # 转换为磅

    # 根据尺寸级别查找费率
    if tier == "小标准尺寸":
        return _lookup_rate(SMALL_STANDARD_RATES, weight_lb, 3.22)
    elif tier == "大标准尺寸":
        return _lookup_rate(LARGE_STANDARD_RATES, weight_lb, 3.86)
    elif tier == "小超大尺寸":
        return _lookup_rate(SMALL_OVERSIZE_RATES, weight_lb, 9.73)
    else:
        return _lookup_rate(LARGE_OVERSIZE_RATES, weight_lb, 17.09)


def _lookup_rate(rates: list, weight_lb: float, default: float) -> float:
    """在费率表中查找对应费率"""
    for max_weight, fee in rates:
        if weight_lb <= max_weight:
            return fee if fee else default
    return default


def calculate_monthly_storage(length: float, width: float, height: float) -> float:
    """计算月度仓储费

    Args:
        length: 长（cm）
        width: 宽（cm）
        height: 高（cm）

    Returns:
        月度仓储费（美元）
    """
    # 计算体积（立方英尺）
    volume_ft3 = (length * width * height) / (30.48 ** 3)  # cm³ → ft³

    # 标准尺寸：$0.87/立方英尺/月（1-9月淡季费率）
    # 超大尺寸：$0.56/立方英尺/月
    tier = classify_size_tier(length, width, height)
    if "超大" in tier:
        return round(volume_ft3 * 0.56, 2)
    else:
        return round(volume_ft3 * 0.87, 2)


def calculate_fba_total(length: float, width: float, height: float,
                        weight_kg: float) -> Tuple[float, float]:
    """计算 FBA 总费用（配送费 + 月仓储费）

    Args:
        length: 长（cm）
        width: 宽（cm）
        height: 高（cm）
        weight_kg: 重量（kg）

    Returns:
        (配送费, 月仓储费) 单位美元
    """
    shipping_fee = calculate_fba_fee(length, width, height, weight_kg)
    storage_fee = calculate_monthly_storage(length, width, height)
    return round(shipping_fee, 2), round(storage_fee, 2)
