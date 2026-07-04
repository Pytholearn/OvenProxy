"""Scraper page: manage sources, choose protocols and launch scraping."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from app.config import AppConfig
from app.database.db import Database
from app.models.proxy import Protocol
from app.models.source import ProxySource
from app.resources.icons import make_icon
from app.services.scraper_worker import ScraperWorker
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.widgets.cards import Card

_PROTOCOLS: list[tuple[Protocol, str]] = [
    (Protocol.SOCKS5, "SOCKS5"),
    (Protocol.SOCKS4, "SOCKS4"),
    (Protocol.HTTP, "HTTP"),
]


class ScraperPage(BasePage):
    """Lets the user toggle sources, pick protocols and scrape off-thread."""

    scraped = pyqtSignal(object)    # list[Proxy]
    message = pyqtSignal(str, str)  # level, text

    def __init__(self, db: Database, config: AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__("Scraper", "Download SOCKS5 / SOCKS4 / HTTP proxies from many providers", parent)
        self._db = db
        self._config = config
        self._worker: Optional[ScraperWorker] = None

        body = QHBoxLayout()
        body.setSpacing(16)

        # ---- left: sources ----
        sources_card = Card()
        sources_card.setFixedWidth(330)
        header = QLabel("Sources")
        header.setObjectName("SectionTitle")
        sources_card.body().addWidget(header)

        self._sources = QListWidget()
        self._sources.itemChanged.connect(self._on_item_changed)
        sources_card.body().addWidget(self._sources, 1)

        source_buttons = QHBoxLayout()
        add_btn = QPushButton("  Add")
        add_btn.setIcon(make_icon("plus", COLORS["text_muted"]))
        add_btn.clicked.connect(self._add_source)
        import_btn = QPushButton("  Import URLs")
        import_btn.setIcon(make_icon("import", COLORS["text_muted"]))
        import_btn.clicked.connect(self._import_urls)
        remove_btn = QPushButton("  Remove")
        remove_btn.setIcon(make_icon("trash", COLORS["text_muted"]))
        remove_btn.clicked.connect(self._remove_source)
        for button in (add_btn, import_btn, remove_btn):
            source_buttons.addWidget(button)
        sources_card.body().addLayout(source_buttons)
        body.addWidget(sources_card)

        # ---- right: controls + protocol filter + output ----
        right = Card()
        controls = QHBoxLayout()
        self._start_btn = QPushButton("  Start Scraping")
        self._start_btn.setObjectName("Primary")
        self._start_btn.setIcon(make_icon("play", "#06222f"))
        self._start_btn.clicked.connect(self._start)
        self._stop_btn = QPushButton("  Stop")
        self._stop_btn.setObjectName("Danger")
        self._stop_btn.setIcon(make_icon("stop", COLORS["error"]))
        self._stop_btn.clicked.connect(self._stop)
        self._stop_btn.setEnabled(False)
        controls.addWidget(self._start_btn)
        controls.addWidget(self._stop_btn)
        controls.addStretch(1)
        self._count = QLabel("0 proxies")
        self._count.setObjectName("SectionTitle")
        controls.addWidget(self._count)
        right.body().addLayout(controls)

        protocols = QHBoxLayout()
        protocols.setSpacing(16)
        proto_label = QLabel("Scrape:")
        proto_label.setObjectName("CardTitle")
        protocols.addWidget(proto_label)
        self._proto_checks: dict[Protocol, QCheckBox] = {}
        for protocol, label in _PROTOCOLS:
            check = QCheckBox(label)
            check.setChecked(True)
            self._proto_checks[protocol] = check
            protocols.addWidget(check)
        protocols.addStretch(1)
        right.body().addLayout(protocols)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        right.body().addWidget(self._output, 1)
        body.addWidget(right, 1)

        self.content().addLayout(body, 1)
        self._reload_sources()

    # --------------------------------------------------------------- sources io
    def _reload_sources(self) -> None:
        self._sources.blockSignals(True)
        self._sources.clear()
        for source in self._db.get_sources():
            self._add_item(source)
        self._sources.blockSignals(False)

    def _add_item(self, source: ProxySource) -> None:
        item = QListWidgetItem(source.name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if source.enabled else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, source)
        item.setToolTip(f"{source.protocol.value.upper()}  ·  {source.url}")
        self._sources.addItem(item)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        source: ProxySource = item.data(Qt.ItemDataRole.UserRole)
        source.enabled = item.checkState() == Qt.CheckState.Checked
        self._db.save_source(source)

    def _add_source(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Source", "Source name:")
        if not ok or not name.strip():
            return
        url, ok = QInputDialog.getText(self, "Add Source", "List URL:")
        if not ok or not url.strip():
            return
        protocol, ok = QInputDialog.getItem(
            self, "Add Source", "Protocol:", ["socks5", "socks4", "http"], 0, False
        )
        if not ok:
            return
        source = ProxySource(name.strip(), url.strip(), True, Protocol(protocol), custom=True)
        self._db.save_source(source)
        self._reload_sources()
        self.message.emit("INFO", f"Added source '{source.name}'.")

    def _import_urls(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self, "Import URLs", "One proxy-list URL per line:"
        )
        if not ok:
            return
        added = 0
        for index, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            source = ProxySource(f"Imported {index}", line, True, Protocol.SOCKS5, custom=True)
            self._db.save_source(source)
            added += 1
        if added:
            self._reload_sources()
            self.message.emit("INFO", f"Imported {added} source(s).")

    def _remove_source(self) -> None:
        item = self._sources.currentItem()
        if item is None:
            return
        source: ProxySource = item.data(Qt.ItemDataRole.UserRole)
        self._db.delete_source(source.name)
        self._reload_sources()
        self.message.emit("INFO", f"Removed source '{source.name}'.")

    def _selected_protocols(self) -> set[Protocol]:
        return {proto for proto, check in self._proto_checks.items() if check.isChecked()}

    def _enabled_sources(self) -> list[ProxySource]:
        protocols = self._selected_protocols()
        result: list[ProxySource] = []
        for row in range(self._sources.count()):
            item = self._sources.item(row)
            source: ProxySource = item.data(Qt.ItemDataRole.UserRole)
            source.enabled = item.checkState() == Qt.CheckState.Checked
            if source.enabled and source.protocol in protocols:
                result.append(source)
        return result

    # ------------------------------------------------------------------ scraping
    def _start(self) -> None:
        if not self._selected_protocols():
            self.message.emit("WARNING", "Select at least one protocol to scrape.")
            return
        sources = self._enabled_sources()
        if not sources:
            self.message.emit("WARNING", "No sources match the selected protocols.")
            return
        self._output.clear()
        self._count.setText("0 proxies")
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

        self._worker = ScraperWorker(sources, self._config)
        self._worker.source_done.connect(self._on_source_done)
        self._worker.message.connect(self.message.emit)
        self._worker.finished_scraping.connect(self._on_finished)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self.message.emit("WARNING", "Stopping scrape...")

    def _on_source_done(self, name: str, count: int) -> None:
        self._output.appendPlainText(f"✓ {name:<26} {count} proxies")

    def _on_finished(self, proxies: list) -> None:
        self._count.setText(f"{len(proxies)} proxies")
        self._output.appendPlainText(f"\nFinished — {len(proxies)} unique proxies collected.")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.scraped.emit(proxies)
