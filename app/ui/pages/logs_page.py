"""Logs page wrapping the colour-coded console."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QWidget

from app.ui.pages.base_page import BasePage
from app.widgets.cards import Card
from app.widgets.log_view import LogView


class LogsPage(BasePage):
    """Displays application log records with export support."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Logs", "Application events and diagnostics", parent)
        card = Card()
        self._log_view = LogView()
        card.body().addWidget(self._log_view)
        self.content().addWidget(card, 1)

    def append(self, level: str, message: str, timestamp: str) -> None:
        self._log_view.append(level, message, timestamp)
