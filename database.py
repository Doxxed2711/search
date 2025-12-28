"""Database for tracking seen listings."""

import sqlite3
import logging
from typing import List, Optional
from datetime import datetime
import hashlib
from scrapers.base import Listing

logger = logging.getLogger(__name__)


class ListingDatabase:
    """SQLite database for tracking seen listings."""

    def __init__(self, db_path: str = "listings.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Create listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_hash TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    url TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    image_url TEXT,
                    posted_date TEXT,
                    source TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_good_deal INTEGER DEFAULT 0,
                    confidence_score REAL DEFAULT 0,
                    deal_quality TEXT,
                    notified INTEGER DEFAULT 0
                )
            ''')

            # Create index on listing_hash for fast lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_listing_hash
                ON listings(listing_hash)
            ''')

            # Create index on is_good_deal for filtering
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_good_deals
                ON listings(is_good_deal, notified)
            ''')

            self.conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def _generate_hash(self, listing: Listing) -> str:
        """Generate a unique hash for a listing."""
        # Use URL and title to create a unique identifier
        unique_string = f"{listing.url}:{listing.title}:{listing.price}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def is_seen(self, listing: Listing) -> bool:
        """Check if a listing has been seen before."""
        listing_hash = self._generate_hash(listing)

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'SELECT id FROM listings WHERE listing_hash = ?',
                (listing_hash,)
            )
            result = cursor.fetchone()
            return result is not None

        except sqlite3.Error as e:
            logger.error(f"Error checking if listing is seen: {e}")
            return False

    def add_listing(self, listing: Listing, analysis: dict = None):
        """Add a new listing to the database."""
        listing_hash = self._generate_hash(listing)

        try:
            cursor = self.conn.cursor()

            # Prepare analysis data
            is_good_deal = 0
            confidence_score = 0.0
            deal_quality = 'unknown'

            if analysis:
                is_good_deal = 1 if analysis.get('is_good_deal', False) else 0
                confidence_score = analysis.get('confidence_score', 0.0)
                deal_quality = analysis.get('deal_quality', 'unknown')

            cursor.execute('''
                INSERT OR REPLACE INTO listings
                (listing_hash, title, price, url, location, description,
                 image_url, posted_date, source, is_good_deal,
                 confidence_score, deal_quality, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                listing_hash,
                listing.title,
                listing.price,
                listing.url,
                listing.location,
                listing.description,
                listing.image_url,
                listing.posted_date,
                listing.source,
                is_good_deal,
                confidence_score,
                deal_quality
            ))

            self.conn.commit()
            logger.debug(f"Added listing to database: {listing.title}")

        except sqlite3.Error as e:
            logger.error(f"Error adding listing to database: {e}")

    def mark_as_notified(self, listing: Listing):
        """Mark a listing as having been notified to the user."""
        listing_hash = self._generate_hash(listing)

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE listings SET notified = 1 WHERE listing_hash = ?',
                (listing_hash,)
            )
            self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Error marking listing as notified: {e}")

    def get_unnotified_good_deals(self) -> List[dict]:
        """Get all good deals that haven't been notified yet."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT title, price, url, location, source,
                       confidence_score, deal_quality
                FROM listings
                WHERE is_good_deal = 1 AND notified = 0
                ORDER BY confidence_score DESC
            ''')

            results = cursor.fetchall()
            deals = []

            for row in results:
                deals.append({
                    'title': row[0],
                    'price': row[1],
                    'url': row[2],
                    'location': row[3],
                    'source': row[4],
                    'confidence_score': row[5],
                    'deal_quality': row[6]
                })

            return deals

        except sqlite3.Error as e:
            logger.error(f"Error getting unnotified deals: {e}")
            return []

    def get_stats(self) -> dict:
        """Get database statistics."""
        try:
            cursor = self.conn.cursor()

            # Total listings
            cursor.execute('SELECT COUNT(*) FROM listings')
            total = cursor.fetchone()[0]

            # Good deals
            cursor.execute('SELECT COUNT(*) FROM listings WHERE is_good_deal = 1')
            good_deals = cursor.fetchone()[0]

            # Notified deals
            cursor.execute('SELECT COUNT(*) FROM listings WHERE notified = 1')
            notified = cursor.fetchone()[0]

            return {
                'total_listings': total,
                'good_deals': good_deals,
                'notified': notified,
                'pending_notifications': good_deals - notified
            }

        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
