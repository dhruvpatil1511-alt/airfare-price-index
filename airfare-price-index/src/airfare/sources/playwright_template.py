"""TEMPLATE for a real website scraper. Not registered by default.

Before scraping any site:
  * Read its robots.txt and Terms of Service. Many airline and OTA sites
    forbid automated access; if so, use an official/partner API instead
    (e.g. Amadeus Self-Service, Skyscanner/Kiwi partner APIs).
  * Rate-limit (one request every few seconds) and identify yourself in the
    User-Agent. Collect once a day, not continuously.

To use: pip install playwright, fill in the TODOs, then register the class in
sources/__init__.py under SOURCES.
"""

from __future__ import annotations

import time
from datetime import date

from ..models import FareObservation, Route
from .base import FareSource


class PlaywrightSource(FareSource):
    name = "example_site"  # TODO: rename to the site you scrape
    min_delay_s = 3.0

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self._last = 0.0

    def _polite_wait(self) -> None:
        wait = self.min_delay_s - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def fetch(self, route: Route, collected_on: date, travel_date: date) -> list[FareObservation]:
        from playwright.sync_api import sync_playwright  # imported lazily

        self._polite_wait()
        url = (  # TODO: real search URL format for your source
            f"https://example.com/search?from={route.origin}&to={route.destination}"
            f"&date={travel_date.isoformat()}"
        )
        fares: list[FareObservation] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page(user_agent="airfare-price-index (student research project)")
            page.goto(url, wait_until="networkidle")
            # TODO: replace selectors with the site's real ones
            for card in page.locator(".flight-card").all():
                carrier = card.locator(".airline-name").inner_text().strip()
                price_text = card.locator(".price").inner_text()
                fare = float("".join(ch for ch in price_text if ch.isdigit()))
                fares.append(
                    FareObservation(route, self.name, collected_on, travel_date, carrier, fare)
                )
            browser.close()
        return fares
