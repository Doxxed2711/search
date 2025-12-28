#!/usr/bin/env python3
"""
Marketplace Deal Scraper

Continuously monitors Facebook Marketplace, OfferUp, and Craigslist for specific
items and uses AI to filter good deals from bad deals.

Usage:
    python marketplace_scraper.py [--setup] [--config config.json]
"""

import argparse
import logging
import time
import sys
from datetime import datetime
from typing import List

from scrapers import CraigslistScraper, OfferupScraper, FacebookScraper
from scrapers.base import Listing
from deal_analyzer import DealAnalyzer
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


class MarketplaceScraper:
    """Main marketplace scraper orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self.db = ListingDatabase()
        self.analyzer = DealAnalyzer(
            market_price=config.get('market_price'),
            price_threshold=config.get('price_threshold', 0.7)
        )
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
        """Analyze listings and save new ones to database."""
        new_good_deals = []

        # Auto-detect market price if not set
        if not self.analyzer.market_price and listings:
            estimated_price = self.analyzer.estimate_market_price(listings)
            if estimated_price:
                self.analyzer.set_market_price(estimated_price)
                logger.info(f"Auto-detected market price: ${estimated_price:.2f}")

        for listing in listings:
            # Skip if already seen
            if self.db.is_seen(listing):
                logger.debug(f"Skipping already seen listing: {listing.title}")
                continue

            # Analyze the listing
            analysis = self.analyzer.analyze_listing(listing)

            # Save to database
            self.db.add_listing(listing, analysis)

            # Track good deals
            if analysis['is_good_deal']:
                new_good_deals.append(listing)
                logger.info(
                    f"⭐ Good deal found: {listing.title} - ${listing.price} "
                    f"({analysis['deal_quality']}, score: {analysis['confidence_score']:.1f})"
                )
                logger.info(f"   Reasons: {', '.join(analysis['reasons'])}")

                # Mark as notified
                self.db.mark_as_notified(listing)

        return new_good_deals

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

        # Notify user of good deals
        if good_deals:
            deal_dicts = [
                {
                    'title': deal.title,
                    'price': deal.price,
                    'url': deal.url,
                    'location': deal.location,
                    'source': deal.source,
                    'confidence_score': 75.0,  # Approximate for notification
                    'deal_quality': 'good'
                }
                for deal in good_deals
            ]
            self.notifier.notify(deal_dicts)
        else:
            logger.info("No new good deals found this cycle")

        # Display stats
        stats = self.db.get_stats()
        logger.info(f"Database stats: {stats}")

    def run_continuous(self):
        """Run continuous scraping with interval."""
        scan_interval = self.config.get('scan_interval_minutes', 15)
        logger.info(f"Starting continuous scraping (interval: {scan_interval} minutes)")
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
        description='Marketplace Deal Scraper - Find great deals automatically!'
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

    args = parser.parse_args()

    # Load or create configuration
    config = Config(args.config)

    # Run setup if requested
    if args.setup:
        config.interactive_setup()

    # Display configuration
    config.display_config()

    # Create and run scraper
    scraper = MarketplaceScraper(config)

    if args.once:
        scraper.run_once()
        scraper.cleanup()
    else:
        scraper.run_continuous()


if __name__ == '__main__':
    main()
