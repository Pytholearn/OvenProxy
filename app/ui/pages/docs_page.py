"""In-app documentation rendered in a styled text browser."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QTextBrowser, QWidget

from app.constants import APP_NAME, APP_VERSION
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.widgets.cards import Card


def _build_html() -> str:
    c = COLORS
    return f"""
    <style>
        h2 {{ color: {c['accent']}; margin-top: 18px; }}
        h3 {{ color: {c['text']}; margin-top: 14px; }}
        p, li {{ color: {c['text']}; line-height: 1.5; }}
        code {{ background: {c['surface_alt']}; color: {c['accent']}; padding: 1px 5px; border-radius: 4px; }}
        .muted {{ color: {c['text_muted']}; }}
    </style>

    <h1 style="color:{c['text']}">{APP_NAME} — User Guide <span class="muted">v{APP_VERSION}</span></h1>
    <p>A SOCKS5 / SOCKS4 / HTTP proxy scraper, checker and local gateway. Below is everything
    you need to go from zero proxies to routing your PC or phone through a clean IP.</p>

    <h2>1 · Scraper</h2>
    <p>Enable the sources you trust (or <b>Add</b> / <b>Import URLs</b> for your own). Use the
    <b>Scrape</b> checkboxes to choose which protocols to collect — <b>SOCKS5</b>, <b>SOCKS4</b>
    and/or <b>HTTP</b> — then press <b>Start Scraping</b>. Lists download in parallel and
    duplicates are removed.</p>

    <h2>2 · Checker</h2>
    <p>After scraping you're moved here automatically. Press <b>Start Check</b> to validate
    every proxy. Each proxy is tested with its own protocol scheme, and {APP_NAME} measures
    latency and resolves country, exit IP and anonymity by sending a request <i>through</i> the
    proxy. Only live proxies move on.</p>

    <h2>3 · Working Proxies</h2>
    <p>Search, filter by country, and <b>Sort by Ping</b> to put the fastest proxies on top.
    Select rows to <b>Copy</b>, <b>Delete</b> or <b>Use in Gateway</b>. Export to
    <code>txt</code>, <code>csv</code> or <code>json</code>.</p>

    <h2>4 · Local Gateway</h2>
    <p>Pick an upstream proxy and a local port, then <b>Start</b>. {APP_NAME} runs a local
    SOCKS5 server that forwards everything through that proxy — the upstream may be
    <b>SOCKS5, SOCKS4 or HTTP</b>. Point any app at <code>socks5://127.0.0.1:1080</code>.</p>

    <h3>Route ALL system traffic</h3>
    <p>Tick <b>Set as system proxy</b> before starting. {APP_NAME} writes the Windows proxy
    setting to <code>socks=127.0.0.1:port</code> and restores your previous setting when you
    stop the gateway or close the app. <span class="muted">(Windows only; SOCKS support in
    the system proxy is best-effort — app-level SOCKS config is always most reliable.)</span></p>

    <h3>Connect your phone (mobile mode)</h3>
    <p>Tick <b>Allow LAN / mobile</b> before starting. The gateway then binds to all network
    interfaces and shows your LAN address, e.g. <code>192.168.1.20:1080</code>.</p>
    <ol>
        <li>Keep your phone on the <b>same Wi-Fi</b> as this PC.</li>
        <li>Android: <i>Wi-Fi → your network → Edit → Advanced → Proxy → Manual</i>.
            iOS: <i>Wi-Fi → (i) → Configure Proxy → Manual</i>.</li>
        <li>Enter the LAN IP and port shown on the Gateway page.</li>
        <li>If it doesn't connect, allow {APP_NAME} through the Windows Firewall.</li>
    </ol>

    <h2>5 · Traffic Monitor</h2>
    <p>Live per-second upload/download charts, totals and active connection count while the
    gateway is running.</p>

    <h2>6 · Updates</h2>
    <p>The <b>Updates</b> page checks a remote <code>version</code> file and upgrades via the
    <code>autoupgrader</code> library. When a newer version exists a banner appears at the top
    of the window. Configure the version-file URL and repository in <b>Settings</b>.</p>

    <h2>7 · Settings</h2>
    <p>Tune threads, timeout, retries, max proxies, auto-export and the update sources.
    Everything is saved automatically.</p>

    <h2>Troubleshooting</h2>
    <ul>
        <li><b>No working proxies?</b> Free proxies die fast — scrape again and raise the
        timeout in Settings.</li>
        <li><b>Phone can't connect?</b> Check the firewall and that both devices share the
        same network.</li>
        <li><b>Update failed?</b> Ensure <code>autoupgrader</code> and <code>git</code> are
        installed.</li>
    </ul>
    """


class DocsPage(BasePage):
    """Renders the bundled HTML documentation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Documentation", "How to use every feature", parent)
        card = Card()
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(_build_html())
        card.body().addWidget(browser)
        self.content().addWidget(card, 1)
