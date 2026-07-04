"""Left navigation rail."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.resources.icons import make_icon
from app.ui.theme import COLORS


class Sidebar(QWidget):
    """Exclusive, icon-labelled navigation buttons."""

    navigate = pyqtSignal(int)

    ITEMS: list[tuple[str, str]] = [
        ("Dashboard", "dashboard"),
        ("Scraper", "scraper"),
        ("Checker", "checker"),
        ("Working Proxies", "proxies"),
        ("Traffic Monitor", "traffic"),
        ("Local Gateway", "gateway"),
        ("Updates", "refresh"),
        ("Settings", "settings"),
        ("Logs", "logs"),
        ("Documentation", "book"),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(224)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 18)
        layout.setSpacing(6)

        title = QLabel("OvenProxy")
        title.setObjectName("AppTitle")
        layout.addWidget(title)
        subtitle = QLabel("Proxy Toolkit")
        subtitle.setObjectName("AppSubtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for index, (label, icon) in enumerate(self.ITEMS):
            button = QPushButton(f"  {label}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setIcon(make_icon(icon, COLORS["text_muted"]))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, i=index: self.navigate.emit(i))
            self._group.addButton(button, index)
            layout.addWidget(button)

        layout.addStretch(1)
        self._status = QLabel("●  Gateway offline")
        self._status.setObjectName("StatusLabel")
        layout.addWidget(self._status)

        first = self._group.button(0)
        if first is not None:
            first.setChecked(True)

    def set_active(self, index: int) -> None:
        button = self._group.button(index)
        if button is not None:
            button.setChecked(True)

    def set_gateway_status(self, running: bool) -> None:
        if running:
            self._status.setText("●  Gateway online")
            self._status.setStyleSheet(f"color: {COLORS['success']}; padding: 6px 4px;")
        else:
            self._status.setText("●  Gateway offline")
            self._status.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 6px 4px;")
