"""Proxy scraping subsystem."""

from app.scraper.scraper import ProxyScraper
from app.scraper.sources import DEFAULT_SOURCES

__all__ = ["ProxyScraper", "DEFAULT_SOURCES"]
