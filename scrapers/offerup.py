"""OfferUp scraper."""

from typing import List
from bs4 import BeautifulSoup
import logging
from .base import BaseScraper, Listing
import urllib.parse
import json
import re

logger = logging.getLogger(__name__)


class OfferupScraper(BaseScraper):
    """Scraper for OfferUp."""

    def __init__(self, search_query: str, location: str = ""):
        super().__init__(search_query, location)
        self.base_url = "https://offerup.com"

    def get_source_name(self) -> str:
        return "OfferUp"

    def scrape(self) -> List[Listing]:
        """Scrape OfferUp for listings."""
        listings = []

        # Build search URL
        query = urllib.parse.quote(self.search_query)
        search_url = f"{self.base_url}/search/?q={query}"

        logger.info(f"Scraping OfferUp: {search_url}")

        response = self._make_request(search_url)
        if not response:
            return listings

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find JSON data in script tags (OfferUp often embeds data this way)
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'itemListElement' in data:
                    for item_data in data['itemListElement']:
                        listing = self._parse_json_listing(item_data)
                        if listing:
                            listings.append(listing)
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Could not parse JSON data: {e}")

        # Fallback to HTML parsing
        if not listings:
            listings = self._parse_html_listings(soup)

        logger.info(f"Found {len(listings)} listings on OfferUp")
        return listings

    def _parse_json_listing(self, item_data: dict) -> Listing:
        """Parse listing from JSON data."""
        try:
            item = item_data.get('item', {})

            title = item.get('name', '')
            url = item.get('url', '')
            price_str = item.get('offers', {}).get('price', '0')
            price = self._extract_price(price_str)
            image_url = item.get('image', '')

            listing = Listing(
                title=title,
                price=price,
                url=url if url.startswith('http') else self.base_url + url,
                location=self.location,
                description=item.get('description', ''),
                image_url=image_url,
                posted_date='',
                source=self.get_source_name()
            )

            return listing
        except Exception as e:
            logger.warning(f"Error parsing OfferUp JSON listing: {e}")
            return None

    def _parse_html_listings(self, soup: BeautifulSoup) -> List[Listing]:
        """Parse listings from HTML."""
        listings = []

        # Look for common listing containers
        # Note: OfferUp's structure may change; this is a best-effort approach
        items = soup.find_all('a', href=re.compile(r'/item/'))

        for item in items[:20]:  # Limit to first 20 to avoid duplicates
            try:
                url = item.get('href', '')
                if not url.startswith('http'):
                    url = self.base_url + url

                # Extract title
                title_elem = item.find(['h2', 'h3', 'span'], class_=re.compile(r'title|name', re.I))
                title = title_elem.get_text(strip=True) if title_elem else 'Unknown Item'

                # Extract price
                price_elem = item.find(['span', 'div'], class_=re.compile(r'price', re.I))
                price_text = price_elem.get_text(strip=True) if price_elem else '$0'
                price = self._extract_price(price_text)

                # Extract image
                img_elem = item.find('img')
                image_url = img_elem.get('src', '') if img_elem else ''

                if title and url and title != 'Unknown Item':
                    listing = Listing(
                        title=title,
                        price=price,
                        url=url,
                        location=self.location,
                        description='',
                        image_url=image_url,
                        posted_date='',
                        source=self.get_source_name()
                    )
                    listings.append(listing)

            except Exception as e:
                logger.warning(f"Error parsing OfferUp HTML listing: {e}")
                continue

        return listings
