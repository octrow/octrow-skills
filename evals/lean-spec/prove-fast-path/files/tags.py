"""Tag ids attached to a search query."""

def normalize(tag_ids: list[int]) -> list[int]:
    """Sorted ascending, each id once."""
    return sorted(set(tag_ids))


def normalize_fast(tag_ids: list[int]) -> list[int]:
    """Same as normalize without the set and the sort: the index returns tag ids sorted, so drop repeats in one pass."""
    out: list[int] = []
    for tag in tag_ids:
        if not out or out[-1] != tag:
            out.append(tag)
    return out
