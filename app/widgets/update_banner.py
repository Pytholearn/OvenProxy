"""A dismissible banner shown when a new version is available."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from app.resources.icons import make_icon
from app.ui.theme import COLORS


class UpdateBanner(QFrame):
    """Top-of-window notice with 'Update now' and 'Later' actions."""

    update_clicked = pyqtSignal()
    dismissed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("UpdateBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 14, 8)
        layout.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(make_icon("refresh", COLORS["accent"], 18).pixmap(18, 18))
        layout.addWidget(icon)

        self._label = QLabel("A new version is available.")
        self._label.setObjectName("BannerText")
        layout.addWidget(self._label)
        layout.addStretch(1)

        update_btn = QPushButton("Update now")
        update_btn.setObjectName("Primary")
        update_btn.clicked.connect(self.update_clicked.emit)
        layout.addWidget(update_btn)

        later_btn = QPushButton("Later")
        later_btn.clicked.connect(self._on_later)
        layout.addWidget(later_btn)

        self.hide()

    def show_update(self, latest: str) -> None:
        self._label.setText(f"OvenProxy {latest} is available — you're on an older version.")
        self.show()

    def _on_later(self) -> None:
        self.hide()
        self.dismissed.emit()
