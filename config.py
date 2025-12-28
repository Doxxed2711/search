"""Configuration management for marketplace scraper."""

import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration for the marketplace scraper."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.settings = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Error reading config file: {e}")
                return self._get_default_config()
        else:
            config = self._get_default_config()
            self.save_config(config)
            return config

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "search_query": "laptop",
            "location": {
                "craigslist": "sfbay",
                "offerup": "",
                "facebook": ""
            },
            "market_price": None,
            "price_threshold": 0.7,
            "scan_interval_minutes": 15,
            "enabled_sources": ["craigslist", "offerup", "facebook"],
            "notifications": {
                "desktop": True,
                "sound": False
            },
            "deal_quality_filter": "good"
        }

    def save_config(self, config: Optional[Dict] = None):
        """Save configuration to file."""
        if config is None:
            config = self.settings

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.settings.get(key, default)

    def set(self, key: str, value):
        """Set a configuration value."""
        self.settings[key] = value

    def interactive_setup(self):
        """Interactive configuration setup."""
        print("\n" + "=" * 60)
        print("MARKETPLACE SCRAPER - CONFIGURATION SETUP")
        print("=" * 60 + "\n")

        # Search query
        search_query = input("What item do you want to search for? ").strip()
        if search_query:
            self.settings['search_query'] = search_query

        # Market price
        print(f"\nWhat's the typical market price for '{search_query}'?")
        print("(This helps the AI determine if a deal is good)")
        market_price_input = input("Market price (leave blank if unknown): $").strip()
        if market_price_input:
            try:
                self.settings['market_price'] = float(market_price_input)
            except ValueError:
                print("Invalid price, using auto-detection")
                self.settings['market_price'] = None
        else:
            print("Will auto-detect market price from listings")
            self.settings['market_price'] = None

        # Price threshold
        print("\nWhat discount percentage makes a 'good deal'?")
        print("(e.g., 30 means items 30% or more below market price)")
        threshold_input = input("Discount percentage [default: 30]: ").strip()
        if threshold_input:
            try:
                discount_pct = float(threshold_input)
                self.settings['price_threshold'] = 1 - (discount_pct / 100)
            except ValueError:
                print("Invalid percentage, using default (30%)")

        # Location for Craigslist
        print("\nCraigslist location (e.g., 'sfbay', 'newyork', 'seattle')")
        print("See: https://www.craigslist.org/about/sites")
        cl_location = input("Craigslist location [default: sfbay]: ").strip()
        if cl_location:
            self.settings['location']['craigslist'] = cl_location

        # Scan interval
        print("\nHow often should I check for new listings?")
        interval_input = input("Scan interval in minutes [default: 15]: ").strip()
        if interval_input:
            try:
                self.settings['scan_interval_minutes'] = int(interval_input)
            except ValueError:
                print("Invalid interval, using default (15 minutes)")

        # Enabled sources
        print("\nWhich marketplaces do you want to search?")
        print("1. Craigslist")
        print("2. OfferUp")
        print("3. Facebook Marketplace")
        sources_input = input("Enter numbers separated by commas [default: 1,2,3]: ").strip()
        if sources_input:
            source_map = {
                '1': 'craigslist',
                '2': 'offerup',
                '3': 'facebook'
            }
            selected = [source_map[s.strip()] for s in sources_input.split(',')
                       if s.strip() in source_map]
            if selected:
                self.settings['enabled_sources'] = selected

        # Save configuration
        self.save_config()

        print("\n" + "=" * 60)
        print("Configuration saved! Starting scraper...")
        print("=" * 60 + "\n")

    def display_config(self):
        """Display current configuration."""
        print("\n" + "=" * 60)
        print("CURRENT CONFIGURATION")
        print("=" * 60)
        print(f"Search Query: {self.settings['search_query']}")
        print(f"Market Price: ${self.settings['market_price']}" if self.settings['market_price']
              else "Market Price: Auto-detect")
        discount = (1 - self.settings['price_threshold']) * 100
        print(f"Good Deal Threshold: {discount:.0f}% discount or more")
        print(f"Scan Interval: {self.settings['scan_interval_minutes']} minutes")
        print(f"Enabled Sources: {', '.join(self.settings['enabled_sources'])}")
        print(f"Craigslist Location: {self.settings['location']['craigslist']}")
        print("=" * 60 + "\n")
