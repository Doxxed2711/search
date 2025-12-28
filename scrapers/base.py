"""Base scraper class for marketplace scrapers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Listing:
    """Represents a marketplace listing."""

    def __init__(self, title: str, price: float, url: str, location: str,
                 description: str = "", image_url: str = "",
                 posted_date: str = "", source: str = ""):
        self.title = title
        self.price = price
        self.url = url
        self.location = location
        self.description = description
        self.image_url = image_url
        self.posted_date = posted_date
        self.source = source

    def to_dict(self) -> Dict:
        """Convert listing to dictionary."""
        return {
            'title': self.title,
            'price': self.price,
            'url': self.url,
            'location': self.location,
            'description': self.description,
            'image_url': self.image_url,
            'posted_date': self.posted_date,
            'source': self.source
        }

    def __repr__(self):
        return f"<Listing: {self.title} - ${self.price} ({self.source})>"


class BaseScraper(ABC):
    """Base class for marketplace scrapers."""

    def __init__(self, search_query: str, location: str = ""):
        self.search_query = search_query
        self.location = location
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    @abstractmethod
    def scrape(self) -> List[Listing]:
        """Scrape listings from the marketplace."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the marketplace source."""
        pass

    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
        return None

    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text."""
        import re
        if not price_text:
            return 0.0

        # Remove currency symbols and commas
        price_text = re.sub(r'[^\d.]', '', price_text)

        try:
            return float(price_text)
        except ValueError:
            return 0.0
