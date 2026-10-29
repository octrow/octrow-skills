"""Desktop app entry point: the QApplication, the main window with a sidebar, start-up and shutdown.

Template from buy-smarter (src/buysmarter/gui/app.py). Add a screen: one file in ``screens/``,
one row in ``MainWindow._screens``.
"""

import logging
import os
import signal
import sys
from collections.abc import Callable
from types import TracebackType
from typing import Any, cast

from PySide6.QtCore import QSize, QSocketNotifier, Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .bridge import USER_ERROR, CoreRunner
from .screens.home import HomeScreen
from .theme import CONTENT_MAX_WIDTH, MIN_WINDOW, SPACE, apply_theme, bind_icon

logger = logging.getLogger(__name__)

TITLE = "myapp"
_SIDEBAR_WIDTH = 220
_NAV_ICON_PX = 18
_CLOSE_WHILE_BUSY = "Задача ещё идёт. Закрыть приложение и остановить её?"
_SIGNAL_POLL_MS = 200  # Python runs signal handlers only between bytecodes: Qt's loop must hand back


class MainWindow(QMainWindow):
    """A sidebar of screens next to the current one."""

    def __init__(self, runner: CoreRunner) -> None:
        super().__init__()
        self.setWindowTitle(TITLE)
        self.setMinimumSize(*MIN_WINDOW)
        self.runner = runner
        self.stack = QStackedWidget()
        self.sidebar = _sidebar()
        for title, icon_name, screen in self._screens():
            self.stack.addWidget(_page(screen, title))
            item = QListWidgetItem(title)
            bind_icon(self.sidebar, item.setIcon, icon_name)
            self.sidebar.addItem(item)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        self.setCentralWidget(self._central())

    def _central(self) -> QWidget:
        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self._side_panel())
        row.addWidget(self.stack, 1)
        return central

    def _screens(self) -> tuple[tuple[str, str, QWidget], ...]:
        """(sidebar title = screen heading, qtawesome icon, screen), in display order."""
        return (("Главная", "mdi6.home-outline", HomeScreen(self.runner)),)

    def _side_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("side")
        panel.setFixedWidth(_SIDEBAR_WIDTH)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, SPACE["lg"], 0, SPACE["lg"])
        layout.setSpacing(SPACE["sm"])
        brand = QLabel(TITLE)
        brand.setObjectName("brand")
        brand.setContentsMargins(SPACE["lg"], 0, SPACE["lg"], 0)
        layout.addWidget(brand)
        layout.addWidget(self.sidebar, 1)
        return panel

    def screen_names(self) -> list[str]:
        """For the screenshot script: one name per sidebar row."""
        return [self.sidebar.item(i).text() for i in range(self.sidebar.count())]

    def show_screen(self, index: int) -> None:
        self.sidebar.setCurrentRow(index)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt override
        """Ask before closing over running work; ``run`` then cancels it through the runner."""
        if self.runner.busy():
            answer = QMessageBox.question(
                self,
                TITLE,
                _CLOSE_WHILE_BUSY,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()


def _sidebar() -> QListWidget:
    nav = QListWidget()
    nav.setObjectName("sidebar")
    nav.setIconSize(QSize(_NAV_ICON_PX, _NAV_ICON_PX))
    # A long item must elide, never grow a scroll bar under the navigation.
    nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    nav.setTextElideMode(Qt.TextElideMode.ElideRight)
    return nav


def _page(screen: QWidget, heading: str) -> QScrollArea:
    """``screen`` under its heading, capped in width, centered, and scrolling when it does not fit.

    Every screen scrolls: at the minimum window a page that cannot scroll squeezes its rows and
    clips their text.
    """
    column = QWidget()
    column.setMaximumWidth(CONTENT_MAX_WIDTH)
    stack = QVBoxLayout(column)
    stack.setContentsMargins(SPACE["xxl"], SPACE["xxl"], SPACE["xxl"], SPACE["xxl"])
    stack.setSpacing(SPACE["xl"])
    title = QLabel(heading)
    title.setObjectName("hero")
    stack.addWidget(title)
    stack.addWidget(screen)
    stack.addStretch(1)
    holder = QWidget()
    row = QHBoxLayout(holder)
    row.setContentsMargins(0, 0, 0, 0)
    row.addStretch(0)  # the column fills the width up to its cap; past it, the stretches center it
    row.addWidget(column, 1)
    row.addStretch(0)
    area = QScrollArea(widgetResizable=True)
    area.setWidget(holder)
    return area


def install_excepthook(parent: QWidget) -> Callable[..., Any]:
    """An unexpected error becomes a dialog with a human sentence; the traceback goes to the log."""
    previous = sys.excepthook
    showing = False

    def show_error(exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
        nonlocal showing
        if issubclass(exc_type, KeyboardInterrupt):
            previous(exc_type, exc, tb)
            return
        logger.critical("Unexpected error in the desktop app", exc_info=(exc_type, exc, tb))
        if showing:  # the dialog's own loop hit another error: log it, do not stack dialogs
            return
        showing = True
        try:
            QMessageBox.critical(parent, TITLE, USER_ERROR)
        finally:
            showing = False

    sys.excepthook = show_error
    return previous


def quit_from_terminal(app: QApplication) -> Callable[[], None]:
    """Ctrl+C (and Ctrl+D on a terminal stdin) quit the app; returns the undo.

    A second Ctrl+C during a slow shutdown falls through to the default handler and kills it.
    """

    def on_sigint(*_: object) -> None:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app.quit()

    previous = signal.signal(signal.SIGINT, on_sigint)
    ticker = QTimer(app)
    ticker.timeout.connect(lambda: None)
    ticker.start(_SIGNAL_POLL_MS)
    helpers: list[QTimer | QSocketNotifier] = [ticker]
    if sys.stdin is not None and sys.stdin.isatty():  # a desktop-menu launch has no terminal
        helpers.append(_quit_on_eof(app))

    def undo() -> None:
        signal.signal(signal.SIGINT, previous)
        ticker.stop()
        for helper in helpers:
            helper.deleteLater()

    return undo


def _quit_on_eof(app: QApplication) -> QSocketNotifier:
    """Ctrl+D on an empty terminal line quits; typed lines are ignored."""
    fd = sys.stdin.fileno()
    notifier = QSocketNotifier(fd, QSocketNotifier.Type.Read, app)

    def on_stdin() -> None:
        if not os.read(fd, 1024):
            notifier.setEnabled(False)
            app.quit()

    notifier.activated.connect(on_stdin)
    return notifier


def run(argv: list[str] | None = None) -> int:
    """Show the main window and run the Qt loop until it closes; the runner always shuts down."""
    app = cast(QApplication, QApplication.instance() or QApplication(argv if argv is not None else sys.argv))
    apply_theme(app)
    runner = CoreRunner()
    window = MainWindow(runner)
    previous_hook = install_excepthook(window)
    restore_sigint = quit_from_terminal(app)
    window.show()
    try:
        return app.exec()
    finally:
        restore_sigint()
        sys.excepthook = previous_hook
        runner.shutdown()


def main() -> int:
    """``<app> gui`` and ``python -m <pkg>.gui``: the CLI's own start-up (logging, config), then the window."""
    logging.basicConfig(level=logging.INFO)  # replace with the project's logging setup
    return run()


if __name__ == "__main__":
    sys.exit(main())
