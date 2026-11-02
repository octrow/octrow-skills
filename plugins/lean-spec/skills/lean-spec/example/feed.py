"""Feed of the newest posts. `feed` is the reference; `feed_fast` skips the sort."""
from typing import NamedTuple

FEED_SIZE = 20


class Post(NamedTuple):
    id: int
    created_at: int
    author_id: int


def feed(posts: list[Post], n: int = FEED_SIZE) -> list[Post]:
    return sorted(posts, key=lambda p: (p.created_at, p.id), reverse=True)[:n]


def is_ordered(posts: list[Post]) -> bool:
    """Runtime check of the invariant (Lean: `checkInv`, proved sound by `checkInv_sound`)."""
    return all((a.created_at, a.id) < (b.created_at, b.id) for a, b in zip(posts, posts[1:]))


def feed_fast(posts: list[Post], n: int = FEED_SIZE) -> list[Post]:
    """Equals `feed` when `is_ordered` holds (Lean: `fast_eq_spec`); otherwise falls back."""
    if not is_ordered(posts):
        return feed(posts, n)
    return posts[::-1][:n]
