"""Differential test: Python feed vs the Lean model (`lake exe oracle`).

Compare whole posts, not ids: the theorems talk about whole posts, and two posts
with the same key but different authors swap places without changing the ids.
"""
import shutil
import subprocess
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from feed import Post, feed, feed_fast

LEAN = Path(__file__).parent.parent / "lean"
ORACLE = LEAN / ".lake/build/bin/oracle"
# lake may live only in ~/.elan/bin, off PATH in a plain test run.
LAKE = shutil.which("lake") or str(Path.home() / ".elan/bin/lake")
pytestmark = pytest.mark.skipif(not Path(LAKE).exists(), reason="Lean (lake) is not installed")

# Small ranges force ties on created_at, which is where sort bugs hide.
post = st.builds(Post, st.integers(0, 50), st.integers(0, 5), st.integers(0, 3))
any_posts = st.lists(post, max_size=40)


@st.composite
def ordered_posts(draw):
    """Posts that satisfy the invariant: strictly increasing (created_at, id)."""
    keys = sorted(draw(st.sets(st.tuples(st.integers(0, 5), st.integers(0, 50)), max_size=40)))
    return [Post(i, c, draw(st.integers(0, 3))) for c, i in keys]


@pytest.fixture(scope="module")
def oracle():
    subprocess.run([LAKE, "build", "oracle"], cwd=LEAN, check=True, capture_output=True)
    proc = subprocess.Popen([ORACLE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    assert proc.stdin is not None  # Popen types stdin as optional; the repo's type checker wants this
    yield proc
    proc.stdin.close()
    proc.wait()


def ask(oracle, n, posts):
    fields = " ".join(f"{p.id} {p.created_at} {p.author_id}" for p in posts)
    oracle.stdin.write(f"{n} {fields}\n")
    oracle.stdin.flush()
    nums = [int(x) for x in oracle.stdout.readline().split()]
    return [Post(*nums[i : i + 3]) for i in range(0, len(nums), 3)]


@settings(max_examples=500)
@given(posts=any_posts, n=st.integers(0, 25))
def test_feed_matches_model(oracle, posts, n):
    assert feed(posts, n) == ask(oracle, n, posts)


@settings(max_examples=500)
@given(posts=any_posts, n=st.integers(0, 25))
def test_feed_fast_matches_model_on_any_input(oracle, posts, n):
    """Unordered input must take the fallback and still be right."""
    assert feed_fast(posts, n) == ask(oracle, n, posts)


@settings(max_examples=500)
@given(posts=ordered_posts(), n=st.integers(0, 25))
def test_feed_fast_matches_model_on_ordered_input(oracle, posts, n):
    """Ordered input takes the fast path."""
    assert feed_fast(posts, n) == ask(oracle, n, posts)
