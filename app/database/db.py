"""Thread-safe SQLite persistence for proxies, sources and settings."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from app.models.proxy import Proxy
from app.models.source import ProxySource


class Database:
    """A small JSON-in-SQLite store guarded by a single lock.

    Values are stored as JSON blobs which keeps the schema stable while the
    dataclasses evolve. A reentrant-free lock serialises access because the
    connection is shared across worker threads (``check_same_thread=False``).
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS proxies (
                    address TEXT PRIMARY KEY,
                    data    TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sources (
                    name TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            self._conn.commit()

    # ------------------------------------------------------------------ proxies
    def upsert_proxy(self, proxy: Proxy) -> None:
        self.upsert_many([proxy])

    def upsert_many(self, proxies: list[Proxy]) -> None:
        if not proxies:
            return
        with self._lock:
            self._conn.executemany(
                "INSERT INTO proxies(address, data) VALUES(?, ?) "
                "ON CONFLICT(address) DO UPDATE SET data=excluded.data",
                [(p.address, json.dumps(p.to_dict())) for p in proxies],
            )
            self._conn.commit()

    def get_proxies(self) -> list[Proxy]:
        with self._lock:
            rows = self._conn.execute("SELECT data FROM proxies").fetchall()
        return [Proxy.from_dict(json.loads(row["data"])) for row in rows]

    def delete_proxy(self, address: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM proxies WHERE address=?", (address,))
            self._conn.commit()

    def clear_proxies(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM proxies")
            self._conn.commit()

    # ------------------------------------------------------------------ sources
    def save_source(self, source: ProxySource) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO sources(name, data) VALUES(?, ?) "
                "ON CONFLICT(name) DO UPDATE SET data=excluded.data",
                (source.name, json.dumps(source.to_dict())),
            )
            self._conn.commit()

    def get_sources(self) -> list[ProxySource]:
        with self._lock:
            rows = self._conn.execute("SELECT data FROM sources").fetchall()
        return [ProxySource.from_dict(json.loads(row["data"])) for row in rows]

    def delete_source(self, name: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM sources WHERE name=?", (name,))
            self._conn.commit()

    # ----------------------------------------------------------------- settings
    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            self._conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM settings WHERE key=?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def close(self) -> None:
        with self._lock:
            self._conn.close()
