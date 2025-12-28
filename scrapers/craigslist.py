"""Craigslist scraper."""

from typing import List
from bs4 import BeautifulSoup
import logging
from .base import BaseScraper, Listing
import urllib.parse

logger = logging.getLogger(__name__)


class CraigslistScraper(BaseScraper):
    """Scraper for Craigslist."""

    def __init__(self, search_query: str, location: str = "sfbay"):
        """
        Initialize Craigslist scraper.

        Args:
            search_query: Item to search for
            location: Craigslist subdomain (e.g., 'sfbay', 'newyork', 'seattle')
        """
        super().__init__(search_query, location)
        self.base_url = f"https://{location}.craigslist.org"

    def get_source_name(self) -> str:
        return "Craigslist"

    def scrape(self) -> List[Listing]:
        """Scrape Craigslist for listings."""
        listings = []

        # Build search URL
        query_params = urllib.parse.urlencode({'query': self.search_query, 'sort': 'date'})
        search_url = f"{self.base_url}/search/sss?{query_params}"

        logger.info(f"Scraping Craigslist: {search_url}")

        response = self._make_request(search_url)
        if not response:
            return listings

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all listing items
        items = soup.find_all('li', class_='cl-static-search-result')

        for item in items:
            try:
                # Extract title and URL
                title_elem = item.find('div', class_='title')
                if not title_elem:
                    continue

                link = title_elem.find('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                url = link.get('href', '')

                # Make URL absolute if needed
                if url.startswith('/'):
                    url = self.base_url + url

                # Extract price
                price_elem = item.find('div', class_='price')
                price_text = price_elem.get_text(strip=True) if price_elem else '$0'
                price = self._extract_price(price_text)

                # Extract location
                location_elem = item.find('div', class_='location')
                location = location_elem.get_text(strip=True) if location_elem else self.location

                # Extract posting date
                date_elem = item.find('div', class_='date')
                posted_date = date_elem.get_text(strip=True) if date_elem else ''

                # Extract image URL
                image_elem = item.find('img')
                image_url = image_elem.get('src', '') if image_elem else ''

                listing = Listing(
                    title=title,
                    price=price,
                    url=url,
                    location=location,
                    description='',
                    image_url=image_url,
                    posted_date=posted_date,
                    source=self.get_source_name()
                )

                listings.append(listing)
                logger.debug(f"Found listing: {listing}")

            except Exception as e:
                logger.warning(f"Error parsing Craigslist listing: {e}")
                continue

        logger.info(f"Found {len(listings)} listings on Craigslist")
        return listings
