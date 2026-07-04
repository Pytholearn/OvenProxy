"""Working-proxies page: searchable, sortable table with export/import."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableView,
    QWidget,
)
from PyQt6.QtGui import QGuiApplication

from app.database.db import Database
from app.models.proxy import Proxy
from app.proxy.exporter import ProxyExporter, ProxyImporter
from app.resources.icons import make_icon
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.widgets.cards import Card
from app.widgets.proxy_table import ProxyFilterProxy, ProxyTableModel


class ProxiesPage(BasePage):
    """CRUD + export/import surface for validated proxies."""

    use_in_gateway = pyqtSignal(object)  # Proxy
    count_changed = pyqtSignal(int)
    message = pyqtSignal(str, str)

    def __init__(self, db: Database, parent: Optional[QWidget] = None) -> None:
        super().__init__("Working Proxies", "Validated, ready-to-use SOCKS5 proxies", parent)
        self._db = db
        self._model = ProxyTableModel(self)
        self._filter = ProxyFilterProxy(self)
        self._filter.setSourceModel(self._model)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search IP or country...")
        self._search.textChanged.connect(self._filter.set_text_filter)
        self._search.setFixedWidth(240)
        toolbar.addWidget(self._search)

        self._country = QComboBox()
        self._country.addItem("All countries")
        self._country.currentTextChanged.connect(self._filter.set_country_filter)
        self._country.setFixedWidth(180)
        toolbar.addWidget(self._country)

        sort_ping_btn = QPushButton("  Sort by Ping")
        sort_ping_btn.setIcon(make_icon("traffic", COLORS["text_muted"]))
        sort_ping_btn.setToolTip("Fastest proxies first")
        sort_ping_btn.clicked.connect(self._sort_by_ping)
        toolbar.addWidget(sort_ping_btn)
        toolbar.addStretch(1)

        export_btn = QPushButton("  Export")
        export_btn.setIcon(make_icon("export", COLORS["text_muted"]))
        export_btn.setMenu(self._build_export_menu())
        toolbar.addWidget(export_btn)

        import_btn = QPushButton("  Import")
        import_btn.setIcon(make_icon("import", COLORS["text_muted"]))
        import_btn.clicked.connect(self._import)
        toolbar.addWidget(import_btn)

        copy_btn = QPushButton("  Copy")
        copy_btn.setIcon(make_icon("copy", COLORS["text_muted"]))
        copy_btn.clicked.connect(self._copy_selected)
        toolbar.addWidget(copy_btn)

        delete_btn = QPushButton("  Delete")
        delete_btn.setIcon(make_icon("trash", COLORS["text_muted"]))
        delete_btn.clicked.connect(self._delete_selected)
        toolbar.addWidget(delete_btn)

        gateway_btn = QPushButton("  Use in Gateway")
        gateway_btn.setObjectName("Primary")
        gateway_btn.setIcon(make_icon("gateway", "#06222f"))
        gateway_btn.clicked.connect(self._use_in_gateway)
        toolbar.addWidget(gateway_btn)
        self.content().addLayout(toolbar)

        card = Card()
        self._table = QTableView()
        self._table.setModel(self._filter)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        card.body().addWidget(self._table)
        self.content().addWidget(card, 1)

        self._load_from_db()

    # ------------------------------------------------------------------- public
    def add_proxy(self, proxy: Proxy) -> None:
        self._model.add_proxy(proxy)
        self._db.upsert_proxy(proxy)
        self._refresh_countries()
        self.count_changed.emit(self._model.rowCount())

    def proxies(self) -> list[Proxy]:
        return self._model.all_proxies()

    # ------------------------------------------------------------------ private
    def _load_from_db(self) -> None:
        self._model.set_proxies(self._db.get_proxies())
        self._refresh_countries()
        self.count_changed.emit(self._model.rowCount())

    def _refresh_countries(self) -> None:
        current = self._country.currentText()
        self._country.blockSignals(True)
        self._country.clear()
        self._country.addItem("All countries")
        self._country.addItems(self._model.countries())
        index = self._country.findText(current)
        self._country.setCurrentIndex(index if index >= 0 else 0)
        self._country.blockSignals(False)

    def _selected_proxies(self) -> list[Proxy]:
        rows = {idx.row() for idx in self._table.selectionModel().selectedRows()}
        result: list[Proxy] = []
        for proxy_row in rows:
            source_index = self._filter.mapToSource(self._filter.index(proxy_row, 0))
            proxy = self._model.proxy_at(source_index.row())
            if proxy is not None:
                result.append(proxy)
        return result

    def _build_export_menu(self) -> QMenu:
        menu = QMenu(self)
        for label, fmt in (("Export as TXT", "txt"), ("Export as CSV", "csv"), ("Export as JSON", "json")):
            menu.addAction(label, lambda f=fmt: self._export(f))
        return menu

    def _export(self, fmt: str) -> None:
        proxies = self._model.all_proxies()
        if not proxies:
            self.message.emit("WARNING", "Nothing to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export proxies", f"working-proxies.{fmt}", f"{fmt.upper()} files (*.{fmt})"
        )
        if not path:
            return
        ProxyExporter.export(proxies, path, fmt)
        self.message.emit("SUCCESS", f"Exported {len(proxies)} proxies to {Path(path).name}.")

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import proxies", "", "Proxy files (*.txt *.json *.csv);;All files (*)"
        )
        if not path:
            return
        imported = ProxyImporter.import_file(path)
        for proxy in imported:
            self._model.add_proxy(proxy)
        self._db.upsert_many(imported)
        self._refresh_countries()
        self.count_changed.emit(self._model.rowCount())
        self.message.emit("INFO", f"Imported {len(imported)} proxies.")

    def _copy_selected(self) -> None:
        proxies = self._selected_proxies() or self._model.all_proxies()
        if not proxies:
            return
        QGuiApplication.clipboard().setText("\n".join(p.address for p in proxies))
        self.message.emit("INFO", f"Copied {len(proxies)} proxies to clipboard.")

    def _delete_selected(self) -> None:
        proxies = self._selected_proxies()
        if not proxies:
            return
        remaining = [p for p in self._model.all_proxies() if p not in proxies]
        for proxy in proxies:
            self._db.delete_proxy(proxy.address)
        self._model.set_proxies(remaining)
        self._refresh_countries()
        self.count_changed.emit(self._model.rowCount())
        self.message.emit("INFO", f"Deleted {len(proxies)} proxies.")

    def _use_in_gateway(self) -> None:
        proxies = self._selected_proxies()
        if not proxies:
            self.message.emit("WARNING", "Select a proxy first.")
            return
        self.use_in_gateway.emit(proxies[0])

    def _sort_by_ping(self) -> None:
        self._table.sortByColumn(3, Qt.SortOrder.AscendingOrder)
