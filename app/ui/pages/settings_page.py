"""Settings page bound to the :class:`AppConfig` dataclass."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app.config import AppConfig
from app.resources.icons import make_icon
from app.ui.pages.base_page import BasePage
from app.widgets.cards import Card


class SettingsPage(BasePage):
    """Edits performance, behaviour and appearance settings."""

    settings_changed = pyqtSignal()

    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__("Settings", "Tune performance and behaviour", parent)
        self._config = config

        card = Card()
        form = QFormLayout()
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(12)

        self._threads = QSpinBox()
        self._threads.setRange(1, 2000)
        form.addRow("Threads", self._threads)

        self._timeout = QDoubleSpinBox()
        self._timeout.setRange(1.0, 60.0)
        self._timeout.setSingleStep(0.5)
        self._timeout.setSuffix(" s")
        form.addRow("Timeout", self._timeout)

        self._retries = QSpinBox()
        self._retries.setRange(1, 10)
        form.addRow("Retry count", self._retries)

        self._max_proxies = QSpinBox()
        self._max_proxies.setRange(0, 1_000_000)
        self._max_proxies.setSpecialValueText("Unlimited")
        form.addRow("Max proxies to scrape", self._max_proxies)

        self._gateway_port = QSpinBox()
        self._gateway_port.setRange(1, 65535)
        form.addRow("Default gateway port", self._gateway_port)

        self._check_url = QLineEdit()
        form.addRow("Check URL", self._check_url)

        self._update_url = QLineEdit()
        self._update_url.setPlaceholderText("Raw GitHub URL to the version file")
        form.addRow("Update version URL", self._update_url)

        self._update_repo = QLineEdit()
        self._update_repo.setPlaceholderText("https://github.com/<user>/<repo>.git")
        form.addRow("Update repository", self._update_repo)

        self._update_startup = QCheckBox("Check for updates on startup")
        form.addRow("Updates", self._update_startup)

        self._auto_remove = QCheckBox("Automatically discard dead proxies")
        form.addRow("Dead proxies", self._auto_remove)

        self._auto_export = QCheckBox("Auto-export working proxies after a check")
        form.addRow("Auto export", self._auto_export)

        self._theme = QComboBox()
        self._theme.addItems(["dark"])
        form.addRow("Theme", self._theme)

        self._language = QComboBox()
        self._language.addItems(["en", "fa"])
        form.addRow("Language", self._language)

        card.body().addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        save_btn = QPushButton("  Save Settings")
        save_btn.setObjectName("Primary")
        save_btn.setIcon(make_icon("checker", "#06222f"))
        save_btn.clicked.connect(self._save)
        buttons.addWidget(save_btn)
        card.body().addLayout(buttons)

        self.content().addWidget(card)
        self.content().addStretch(1)
        self._load()

    def _load(self) -> None:
        config = self._config
        self._threads.setValue(config.threads)
        self._timeout.setValue(config.timeout)
        self._retries.setValue(config.retries)
        self._max_proxies.setValue(config.max_proxies)
        self._gateway_port.setValue(config.gateway_port)
        self._check_url.setText(config.check_url)
        self._update_url.setText(config.update_version_url)
        self._update_repo.setText(config.update_repo_url)
        self._update_startup.setChecked(config.check_updates_on_startup)
        self._auto_remove.setChecked(config.auto_remove_dead)
        self._auto_export.setChecked(config.auto_export)
        self._theme.setCurrentText(config.theme)
        self._language.setCurrentText(config.language)

    def _save(self) -> None:
        self._config.update(
            threads=self._threads.value(),
            timeout=self._timeout.value(),
            retries=self._retries.value(),
            max_proxies=self._max_proxies.value(),
            gateway_port=self._gateway_port.value(),
            check_url=self._check_url.text().strip() or self._config.check_url,
            update_version_url=self._update_url.text().strip() or self._config.update_version_url,
            update_repo_url=self._update_repo.text().strip() or self._config.update_repo_url,
            check_updates_on_startup=self._update_startup.isChecked(),
            auto_remove_dead=self._auto_remove.isChecked(),
            auto_export=self._auto_export.isChecked(),
            theme=self._theme.currentText(),
            language=self._language.currentText(),
        )
        self.settings_changed.emit()
