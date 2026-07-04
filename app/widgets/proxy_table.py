"""Qt model/view classes for displaying working proxies."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PyQt6.QtGui import QColor

from app.models.proxy import AnonymityLevel, Proxy, ProxyStatus
from app.ui.theme import COLORS

_HEADERS = ["IP", "Port", "Country", "Ping (ms)", "Anonymity", "Protocol", "Status", "Last Checked"]


def _sort_value(proxy: Proxy, column: int) -> Any:
    """Return a natively-comparable value for a proxy in the given column."""
    if column == 0:
        return tuple(int(octet) for octet in proxy.ip.split("."))
    if column == 1:
        return proxy.port
    if column == 2:
        return proxy.country
    if column == 3:
        return proxy.latency_ms if proxy.latency_ms is not None else float("inf")
    if column == 4:
        return proxy.anonymity.value
    if column == 5:
        return proxy.protocol.value
    if column == 6:
        return proxy.status.value
    if column == 7:
        return proxy.last_checked or datetime.min
    return ""


class ProxyTableModel(QAbstractTableModel):
    """A table model backed by a list of :class:`Proxy` objects."""

    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._proxies: list[Proxy] = []

    # ------------------------------------------------------------- Qt overrides
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._proxies)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(_HEADERS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return _HEADERS[section]
        return section + 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        proxy = self._proxies[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self._display(proxy, column)
        if role == Qt.ItemDataRole.ForegroundRole:
            if column == 6:  # Status
                return QColor(COLORS["success"] if proxy.status == ProxyStatus.ALIVE else COLORS["error"])
            if column == 3 and proxy.latency_ms is not None:  # Ping
                return QColor(self._ping_color(proxy.latency_ms))
        if role == Qt.ItemDataRole.TextAlignmentRole and column in (1, 3):
            return int(Qt.AlignmentFlag.AlignCenter)
        if role == Qt.ItemDataRole.UserRole:
            return proxy
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        reverse = order == Qt.SortOrder.DescendingOrder
        keys = {
            0: lambda p: tuple(int(o) for o in p.ip.split(".")),
            1: lambda p: p.port,
            2: lambda p: p.country,
            3: lambda p: p.latency_ms if p.latency_ms is not None else float("inf"),
            4: lambda p: p.anonymity.value,
            5: lambda p: p.protocol.value,
            6: lambda p: p.status.value,
            7: lambda p: p.last_checked or 0,
        }
        key = keys.get(column)
        if key is None:
            return
        self.layoutAboutToBeChanged.emit()
        self._proxies.sort(key=key, reverse=reverse)
        self.layoutChanged.emit()

    # --------------------------------------------------------------- public API
    def set_proxies(self, proxies: list[Proxy]) -> None:
        self.beginResetModel()
        self._proxies = list(proxies)
        self.endResetModel()

    def add_proxy(self, proxy: Proxy) -> None:
        row = len(self._proxies)
        self.beginInsertRows(QModelIndex(), row, row)
        self._proxies.append(proxy)
        self.endInsertRows()

    def remove_rows(self, rows: list[int]) -> None:
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(self._proxies):
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._proxies[row]
                self.endRemoveRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._proxies.clear()
        self.endResetModel()

    def proxy_at(self, row: int) -> Optional[Proxy]:
        if 0 <= row < len(self._proxies):
            return self._proxies[row]
        return None

    def all_proxies(self) -> list[Proxy]:
        return list(self._proxies)

    def countries(self) -> list[str]:
        return sorted({p.country for p in self._proxies if p.country})

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _display(proxy: Proxy, column: int) -> str:
        if column == 0:
            return proxy.ip
        if column == 1:
            return str(proxy.port)
        if column == 2:
            return f"{proxy.country_code}  {proxy.country}".strip()
        if column == 3:
            return f"{proxy.latency_ms:.0f}" if proxy.latency_ms is not None else "—"
        if column == 4:
            return proxy.anonymity.value
        if column == 5:
            return proxy.protocol.value.upper()
        if column == 6:
            return proxy.status.value
        if column == 7:
            return proxy.last_checked.strftime("%H:%M:%S") if proxy.last_checked else "—"
        return ""

    @staticmethod
    def _ping_color(latency_ms: float) -> str:
        if latency_ms < 500:
            return COLORS["success"]
        if latency_ms < 1500:
            return COLORS["warning"]
        return COLORS["error"]


class ProxyFilterProxy(QSortFilterProxyModel):
    """Filters by a free-text query (IP/country) and an exact country."""

    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self._text = ""
        self._country = ""
        self.setSortRole(Qt.ItemDataRole.DisplayRole)

    def set_text_filter(self, text: str) -> None:
        self._text = text.strip().lower()
        self.invalidateFilter()

    def set_country_filter(self, country: str) -> None:
        self._country = "" if country in ("", "All countries") else country
        self.invalidateFilter()

    def filterAcceptsRow(  # noqa: N802
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        model = self.sourceModel()
        if not isinstance(model, ProxyTableModel):
            return True
        proxy = model.proxy_at(source_row)
        if proxy is None:
            return False
        if self._country and proxy.country != self._country:
            return False
        if self._text:
            haystack = f"{proxy.ip} {proxy.country} {proxy.country_code}".lower()
            if self._text not in haystack:
                return False
        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        model = self.sourceModel()
        if not isinstance(model, ProxyTableModel):
            return super().lessThan(left, right)
        left_proxy = model.proxy_at(left.row())
        right_proxy = model.proxy_at(right.row())
        if left_proxy is None or right_proxy is None:
            return super().lessThan(left, right)
        return _sort_value(left_proxy, left.column()) < _sort_value(right_proxy, right.column())
