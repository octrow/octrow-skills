"""The app's look: one palette dict per scheme feeds a generated QSS, every color a named token.

Template from buy-smarter (src/buysmarter/gui/theme/__init__.py). Change the palette values and
the accent; keep the shape: tokens -> build_qss -> apply_theme, and the contrast test over TEXT_PAIRS.
"""

import logging
import os
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtGui import QFontDatabase, QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QLayout, QWidget

os.environ.setdefault("QT_API", "pyside6")  # qtawesome loads Qt through qtpy: never another binding
import qtawesome  # noqa: E402 - needs QT_API first

logger = logging.getLogger(__name__)

# Static faces only (Regular, SemiBold, Bold): Qt registers a variable font as one Regular
# style, so weight 600 renders as 400. No files here -> the platform sans.
FONT_DIR = Path(__file__).parent / "fonts"
FONT_FAMILY = "Inter"

TYPE = {"caption": 12, "body": 14, "subhead": 16, "title": 20, "hero": 28}  # ~1.2 ratio, fixed px
SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}  # a 4px grid
PAGE_GAP = SPACE["xl"]  # between cards: never less than a card's own padding
CARD_GAP = SPACE["md"]  # between rows inside a card
RADIUS = 6
CONTENT_MAX_WIDTH = 1200  # pages stop growing here on a wide monitor
MIN_WINDOW = (960, 640)  # every screen must fit this without clipping

LIGHT = {
    "window": "#F4F6F8",
    "surface": "#FFFFFF",
    "sidebar": "#E9EDF1",
    "border": "#D3D9E0",
    "border_strong": "#848F9B",  # input outlines, 3:1 non-text contrast
    "text": "#16202B",
    "text_muted": "#4A5663",
    "disabled": "#5E6975",
    "accent": "#00758A",
    "accent_hover": "#005F70",
    "on_accent": "#FFFFFF",
    "accent_soft": "#DCEFF2",
    "ok": "#1D7135",
    "warning": "#875200",
    "danger": "#B3261E",
}

DARK = {
    "window": "#11161C",
    "surface": "#192028",
    "sidebar": "#141A21",
    "border": "#2B3540",
    "border_strong": "#5E6B78",
    "text": "#E5EAF0",
    "text_muted": "#A2AEBB",
    "disabled": "#8592A0",
    "accent": "#3FB8CC",
    "accent_hover": "#68CAD9",
    "on_accent": "#08171B",
    "accent_soft": "#173A42",
    "ok": "#5CC27C",
    "warning": "#E0AE4C",
    "danger": "#F28B82",
}

# Every (text, background) pair the QSS renders; the test holds each to WCAG AA 4.5:1.
TEXT_PAIRS = [
    *((fg, bg) for fg in ("text", "text_muted", "disabled") for bg in ("window", "surface", "sidebar")),
    *((fg, bg) for fg in ("ok", "warning", "danger") for bg in ("window", "surface")),
    ("text", "accent_soft"),
    ("on_accent", "accent"),
    ("on_accent", "accent_hover"),
    ("accent", "surface"),
]


