"""Shared base class giving every page a consistent header."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BasePage(QWidget):
    """A page with a title/subtitle header and a content layout."""

    def __init__(self, title: str, subtitle: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(26, 22, 26, 22)
        self._root.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        header.addWidget(title_label)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        header.addWidget(subtitle_label)
        self._root.addLayout(header)

    def content(self) -> QVBoxLayout:
        return self._root
