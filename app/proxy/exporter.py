"""Export and import working proxies in txt / csv / json formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from app.models.proxy import Protocol, Proxy
from app.utils.network import parse_proxy_line


class ProxyExporter:
    """Writes a list of proxies to disk in the requested format."""

    @staticmethod
    def export(proxies: list[Proxy], path: str | Path, fmt: str = "txt") -> None:
        fmt = fmt.lower()
        if fmt == "json":
            ProxyExporter._json(proxies, path)
        elif fmt == "csv":
            ProxyExporter._csv(proxies, path)
        else:
            ProxyExporter._txt(proxies, path)

    @staticmethod
    def _txt(proxies: list[Proxy], path: str | Path) -> None:
        Path(path).write_text("\n".join(p.address for p in proxies), encoding="utf-8")

    @staticmethod
    def _json(proxies: list[Proxy], path: str | Path) -> None:
        payload = [p.to_dict() for p in proxies]
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _csv(proxies: list[Proxy], path: str | Path) -> None:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["IP", "Port", "Protocol", "Country", "Ping(ms)",
                 "Anonymity", "Status", "ExitIP", "LastChecked"]
            )
            for proxy in proxies:
                writer.writerow([
                    proxy.ip,
                    proxy.port,
                    proxy.protocol.value,
                    proxy.country,
                    proxy.latency_ms if proxy.latency_ms is not None else "",
                    proxy.anonymity.value,
                    proxy.status.value,
                    proxy.exit_ip,
                    proxy.last_checked.isoformat() if proxy.last_checked else "",
                ])


class ProxyImporter:
    """Reads proxies from a txt / json file, de-duplicating by address."""

    @staticmethod
    def import_file(path: str | Path) -> list[Proxy]:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        stripped = text.strip()

        if stripped.startswith(("[", "{")):
            proxies = ProxyImporter._from_json(stripped)
            if proxies:
                return proxies

        seen: set[str] = set()
        result: list[Proxy] = []
        for line in text.splitlines():
            parsed = parse_proxy_line(line)
            if not parsed:
                continue
            ip, port = parsed
            address = f"{ip}:{port}"
            if address not in seen:
                seen.add(address)
                result.append(Proxy(ip=ip, port=port, protocol=Protocol.SOCKS5))
        return result

    @staticmethod
    def _from_json(stripped: str) -> list[Proxy]:
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return []
        items = data if isinstance(data, list) else [data]
        seen: set[str] = set()
        result: list[Proxy] = []
        for item in items:
            if not isinstance(item, dict) or "ip" not in item:
                continue
            try:
                proxy = Proxy.from_dict(item)
            except (KeyError, ValueError):
                continue
            if proxy.address not in seen:
                seen.add(proxy.address)
                result.append(proxy)
        return result
