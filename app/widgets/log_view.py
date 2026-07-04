"""A colour-coded log console with clear/export controls."""

from __future__ import annotations

from html import escape
from typing import Optional

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.resources.icons import make_icon
from app.ui.theme import COLORS, LEVEL_COLORS


class LogView(QWidget):
    """Read-only console that renders records with per-level colours."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._console = QPlainTextEdit()
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(5000)
        self._console.setFont(QFont("Consolas", 10))
        layout.addWidget(self._console, 1)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self._clear_btn = QPushButton("  Clear")
        self._clear_btn.setIcon(make_icon("trash", COLORS["text_muted"]))
        self._clear_btn.clicked.connect(self._console.clear)
        controls.addWidget(self._clear_btn)

        self._export_btn = QPushButton("  Export")
        self._export_btn.setIcon(make_icon("export", COLORS["text_muted"]))
        self._export_btn.clicked.connect(self._export)
        controls.addWidget(self._export_btn)
        layout.addLayout(controls)

    def append(self, level: str, message: str, timestamp: str) -> None:
        color = LEVEL_COLORS.get(level, COLORS["text"])
        safe = escape(message)
        html = (
            f'<span style="color:{COLORS["text_muted"]}">{timestamp}</span> '
            f'<span style="color:{color}; font-weight:600">[{level}]</span> '
            f'<span style="color:{COLORS["text"]}">{safe}</span>'
        )
        self._console.appendHtml(html)

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export logs", "ovenproxy-logs.txt", "Text files (*.txt)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self._console.toPlainText())
