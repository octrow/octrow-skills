"""Pick the warehouse that ships an order."""


def pick_warehouse(stock: dict[int, set[str]], items: set[str], distance: dict[int, int]) -> int:
    full = [w for w, have in stock.items() if items <= have]
    if full:
        return min(full, key=lambda w: (distance[w], w))
    return min(stock, key=lambda w: (-len(items & stock[w]), w))
