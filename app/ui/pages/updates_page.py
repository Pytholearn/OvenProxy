"""Updates page: check for and apply new versions via autoupgrader."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from app.resources.icons import make_icon
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.widgets.cards import Card


class UpdatesPage(BasePage):
    """Surfaces the current/latest version and drives the upgrade flow."""

    check_requested = pyqtSignal()
    update_requested = pyqtSignal()

    def __init__(self, current_version: str, parent: Optional[QWidget] = None) -> None:
        super().__init__("Updates", "Keep OvenProxy up to date", parent)

        card = Card()

        self._current = QLabel(f"Current version:  v{current_version}")
        self._current.setObjectName("SectionTitle")
        card.body().addWidget(self._current)

        self._latest = QLabel("Latest version:  —")
        self._latest.setObjectName("StatCaption")
        card.body().addWidget(self._latest)

        self._status = QLabel("Click “Check for Updates” to look for a new release.")
        self._status.setWordWrap(True)
        card.body().addWidget(self._status)

        buttons = QHBoxLayout()
        self._check_btn = QPushButton("  Check for Updates")
        self._check_btn.setIcon(make_icon("refresh", COLORS["text_muted"]))
        self._check_btn.clicked.connect(self.check_requested.emit)
        buttons.addWidget(self._check_btn)

        self._update_btn = QPushButton("  Update Now")
        self._update_btn.setObjectName("Primary")
        self._update_btn.setIcon(make_icon("import", "#06222f"))
        self._update_btn.clicked.connect(self.update_requested.emit)
        self._update_btn.setVisible(False)
        buttons.addWidget(self._update_btn)
        buttons.addStretch(1)
        card.body().addLayout(buttons)

        self.content().addWidget(card)
        self.content().addStretch(1)

    # ------------------------------------------------------------------ states
    def set_checking(self) -> None:
        self._check_btn.setEnabled(False)
        self._update_btn.setVisible(False)
        self._status.setText("Checking for updates...")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']};")

    def set_up_to_date(self, current: str) -> None:
        self._check_btn.setEnabled(True)
        self._update_btn.setVisible(False)
        self._latest.setText(f"Latest version:  v{current}")
        self._status.setText("✓ You are running the latest version.")
        self._status.setStyleSheet(f"color: {COLORS['success']};")

    def set_available(self, current: str, latest: str) -> None:
        self._check_btn.setEnabled(True)
        self._update_btn.setVisible(True)
        self._update_btn.setEnabled(True)
        self._latest.setText(f"Latest version:  v{latest}")
        self._status.setText(f"A new version (v{latest}) is available. Click “Update Now”.")
        self._status.setStyleSheet(f"color: {COLORS['accent']};")

    def set_error(self, message: str) -> None:
        self._check_btn.setEnabled(True)
        self._status.setText(f"⚠ {message}")
        self._status.setStyleSheet(f"color: {COLORS['warning']};")

    def set_updating(self) -> None:
        self._update_btn.setEnabled(False)
        self._check_btn.setEnabled(False)
        self._status.setText("Downloading update... this may take a moment.")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']};")

    def set_finished(self, success: bool, message: str) -> None:
        self._check_btn.setEnabled(True)
        self._update_btn.setEnabled(True)
        self._status.setText(("✓ " if success else "⚠ ") + message)
        self._status.setStyleSheet(
            f"color: {COLORS['success'] if success else COLORS['error']};"
        )
