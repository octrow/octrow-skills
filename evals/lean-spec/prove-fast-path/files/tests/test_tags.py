from tags import normalize, normalize_fast


def test_fast_on_index_output():
    ids = [1, 1, 2, 5, 5, 5, 9]
    assert normalize_fast(ids) == normalize(ids) == [1, 2, 5, 9]
