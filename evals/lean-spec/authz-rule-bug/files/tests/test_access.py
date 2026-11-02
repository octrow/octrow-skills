from access import Doc, User, can_edit


def test_owner_edits_own_doc():
    assert can_edit(User(1, False), Doc(1, False, ()))


def test_stranger_cannot_edit():
    assert not can_edit(User(2, False), Doc(1, False, ()))
