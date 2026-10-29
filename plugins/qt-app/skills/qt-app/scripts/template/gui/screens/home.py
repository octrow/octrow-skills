"""Example screen: a form card that runs one core call through the runner, with a status and cancel.

Replace ``_example_core`` with the function the CLI command calls, and the texts with the CLI's
own (a shared Qt-free module), so both entry points say and do the same thing.
"""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ..bridge import CoreRunner, Job
from ..theme import PAGE_GAP, SPACE, card_body, set_state

Core = Callable[[str], Coroutine[Any, Any, str]]

RUN = "Запустить"
RUNNING = "Выполняется…"
CANCEL = "Отмена"
CANCELLED = "Остановлено."
PLACEHOLDER = "Что сделать?"


async def _example_core(text: str) -> str:
    await asyncio.sleep(0.2)
    return f"Готово: {text}"


class HomeScreen(QWidget):
    def __init__(self, runner: CoreRunner, core: Core = _example_core) -> None:
        super().__init__()
        self._runner, self._core = runner, core
        self._job: Job | None = None
        self.query = QLineEdit(placeholderText=PLACEHOLDER)
        self.run_button = QPushButton(RUN)
        set_state(self.run_button, "primary", "true")  # one primary action per screen
        self.cancel_button = QPushButton(CANCEL, enabled=False)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.run_button.clicked.connect(self.start)
        self.query.returnPressed.connect(self.start)
        self._lay_out()

    def _lay_out(self) -> None:
        card = QGroupBox("Задача")
        body = card_body(QVBoxLayout(card))
        body.addWidget(self.query)
        buttons = QHBoxLayout()
        buttons.setSpacing(SPACE["sm"])
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch(1)
        body.addLayout(buttons)
        page = QVBoxLayout(self)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(PAGE_GAP)
        page.addWidget(card)
        page.addWidget(self.status)

    def is_running(self) -> bool:
        return self._job is not None

    def start(self) -> None:
        if self._job is not None or not (text := self.query.text().strip()):
            return
        job = self._job = self._runner.submit(self._core(text))
        job.finished.connect(lambda result: self._settle(result, "ok"))
        job.failed.connect(lambda message: self._settle(message, "error"))
        job.cancelled.connect(lambda: self._settle(CANCELLED, "warning"))
        self.cancel_button.clicked.connect(job.cancel)
        self._set_busy(True)
        self._show(RUNNING, "muted")

    def _settle(self, text: str, state: str) -> None:
        """Exactly one outcome per job reaches here: finished, failed or cancelled."""
        self.cancel_button.clicked.disconnect()
        self._job = None
        self._set_busy(False)
        self._show(text, state)

    def _set_busy(self, busy: bool) -> None:
        self.run_button.setEnabled(not busy)
        self.run_button.setText(RUNNING if busy else RUN)
        self.cancel_button.setEnabled(busy)
        self.query.setEnabled(not busy)

    def _show(self, text: str, state: str) -> None:
        self.status.setText(text)
        set_state(self.status, "role", "muted" if state == "muted" else "")
        set_state(self.status, "state", "" if state == "muted" else state)
