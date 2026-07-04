"""Rounded card containers and statistic tiles."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.resources.icons import make_icon
from app.ui.theme import COLORS


class Card(QFrame):
    """A simple rounded surface with a vertical layout."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(10)

    def body(self) -> QVBoxLayout:
        return self._layout


class StatCard(QFrame):
    """A KPI tile: icon, title and a large value."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        icon: str = "dashboard",
        accent: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        accent = accent or COLORS["accent"]

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        icon_label = QLabel()
        icon_label.setPixmap(make_icon(icon, accent, 18).pixmap(18, 18))
        header.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        header.addWidget(title_label)
        header.addStretch(1)
        root.addLayout(header)

        self._value = QLabel(value)
        self._value.setObjectName("StatValue")
        root.addWidget(self._value)

        self._caption = QLabel("")
        self._caption.setObjectName("StatCaption")
        root.addWidget(self._caption)

        self.setMinimumWidth(170)

    def set_value(self, value: str) -> None:
        self._value.setText(value)

    def set_caption(self, caption: str) -> None:
        self._caption.setText(caption)

    def set_value_color(self, color: str) -> None:
        self._value.setStyleSheet(f"color: {color};")
        align = Qt.AlignmentFlag.AlignLeft  # keep layout stable
        self._value.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
