"""Set or restore the Windows system-wide proxy (WinINET).

When enabled, the user's existing settings are saved and restored on disable, so
toggling the gateway never leaves the machine in a broken proxy state.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from app.utils.logger import LOGGER_NAME

_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
_INTERNET_OPTION_SETTINGS_CHANGED = 39
_INTERNET_OPTION_REFRESH = 37


class SystemProxyService(QObject):
    """Toggles the OS proxy so all system traffic flows through the gateway."""

    changed = pyqtSignal(bool)  # active?

    def __init__(self, logger: Optional[logging.Logger] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._log = logger or logging.getLogger(LOGGER_NAME)
        self._active = False
        self._saved: Optional[tuple[int, str]] = None

    @property
    def is_supported(self) -> bool:
        return sys.platform.startswith("win")

    @property
    def is_active(self) -> bool:
        return self._active

    def enable(self, host: str, port: int) -> bool:
        """Route system traffic through ``socks=host:port``."""
        if not self.is_supported:
            self._log.warning("System proxy is only supported on Windows.")
            return False
        import winreg

        try:
            self._saved = self._read_current(winreg)
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"socks={host}:{port}")
            self._refresh()
            self._active = True
            self.changed.emit(True)
            self._log.info("System proxy enabled -> socks=%s:%d", host, port)
            return True
        except OSError as exc:
            self._log.error("Failed to set system proxy: %s", exc)
            return False

    def disable(self) -> bool:
        """Restore the previously saved proxy configuration."""
        if not self.is_supported or not self._active:
            return False
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                if self._saved is not None:
                    enable_val, server_val = self._saved
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, enable_val)
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server_val)
                else:
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            self._refresh()
            self._active = False
            self.changed.emit(False)
            self._log.info("System proxy restored.")
            return True
        except OSError as exc:
            self._log.error("Failed to restore system proxy: %s", exc)
            return False

    @staticmethod
    def _read_current(winreg_module) -> tuple[int, str]:
        with winreg_module.OpenKey(
            winreg_module.HKEY_CURRENT_USER, _REG_PATH, 0, winreg_module.KEY_READ
        ) as key:
            try:
                enable_val = int(winreg_module.QueryValueEx(key, "ProxyEnable")[0])
            except FileNotFoundError:
                enable_val = 0
            try:
                server_val = str(winreg_module.QueryValueEx(key, "ProxyServer")[0])
            except FileNotFoundError:
                server_val = ""
        return enable_val, server_val

    @staticmethod
    def _refresh() -> None:
        """Broadcast the change so running apps pick up the new settings."""
        try:
            import ctypes

            wininet = ctypes.windll.Wininet
            wininet.InternetSetOptionW(0, _INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            wininet.InternetSetOptionW(0, _INTERNET_OPTION_REFRESH, 0, 0)
        except (OSError, AttributeError):
            pass
