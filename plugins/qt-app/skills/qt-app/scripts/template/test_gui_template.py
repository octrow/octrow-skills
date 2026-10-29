"""The template's own check, and the starting tests for a project: copy to tests/gui/test_shell.py
and change ``from gui`` to ``from <pkg>.gui``.

    QT_QPA_PLATFORM=offscreen python -m pytest test_gui_template.py   # needs PySide6, qtawesome, pytest-qt
"""

import asyncio
import os
import threading

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtCore import Qt, QThread  # noqa: E402
from PySide6.QtWidgets import QMessageBox  # noqa: E402

from gui import theme  # noqa: E402
from gui.app import MainWindow  # noqa: E402
from gui.bridge import USER_ERROR, CoreRunner, in_daemon_thread  # noqa: E402
from gui.screens.home import CANCELLED, HomeScreen  # noqa: E402

WAIT_MS = 3000


@pytest.fixture
def runner(qapp):
    r = CoreRunner()
    yield r
    r.shutdown()  # always: a leaked loop thread breaks later tests in the same QApplication


async def _answer() -> int:
    await asyncio.sleep(0)
    return 42


def test_result_arrives_on_the_gui_thread(qtbot, qapp, runner):
    seen = []
    job = runner.submit(_answer())
    job.finished.connect(lambda value: seen.append((value, QThread.currentThread())))
    with qtbot.waitSignal(job.finished, timeout=WAIT_MS) as blocker:
        blocker.connect(job.failed)  # a failure ends the wait at once instead of a timeout
    assert seen == [(42, qapp.thread())]


def test_an_exception_becomes_failed_with_a_message_free_of_internals(qtbot, runner):
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    job = runner.submit(boom())
    with qtbot.waitSignal(job.failed, timeout=WAIT_MS) as blocker:
        pass
    assert blocker.args == [USER_ERROR]


def test_cancel_fires_only_after_the_coroutine_cleaned_up(qtbot, runner):
    started, cleaned, at_cancel = threading.Event(), [], []

    async def sleeper() -> None:
        try:
            started.set()
            await asyncio.sleep(60)
        finally:
            await asyncio.sleep(0.05)  # an aclose() that takes a moment
            cleaned.append(True)

    job = runner.submit(sleeper())
    job.cancelled.connect(lambda: at_cancel.append(list(cleaned)))
    assert started.wait(WAIT_MS / 1000)
    with qtbot.waitSignal(job.cancelled, timeout=WAIT_MS):
        job.cancel()
    assert at_cancel == [[True]]


def test_shutdown_cancels_running_work_and_joins_the_loop_thread(qapp):
    r = CoreRunner()
    r.submit(asyncio.sleep(60))
    r.shutdown()
    assert not r._thread.is_alive()


def test_a_blocking_call_runs_on_a_daemon_thread_and_cancel_sets_its_stop(qtbot, runner):
    stop, started = threading.Event(), threading.Event()
    job = runner.submit(in_daemon_thread(lambda: threading.current_thread().daemon, stop))
    with qtbot.waitSignal(job.finished, timeout=WAIT_MS) as blocker:
        blocker.connect(job.failed)
    assert blocker.args == [True]

    def blocking() -> None:
        started.set()
        stop.wait(WAIT_MS / 1000)

    job = runner.submit(in_daemon_thread(blocking, stop))
    assert started.wait(WAIT_MS / 1000)
    with qtbot.waitSignal(job.cancelled, timeout=WAIT_MS):
        job.cancel()
    assert stop.is_set()


def _contrast(fg: str, bg: str) -> float:
    def lum(c: str) -> float:
        ch = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in ch]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("palette", [theme.LIGHT, theme.DARK], ids=["light", "dark"])
def test_every_text_pair_meets_wcag_aa(palette):
    failing = {pair: round(_contrast(palette[pair[0]], palette[pair[1]]), 2) for pair in theme.TEXT_PAIRS
               if _contrast(palette[pair[0]], palette[pair[1]]) < 4.5}
    assert failing == {}
    assert _contrast(palette["border_strong"], palette["surface"]) >= 3.0  # input outlines


def test_both_palettes_define_the_same_tokens_and_all_reach_the_qss():
    assert theme.LIGHT.keys() == theme.DARK.keys()
    qss = theme.build_qss(theme.DARK)
    assert {k for k, v in theme.DARK.items() if v not in qss} == set()


def test_forcing_dark_restyles_the_app(qapp):
    theme.apply_theme(qapp)
    theme.force_scheme(Qt.ColorScheme.Dark)
    try:
        assert theme.DARK["window"] in qapp.styleSheet()
    finally:
        theme.force_scheme(Qt.ColorScheme.Light)


def test_the_window_fits_its_minimum_and_every_screen_has_a_heading(qtbot, runner):
    window = MainWindow(runner)
    qtbot.addWidget(window)
    window.resize(*theme.MIN_WINDOW)
    window.show()
    assert window.screen_names() == ["Главная"]


def test_closing_over_running_work_asks_and_no_keeps_the_window(qtbot, runner, monkeypatch):
    window = MainWindow(runner)
    qtbot.addWidget(window)
    window.show()
    runner.submit(asyncio.sleep(60))
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    window.close()
    assert window.isVisible()


def test_home_runs_the_core_and_shows_the_result(qtbot, runner):
    screen = HomeScreen(runner, core=lambda text: _echo(text))
    qtbot.addWidget(screen)
    screen.query.setText("пример")
    screen.start()
    assert not screen.run_button.isEnabled()
    qtbot.waitUntil(lambda: not screen.is_running(), timeout=WAIT_MS)
    assert screen.status.text() == "эхо: пример"
    assert screen.run_button.isEnabled()


def test_home_cancel_stops_the_core_and_says_so(qtbot, runner):
    screen = HomeScreen(runner, core=lambda text: asyncio.sleep(60, result=text))
    qtbot.addWidget(screen)
    screen.query.setText("долго")
    screen.start()
    screen.cancel_button.click()
    qtbot.waitUntil(lambda: not screen.is_running(), timeout=WAIT_MS)
    assert screen.status.text() == CANCELLED


async def _echo(text: str) -> str:
    return f"эхо: {text}"
