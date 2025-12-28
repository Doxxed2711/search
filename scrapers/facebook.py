"""Facebook Marketplace scraper."""

from typing import List
from bs4 import BeautifulSoup
import logging
from .base import BaseScraper, Listing
import urllib.parse
import json
import re

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):
    """
    Scraper for Facebook Marketplace.

    Note: Facebook has strong anti-scraping measures. This scraper attempts basic
    scraping but may require Selenium/Playwright for better results or if blocked.
    Consider using Facebook Graph API for production use.
    """

    def __init__(self, search_query: str, location: str = ""):
        super().__init__(search_query, location)
        self.base_url = "https://www.facebook.com"
        # Update headers to look more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_source_name(self) -> str:
        return "Facebook Marketplace"

    def scrape(self) -> List[Listing]:
        """
        Scrape Facebook Marketplace for listings.

        Note: This method may have limited success due to Facebook's anti-scraping.
        For production use, consider:
        1. Using Selenium/Playwright for JavaScript rendering
        2. Using Facebook Graph API (requires authentication)
        3. Using official Facebook marketplace tools
        """
        listings = []

        # Build search URL
        query = urllib.parse.quote(self.search_query)
        # Facebook Marketplace search URL format
        search_url = f"{self.base_url}/marketplace/search/?query={query}"

        logger.info(f"Scraping Facebook Marketplace: {search_url}")
        logger.warning("Facebook Marketplace scraping may be limited due to anti-scraping measures")

        response = self._make_request(search_url)
        if not response:
            logger.warning("Could not fetch Facebook Marketplace. Consider using Selenium or the Graph API.")
            return listings

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to extract data from embedded JSON
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                # Facebook embeds data in complex nested structures
                # This is a simplified approach and may need adjustment
                listings_data = self._extract_listings_from_json(data)
                for listing_data in listings_data:
                    listing = self._parse_json_listing(listing_data)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Could not parse JSON data: {e}")

        # Fallback HTML parsing (likely to have limited success)
        if not listings:
            logger.info("JSON parsing failed, trying HTML parsing (may have limited results)")
            listings = self._parse_html_listings(soup)

        if not listings:
            logger.warning(
                "No listings found on Facebook Marketplace. This is likely due to:\n"
                "  1. Facebook's anti-scraping measures blocking the request\n"
                "  2. JavaScript-rendered content that requires Selenium/Playwright\n"
                "  3. Need for authentication\n"
                "Consider using the Facebook Graph API or Selenium for better results."
            )

        logger.info(f"Found {len(listings)} listings on Facebook Marketplace")
        return listings

    def _extract_listings_from_json(self, data, listings=None):
        """Recursively extract listing data from nested JSON."""
        if listings is None:
            listings = []

        if isinstance(data, dict):
            # Look for marketplace listing patterns
            if 'marketplace_listing_title' in data or 'listing_price' in data:
                listings.append(data)

            for value in data.values():
                self._extract_listings_from_json(value, listings)

        elif isinstance(data, list):
            for item in data:
                self._extract_listings_from_json(item, listings)

        return listings

    def _parse_json_listing(self, data: dict) -> Listing:
        """Parse listing from JSON data."""
        try:
            title = data.get('marketplace_listing_title', data.get('title', ''))
            url_slug = data.get('marketplace_listing_url', data.get('url', ''))
            url = url_slug if url_slug.startswith('http') else self.base_url + url_slug

            # Extract price
            price_data = data.get('listing_price', {})
            if isinstance(price_data, dict):
                price_text = price_data.get('amount', '0')
            else:
                price_text = str(price_data)
            price = self._extract_price(price_text)

            # Extract location
            location_data = data.get('location', {})
            if isinstance(location_data, dict):
                location = location_data.get('name', self.location)
            else:
                location = str(location_data) if location_data else self.location

            # Extract image
            image_data = data.get('primary_listing_photo', {})
            image_url = image_data.get('url', '') if isinstance(image_data, dict) else ''

            if title and url:
                listing = Listing(
                    title=title,
                    price=price,
                    url=url,
                    location=location,
                    description='',
                    image_url=image_url,
                    posted_date='',
                    source=self.get_source_name()
                )
                return listing

        except Exception as e:
            logger.warning(f"Error parsing Facebook JSON listing: {e}")

        return None

    def _parse_html_listings(self, soup: BeautifulSoup) -> List[Listing]:
        """Attempt to parse listings from HTML (likely limited success)."""
        listings = []

        # Look for common patterns (may need adjustment based on Facebook's current structure)
        links = soup.find_all('a', href=re.compile(r'/marketplace/item/'))

        for link in links[:20]:
            try:
                url = link.get('href', '')
                if not url.startswith('http'):
                    url = self.base_url + url

                # Try to extract title
                title = link.get('aria-label', '') or link.get_text(strip=True)

                # Try to find price nearby
                parent = link.find_parent()
                price_elem = parent.find(text=re.compile(r'\$\d+')) if parent else None
                price = self._extract_price(price_elem) if price_elem else 0.0

                if title and url:
                    listing = Listing(
                        title=title,
                        price=price,
                        url=url,
                        location=self.location,
                        description='',
                        image_url='',
                        posted_date='',
                        source=self.get_source_name()
                    )
                    listings.append(listing)

            except Exception as e:
                logger.warning(f"Error parsing Facebook HTML listing: {e}")
                continue

        return listings