def build_qss(p: dict[str, str]) -> str:
    """The app stylesheet for palette ``p``; widgets carry object names and properties, never colors."""
    s, t, r = SPACE, TYPE, RADIUS
    return f"""
* {{ font-family: "{FONT_FAMILY}"; font-size: {t["body"]}px; color: {p["text"]}; }}
QMainWindow, QStackedWidget > QWidget, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {p["window"]}; }}
QScrollArea {{ border: none; }}
QFrame#side {{ background: {p["sidebar"]}; border-right: 1px solid {p["border"]}; }}
QLabel#brand {{ font-size: {t["subhead"]}px; font-weight: 600; }}
QListWidget#sidebar {{ background: transparent; border: none; outline: 0; }}
QListWidget#sidebar::item {{ padding: {s["sm"]}px {s["lg"]}px; color: {p["text_muted"]}; }}
QListWidget#sidebar::item:selected {{ background: {p["accent_soft"]}; color: {p["text"]}; }}
QLabel#hero {{ font-size: {t["hero"]}px; font-weight: 600; }}
QLabel[role="muted"] {{ color: {p["text_muted"]}; }}
QLabel[state="ok"] {{ color: {p["ok"]}; }}
QLabel[state="warning"] {{ color: {p["warning"]}; }}
QLabel[state="error"] {{ color: {p["danger"]}; }}
QGroupBox {{ background: {p["surface"]}; border: 1px solid {p["border"]}; border-radius: {r}px;
             margin-top: 0; padding: {s["xl"]}px; padding-top: {s["xl"] + t["subhead"] + s["md"]}px;
             font-size: {t["subhead"]}px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: padding; left: {s["xl"]}px; top: {s["xl"]}px; }}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{ background: {p["surface"]}; border: 1px solid {p["border_strong"]};
             border-radius: {r}px; padding: {s["sm"]}px; min-height: 18px; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {{ border-color: {p["accent"]}; }}
QPushButton {{ background: {p["surface"]}; border: 1px solid {p["border_strong"]}; border-radius: {r}px;
               padding: {s["sm"]}px {s["lg"]}px; }}
QPushButton:hover {{ border-color: {p["accent"]}; }}
QPushButton:disabled {{ color: {p["disabled"]}; }}
QPushButton[primary="true"] {{ background: {p["accent"]}; color: {p["on_accent"]}; border-color: {p["accent"]}; font-weight: 600; }}
QPushButton[primary="true"]:hover {{ background: {p["accent_hover"]}; }}
QTableView {{ background: {p["surface"]}; border: 1px solid {p["border"]}; gridline-color: {p["border"]};
              selection-background-color: {p["accent_soft"]}; selection-color: {p["text"]}; }}
QHeaderView::section {{ background: {p["sidebar"]}; color: {p["text_muted"]}; border: none; padding: {s["sm"]}px; }}
QToolTip {{ background: {p["surface"]}; color: {p["text"]}; border: 1px solid {p["border"]}; }}
"""


# Offscreen Qt ignores styleHints().setColorScheme(): screenshots and tests force the scheme here.
_forced: Qt.ColorScheme | None = None


def palette_for(scheme: Qt.ColorScheme) -> dict[str, str]:
    return DARK if scheme == Qt.ColorScheme.Dark else LIGHT


def current_scheme() -> Qt.ColorScheme:
    return _forced if _forced is not None else QGuiApplication.styleHints().colorScheme()


def current_palette() -> dict[str, str]:
    return palette_for(current_scheme())


def force_scheme(scheme: Qt.ColorScheme) -> None:
    """Pin the scheme (screenshots, tests) and re-style everything that follows the OS scheme."""
    global _forced
    _forced = scheme
    QGuiApplication.styleHints().colorSchemeChanged.emit(scheme)


def load_font() -> None:
    for path in sorted(FONT_DIR.glob("*.ttf")):
        if QFontDatabase.addApplicationFont(str(path)) < 0:
            logger.warning("Could not load the bundled font %s", path)


def apply_theme(app: QApplication) -> None:
    """Load the font, style the app for the current scheme and follow scheme changes live."""
    load_font()

    def restyle(scheme: Qt.ColorScheme) -> None:
        app.setStyleSheet(build_qss(palette_for(_forced if _forced is not None else scheme)))

    restyle(current_scheme())
    QGuiApplication.styleHints().colorSchemeChanged.connect(restyle)


def icon(name: str, color: str = "text_muted") -> QIcon:
    """A qtawesome icon (``mdi6.*``) in a palette color; redraw it on a scheme change (``bind_icon``)."""
    p = current_palette()
    drawn: QIcon = qtawesome.icon(
        name, color=p[color], color_active=p["accent"], color_selected=p["accent"], color_disabled=p["disabled"]
    )
    return drawn


class _IconBinding(QObject):
    """Keeps one widget's icon in the current scheme's colors; a child, so it dies with its owner."""

    def __init__(self, owner: QObject, setter: Callable[[QIcon], object], name: str, color: str) -> None:
        super().__init__(owner)
        self._setter, self._name, self._color = setter, name, color
        self.repaint()
        QGuiApplication.styleHints().colorSchemeChanged.connect(self.repaint)

    @Slot()
    def repaint(self) -> None:
        self._setter(icon(self._name, self._color))


def bind_icon(owner: QObject, setter: Callable[[QIcon], object], name: str, color: str = "text_muted") -> None:
    """Set ``owner``'s icon now and again on every scheme change: an icon read once stays in the old theme."""
    _IconBinding(owner, setter, name, color)


def card_body[L: QLayout](layout: L) -> L:
    """A card's (QGroupBox's) layout: the QSS padding frames the card, so the layout adds no margins."""
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(CARD_GAP)  # Qt's default 6px is off the 4px grid
    return layout


def set_state(widget: QWidget, name: str, value: str) -> None:
    """Set a dynamic property the QSS keys on (``state``, ``role``, ``primary``) and re-style."""
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
