"""Concurrent proxy scraper that downloads and parses many lists at once."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

import requests

from app.models.proxy import Proxy
from app.models.source import ProxySource
from app.utils.logger import LOGGER_NAME
from app.utils.network import parse_proxy_line

OnSource = Callable[[str, int], None]

_HEADERS = {"User-Agent": "OvenProxy/1.0 (+https://github.com/Pytholearn/OvenProxy)"}


class ProxyScraper:
    """Downloads proxy lists from multiple sources using a thread pool."""

    def __init__(self, timeout: float = 15.0, logger: Optional[logging.Logger] = None) -> None:
        self._timeout = timeout
        self._log = logger or logging.getLogger(LOGGER_NAME)
        self._stop = False

    def stop(self) -> None:
        """Request cancellation; in-flight downloads will be ignored."""
        self._stop = True

    def _fetch(self, source: ProxySource) -> set[Proxy]:
        result: set[Proxy] = set()
        if self._stop:
            return result
        try:
            response = requests.get(source.url, timeout=self._timeout, headers=_HEADERS)
            response.raise_for_status()
        except requests.RequestException as exc:
            self._log.warning("Source '%s' failed: %s", source.name, exc)
            return result
        for line in response.text.splitlines():
            parsed = parse_proxy_line(line)
            if parsed:
                ip, port = parsed
                result.add(Proxy(ip=ip, port=port, protocol=source.protocol))
        self._log.info("Source '%s' -> %d proxies", source.name, len(result))
        return result

    def scrape(
        self,
        sources: list[ProxySource],
        max_workers: int = 12,
        on_source: Optional[OnSource] = None,
    ) -> list[Proxy]:
        """Return the de-duplicated union of proxies from all enabled *sources*."""
        self._stop = False
        enabled = [s for s in sources if s.enabled]
        if not enabled:
            return []

        collected: set[Proxy] = set()
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(self._fetch, src): src for src in enabled}
            for future in as_completed(futures):
                source = futures[future]
                proxies = future.result()
                collected.update(proxies)
                if on_source is not None:
                    on_source(source.name, len(proxies))
                if self._stop:
                    break
        return list(collected)
