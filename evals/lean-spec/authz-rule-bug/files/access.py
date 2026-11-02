"""Who may edit a document."""
from typing import NamedTuple


class User(NamedTuple):
    id: int
    is_admin: bool


class Doc(NamedTuple):
    owner_id: int
    archived: bool
    editors: tuple[int, ...]


def can_edit(user: User, doc: Doc) -> bool:
    """Rules:
    1. Nobody edits an archived document.
    2. The owner and admins edit any other document.
    3. Users listed in editors edit it too.
    """
    if user.is_admin:
        return True
    if doc.archived:
        return False
    return user.id == doc.owner_id or user.id in doc.editors
