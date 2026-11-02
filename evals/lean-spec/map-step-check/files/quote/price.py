"""Delivery price in tenge."""
import math

FREE_FROM = 20_000
BASE = 1_000
PER_KG = 200
FREE_KG = 5


def delivery_price(order_total: int, weight_g: int, express: bool) -> int:
    if order_total > FREE_FROM:
        return 0
    extra_kg = max(0, math.ceil((weight_g - FREE_KG * 1000) / 1000))
    standard = BASE + PER_KG * extra_kg
    return standard * 2 if express else standard
