"""A local SOCKS5 server that chains every connection to one upstream proxy.

The local listener always speaks SOCKS5 (no-auth, CONNECT). The *upstream* proxy
it forwards through can be SOCKS5, SOCKS4/4a or an HTTP CONNECT proxy, so any
working proxy from the checker can be used as a gateway.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import struct
from dataclasses import dataclass

from app.models.proxy import Protocol
from app.utils.logger import LOGGER_NAME

_SOCKS_VERSION = 0x05
_CMD_CONNECT = 0x01
_ATYP_IPV4 = 0x01
_ATYP_DOMAIN = 0x03
_ATYP_IPV6 = 0x04
_REP_SUCCESS = b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00"
_REP_HOST_UNREACHABLE = b"\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00"
_REP_GENERAL_FAILURE = b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00"
_REP_CMD_UNSUPPORTED = b"\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00"
_REP_ATYP_UNSUPPORTED = b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00"
_CHUNK = 65536


@dataclass
class TrafficCounters:
    """Cumulative byte/connection counters shared with the GUI thread.

    Integers are read from the GUI thread for display only; thanks to the GIL
    each read is atomic, so no lock is required for monotonic counters.
    """

    upload: int = 0
    download: int = 0
    active: int = 0
    total_connections: int = 0


class Socks5Forwarder:
    """A no-auth SOCKS5 CONNECT server forwarding to a single upstream proxy."""

    def __init__(
        self,
        local_host: str,
        local_port: int,
        upstream_host: str,
        upstream_port: int,
        timeout: float = 15.0,
        logger: logging.Logger | None = None,
        upstream_protocol: Protocol = Protocol.SOCKS5,
    ) -> None:
        self.local_host = local_host
        self.local_port = local_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.upstream_protocol = upstream_protocol
        self.timeout = timeout
        self.counters = TrafficCounters()
        self._log = logger or logging.getLogger(LOGGER_NAME)
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client, self.local_host, self.local_port
        )
        self._log.info(
            "Gateway listening on %s:%d -> %s %s:%d",
            self.local_host, self.local_port, self.upstream_protocol.value,
            self.upstream_host, self.upstream_port,
        )

    async def serve_forever(self) -> None:
        assert self._server is not None
        async with self._server:
            await self._server.serve_forever()

    def close(self) -> None:
        if self._server is not None:
            self._server.close()

    # ------------------------------------------------------------------ client
    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.counters.active += 1
        self.counters.total_connections += 1
        upstream_writer: asyncio.StreamWriter | None = None
        try:
            if not await self._client_handshake(reader, writer):
                return
            target = await self._read_request(reader, writer)
            if target is None:
                return
            host, port = target
            try:
                up_reader, up_writer = await asyncio.wait_for(
                    self._connect_upstream(host, port), timeout=self.timeout
                )
                upstream_writer = up_writer
            except (asyncio.TimeoutError, OSError, ConnectionError) as exc:
                self._log.debug("Upstream failed for %s:%d (%s)", host, port, exc)
                await self._reply(writer, _REP_HOST_UNREACHABLE)
                return

            await self._reply(writer, _REP_SUCCESS)
            await asyncio.gather(
                self._pipe(reader, up_writer, upload=True),
                self._pipe(up_reader, writer, upload=False),
            )
        except (asyncio.IncompleteReadError, ConnectionError, OSError):
            pass
        finally:
            self.counters.active = max(0, self.counters.active - 1)
            self._safe_close(writer)
            if upstream_writer is not None:
                self._safe_close(upstream_writer)

    async def _client_handshake(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> bool:
        header = await reader.readexactly(2)
        if header[0] != _SOCKS_VERSION:
            return False
        n_methods = header[1]
        await reader.readexactly(n_methods)
        writer.write(b"\x05\x00")  # choose "no authentication"
        await writer.drain()
        return True

    async def _read_request(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> tuple[str, int] | None:
        header = await reader.readexactly(4)
        version, command, _, address_type = header
        if version != _SOCKS_VERSION or command != _CMD_CONNECT:
            await self._reply(writer, _REP_CMD_UNSUPPORTED)
            return None
        if address_type == _ATYP_IPV4:
            host = socket.inet_ntoa(await reader.readexactly(4))
        elif address_type == _ATYP_DOMAIN:
            length = (await reader.readexactly(1))[0]
            host = (await reader.readexactly(length)).decode("idna", errors="ignore")
        elif address_type == _ATYP_IPV6:
            host = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
        else:
            await self._reply(writer, _REP_ATYP_UNSUPPORTED)
            return None
        port = struct.unpack("!H", await reader.readexactly(2))[0]
        return host, port

    # ---------------------------------------------------------------- upstream
    async def _connect_upstream(
        self, host: str, port: int
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if self.upstream_protocol == Protocol.SOCKS4:
            return await self._connect_socks4(host, port)
        if self.upstream_protocol == Protocol.HTTP:
            return await self._connect_http(host, port)
        return await self._connect_socks5(host, port)

    async def _connect_socks5(
        self, host: str, port: int
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await asyncio.open_connection(self.upstream_host, self.upstream_port)
        writer.write(b"\x05\x01\x00")  # version, 1 method, no-auth
        await writer.drain()
        choice = await reader.readexactly(2)
        if choice[0] != _SOCKS_VERSION or choice[1] != 0x00:
            raise ConnectionError("upstream refused no-auth negotiation")

        if _is_ipv4(host):
            request = b"\x05\x01\x00\x01" + socket.inet_aton(host) + struct.pack("!H", port)
        else:
            domain = host.encode("idna", errors="ignore")
            request = (
                b"\x05\x01\x00\x03" + bytes([len(domain)]) + domain + struct.pack("!H", port)
            )
        writer.write(request)
        await writer.drain()

        reply = await reader.readexactly(4)
        if reply[1] != 0x00:
            raise ConnectionError(f"upstream CONNECT error code {reply[1]}")
        bound_type = reply[3]
        if bound_type == _ATYP_IPV4:
            await reader.readexactly(4)
        elif bound_type == _ATYP_DOMAIN:
            length = (await reader.readexactly(1))[0]
            await reader.readexactly(length)
        elif bound_type == _ATYP_IPV6:
            await reader.readexactly(16)
        await reader.readexactly(2)  # bound port
        return reader, writer

    async def _connect_socks4(
        self, host: str, port: int
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await asyncio.open_connection(self.upstream_host, self.upstream_port)
        if _is_ipv4(host):
            request = b"\x04\x01" + struct.pack("!H", port) + socket.inet_aton(host) + b"\x00"
        else:
            # SOCKS4a: unroutable 0.0.0.1 marks a domain that follows the user id.
            request = (
                b"\x04\x01" + struct.pack("!H", port) + b"\x00\x00\x00\x01" + b"\x00"
                + host.encode("idna", errors="ignore") + b"\x00"
            )
        writer.write(request)
        await writer.drain()
        reply = await reader.readexactly(8)
        if reply[1] != 0x5A:  # 0x5A == request granted
            raise ConnectionError(f"upstream SOCKS4 error code {reply[1]}")
        return reader, writer

    async def _connect_http(
        self, host: str, port: int
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await asyncio.open_connection(self.upstream_host, self.upstream_port)
        request = (
            f"CONNECT {host}:{port} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Proxy-Connection: Keep-Alive\r\n\r\n"
        )
        writer.write(request.encode("ascii", errors="ignore"))
        await writer.drain()
        status_line = await reader.readline()
        parts = status_line.split()
        if len(parts) < 2 or parts[1] != b"200":
            raise ConnectionError(f"upstream HTTP CONNECT failed: {status_line!r}")
        while True:  # drain response headers up to the blank line
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        return reader, writer

    async def _pipe(
        self, src: asyncio.StreamReader, dst: asyncio.StreamWriter, *, upload: bool
    ) -> None:
        try:
            while True:
                data = await src.read(_CHUNK)
                if not data:
                    break
                dst.write(data)
                await dst.drain()
                if upload:
                    self.counters.upload += len(data)
                else:
                    self.counters.download += len(data)
        except (ConnectionError, OSError):
            pass
        finally:
            try:
                if dst.can_write_eof():
                    dst.write_eof()
            except (OSError, RuntimeError):
                pass

    @staticmethod
    async def _reply(writer: asyncio.StreamWriter, payload: bytes) -> None:
        try:
            writer.write(payload)
            await writer.drain()
        except (OSError, ConnectionError):
            pass

    @staticmethod
    def _safe_close(writer: asyncio.StreamWriter) -> None:
        try:
            writer.close()
        except (OSError, RuntimeError):
            pass


def _is_ipv4(host: str) -> bool:
    try:
        socket.inet_aton(host)
        return host.count(".") == 3
    except OSError:
        return False
