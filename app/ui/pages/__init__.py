"""Stacked application pages."""

from app.ui.pages.checker_page import CheckerPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.docs_page import DocsPage
from app.ui.pages.gateway_page import GatewayPage
from app.ui.pages.logs_page import LogsPage
from app.ui.pages.proxies_page import ProxiesPage
from app.ui.pages.scraper_page import ScraperPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.traffic_page import TrafficPage
from app.ui.pages.updates_page import UpdatesPage

__all__ = [
    "CheckerPage",
    "DashboardPage",
    "DocsPage",
    "GatewayPage",
    "LogsPage",
    "ProxiesPage",
    "ScraperPage",
    "SettingsPage",
    "TrafficPage",
    "UpdatesPage",
]
