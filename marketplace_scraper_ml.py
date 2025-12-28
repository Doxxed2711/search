#!/usr/bin/env python3
"""
AI-Powered Marketplace Deal Scraper with Android App Integration

Continuously monitors Facebook Marketplace, OfferUp, and Craigslist for specific
items and uses ML to filter good deals from bad deals. Sends notifications to
Android app via API server.

Usage:
    python marketplace_scraper_ml.py [--setup] [--config config.json]
"""

import argparse
import logging
import time
import sys
import requests
from datetime import datetime
from typing import List

from scrapers import CraigslistScraper, OfferupScraper, FacebookScraper
from scrapers.base import Listing
from ml_models.price_predictor import PricePredictor
from database import ListingDatabase
from notifier import Notifier
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class MarketplaceScraperML:
    """Main marketplace scraper orchestrator with ML integration."""

    def __init__(self, config: Config, api_url: str = "http://localhost:5000"):
        self.config = config
        self.api_url = api_url
        self.db = ListingDatabase()
        self.ml_model = PricePredictor()
        self.notifier = Notifier(
            enable_desktop=config.get('notifications', {}).get('desktop', True),
            enable_sound=config.get('notifications', {}).get('sound', False)
        )
        self.scrapers = self._init_scrapers()

    def _init_scrapers(self) -> List:
        """Initialize scrapers based on configuration."""
        scrapers = []
        enabled = self.config.get('enabled_sources', ['craigslist', 'offerup', 'facebook'])
        search_query = self.config.get('search_query', 'laptop')
        locations = self.config.get('location', {})

        if 'craigslist' in enabled:
            cl_location = locations.get('craigslist', 'sfbay')
            scrapers.append(CraigslistScraper(search_query, cl_location))
            logger.info(f"Initialized Craigslist scraper (location: {cl_location})")

        if 'offerup' in enabled:
            ou_location = locations.get('offerup', '')
            scrapers.append(OfferupScraper(search_query, ou_location))
            logger.info("Initialized OfferUp scraper")

        if 'facebook' in enabled:
            fb_location = locations.get('facebook', '')
            scrapers.append(FacebookScraper(search_query, fb_location))
            logger.info("Initialized Facebook Marketplace scraper")

        return scrapers

    def scrape_all(self) -> List[Listing]:
        """Scrape all enabled marketplaces."""
        all_listings = []

        for scraper in self.scrapers:
            try:
                logger.info(f"Scraping {scraper.get_source_name()}...")
                listings = scraper.scrape()
                all_listings.extend(listings)
                logger.info(f"Found {len(listings)} listings on {scraper.get_source_name()}")
            except Exception as e:
                logger.error(f"Error scraping {scraper.get_source_name()}: {e}")

        return all_listings

    def analyze_and_save(self, listings: List[Listing]) -> List[Listing]:
        """Analyze listings using ML model and save new ones to database."""
        new_good_deals = []

        # Auto-detect market price if not set
        if not self.config.get('market_price') and listings:
            prices = [l.price for l in listings if l.price > 0]
            if prices:
                estimated_price = self._estimate_market_price(prices)
                self.config.set('market_price', estimated_price)
                logger.info(f"Auto-detected market price: ${estimated_price:.2f}")

        market_price = self.config.get('market_price')

        for listing in listings:
            # Skip if already seen
            if self.db.is_seen(listing):
                logger.debug(f"Skipping already seen listing: {listing.title}")
                continue

            # Prepare listing data for ML model
            listing_data = {
                'title': listing.title,
                'description': listing.description,
                'price': listing.price,
                'market_price': market_price,
                'image_url': listing.image_url,
                'search_keywords': self.config.get('search_query', '').split()
            }

            # Analyze using ML model
            prediction = self.ml_model.predict_deal_quality(listing_data)

            # Convert to expected format
            analysis = {
                'is_good_deal': prediction['is_good_deal'],
                'confidence_score': prediction['score'],
                'deal_quality': prediction['quality'],
                'reasons': self._format_reasons(prediction),
                'warnings': []
            }

            # Save to database
            self.db.add_listing(listing, analysis)

            # Track good deals
            if analysis['is_good_deal']:
                new_good_deals.append(listing)
                logger.info(
                    f"⭐ Good deal found: {listing.title} - ${listing.price} "
                    f"({analysis['deal_quality']}, score: {analysis['confidence_score']:.1f})"
                )

                # Send to API server for push notification
                self._notify_api_server({
                    'title': listing.title,
                    'price': listing.price,
                    'url': listing.url,
                    'source': listing.source,
                    'location': listing.location,
                    'score': analysis['confidence_score'],
                    'quality': analysis['deal_quality']
                })

                # Mark as notified
                self.db.mark_as_notified(listing)

        return new_good_deals

    def _format_reasons(self, prediction: dict) -> List[str]:
        """Format prediction features into readable reasons."""
        reasons = []
        features = prediction.get('features', {})

        if features.get('price_ratio', 1.0) < 0.7:
            discount = (1 - features['price_ratio']) * 100
            reasons.append(f"Great price: {discount:.0f}% below market value")

        if features.get('condition_score', 0.5) > 0.7:
            reasons.append("Excellent condition mentioned")

        if features.get('listing_quality', 0.5) > 0.7:
            reasons.append("High-quality listing with details and images")

        return reasons

    def _estimate_market_price(self, prices: List[float]) -> float:
        """Estimate market price from a list of prices using median."""
        if not prices:
            return 0.0

        prices.sort()
        n = len(prices)

        if n < 3:
            return sum(prices) / n

        # Remove outliers using IQR
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = prices[q1_idx]
        q3 = prices[q3_idx]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        filtered_prices = [p for p in prices if lower_bound <= p <= upper_bound]

        if not filtered_prices:
            return sum(prices) / n

        # Return median
        median_idx = len(filtered_prices) // 2
        return filtered_prices[median_idx]

    def _notify_api_server(self, deal: dict):
        """Send deal notification to API server."""
        try:
            response = requests.post(
                f"{self.api_url}/api/deals/new",
                json={'deal': deal},
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Notified API server about deal: {deal['title']}")
            else:
                logger.warning(f"Failed to notify API server: {response.status_code}")

        except Exception as e:
            logger.error(f"Error notifying API server: {e}")

    def run_once(self):
        """Run a single scraping cycle."""
        logger.info("=" * 60)
        logger.info(f"Starting scrape cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # Scrape all sources
        listings = self.scrape_all()
        logger.info(f"Total listings found: {len(listings)}")

        if not listings:
            logger.warning("No listings found this cycle")
            return

        # Analyze and save
        good_deals = self.analyze_and_save(listings)

        # Notify user of good deals (console/desktop)
        if good_deals:
            deal_dicts = [
                {
                    'title': deal.title,
                    'price': deal.price,
                    'url': deal.url,
                    'location': deal.location,
                    'source': deal.source,
                    'confidence_score': 75.0,
                    'deal_quality': 'good'
                }
                for deal in good_deals
            ]
            self.notifier.notify(deal_dicts)
        else:
            logger.info("No new good deals found this cycle")

        # Display stats
        stats = self.db.get_stats()
        ml_stats = self.ml_model.get_stats()
        logger.info(f"Database stats: {stats}")
        logger.info(f"ML model stats: {ml_stats}")

    def run_continuous(self):
        """Run continuous scraping with interval."""
        scan_interval = self.config.get('scan_interval_minutes', 15)
        logger.info(f"Starting continuous scraping (interval: {scan_interval} minutes)")
        logger.info(f"API server: {self.api_url}")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                self.run_once()

                # Wait for next cycle
                logger.info(f"Waiting {scan_interval} minutes until next scan...")
                logger.info("=" * 60 + "\n")
                time.sleep(scan_interval * 60)

        except KeyboardInterrupt:
            logger.info("\nStopping scraper...")
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.db.close()
        logger.info("Scraper stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI-Powered Marketplace Deal Scraper with Android App'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run interactive configuration setup'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (don\'t run continuously)'
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:5000',
        help='API server URL (default: http://localhost:5000)'
    )

    args = parser.parse_args()

    # Load or create configuration
    config = Config(args.config)

    # Run setup if requested
    if args.setup:
        config.interactive_setup()

    # Display configuration
    config.display_config()

    # Create and run scraper
    scraper = MarketplaceScraperML(config, args.api_url)

    if args.once:
        scraper.run_once()
        scraper.cleanup()
    else:
        scraper.run_continuous()


if __name__ == '__main__':
    main()
