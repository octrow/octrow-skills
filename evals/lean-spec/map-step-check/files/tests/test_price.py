from quote.price import delivery_price


def test_light_standard_order():
    assert delivery_price(5_000, 3_000, express=False) == 1_000


def test_big_order_is_free():
    assert delivery_price(50_000, 3_000, express=False) == 0
