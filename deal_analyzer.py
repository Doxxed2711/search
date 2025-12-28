"""AI-powered deal analyzer for marketplace listings."""

import logging
from typing import Dict, List, Optional
import re
from scrapers.base import Listing

logger = logging.getLogger(__name__)


class DealAnalyzer:
    """
    Analyzes marketplace listings to determine if they're good deals.

    Uses multiple criteria:
    1. Price comparison against market average
    2. Keyword analysis for condition indicators
    3. Price anomaly detection
    4. Title/description quality analysis
    """

    def __init__(self, market_price: Optional[float] = None,
                 price_threshold: float = 0.7):
        """
        Initialize the deal analyzer.

        Args:
            market_price: Expected market price for the item (optional)
            price_threshold: Price ratio threshold for good deals (default 0.7 = 30% off)
        """
        self.market_price = market_price
        self.price_threshold = price_threshold

        # Keywords that indicate good condition
        self.good_condition_keywords = [
            'new', 'mint', 'excellent', 'perfect', 'unused', 'sealed',
            'like new', 'barely used', 'pristine', 'flawless', 'brand new'
        ]

        # Keywords that indicate poor condition
        self.bad_condition_keywords = [
            'broken', 'damaged', 'cracked', 'scratched', 'worn', 'defective',
            'for parts', 'not working', 'needs repair', 'as-is', 'faulty'
        ]

        # Red flag keywords that indicate scams or bad deals
        self.red_flag_keywords = [
            'replica', 'fake', 'copy', 'imitation', 'knockoff',
            'financing available', 'credit check', 'mlm', 'work from home'
        ]

    def analyze_listing(self, listing: Listing) -> Dict:
        """
        Analyze a listing and return deal quality assessment.

        Returns:
            Dict with keys:
                - is_good_deal: bool
                - confidence_score: float (0-100)
                - reasons: List[str]
                - warnings: List[str]
                - deal_quality: str ('excellent', 'good', 'fair', 'poor', 'bad')
        """
        reasons = []
        warnings = []
        score = 50.0  # Start with neutral score

        # Check for red flags first
        red_flags = self._check_red_flags(listing)
        if red_flags:
            return {
                'is_good_deal': False,
                'confidence_score': 10.0,
                'reasons': [],
                'warnings': red_flags,
                'deal_quality': 'bad',
                'price_analysis': self._analyze_price(listing)
            }

        # Analyze price
        price_analysis = self._analyze_price(listing)
        score += price_analysis['score_adjustment']
        reasons.extend(price_analysis['reasons'])
        warnings.extend(price_analysis['warnings'])

        # Analyze condition keywords
        condition_analysis = self._analyze_condition(listing)
        score += condition_analysis['score_adjustment']
        reasons.extend(condition_analysis['reasons'])

        # Analyze title/description quality
        quality_analysis = self._analyze_quality(listing)
        score += quality_analysis['score_adjustment']
        reasons.extend(quality_analysis['reasons'])
        warnings.extend(quality_analysis['warnings'])

        # Determine deal quality
        score = max(0, min(100, score))  # Clamp between 0-100

        if score >= 80:
            deal_quality = 'excellent'
            is_good_deal = True
        elif score >= 65:
            deal_quality = 'good'
            is_good_deal = True
        elif score >= 50:
            deal_quality = 'fair'
            is_good_deal = False
        elif score >= 30:
            deal_quality = 'poor'
            is_good_deal = False
        else:
            deal_quality = 'bad'
            is_good_deal = False

        return {
            'is_good_deal': is_good_deal,
            'confidence_score': score,
            'reasons': reasons,
            'warnings': warnings,
            'deal_quality': deal_quality,
            'price_analysis': price_analysis
        }

    def _check_red_flags(self, listing: Listing) -> List[str]:
        """Check for red flag keywords."""
        red_flags = []
        text = f"{listing.title} {listing.description}".lower()

        for keyword in self.red_flag_keywords:
            if keyword in text:
                red_flags.append(f"Red flag: '{keyword}' found in listing")

        # Check for suspiciously low prices
        if listing.price > 0 and self.market_price:
            if listing.price < self.market_price * 0.2:
                red_flags.append("Price is suspiciously low (< 20% of market value) - possible scam")

        return red_flags

    def _analyze_price(self, listing: Listing) -> Dict:
        """Analyze the listing price."""
        analysis = {
            'score_adjustment': 0,
            'reasons': [],
            'warnings': [],
            'price_ratio': None,
            'savings': None
        }

        if listing.price <= 0:
            analysis['warnings'].append("Price not specified or listed as free")
            analysis['score_adjustment'] = -10
            return analysis

        if self.market_price and self.market_price > 0:
            price_ratio = listing.price / self.market_price
            savings = self.market_price - listing.price
            savings_percent = ((self.market_price - listing.price) / self.market_price) * 100

            analysis['price_ratio'] = price_ratio
            analysis['savings'] = savings

            if price_ratio <= self.price_threshold:
                discount = (1 - price_ratio) * 100
                analysis['score_adjustment'] = 30
                analysis['reasons'].append(
                    f"Excellent price: {discount:.1f}% below market value (${savings:.2f} savings)"
                )
            elif price_ratio <= 0.85:
                discount = (1 - price_ratio) * 100
                analysis['score_adjustment'] = 20
                analysis['reasons'].append(
                    f"Good price: {discount:.1f}% below market value (${savings:.2f} savings)"
                )
            elif price_ratio <= 1.0:
                discount = (1 - price_ratio) * 100
                analysis['score_adjustment'] = 10
                analysis['reasons'].append(
                    f"Fair price: {discount:.1f}% below market value (${savings:.2f} savings)"
                )
            elif price_ratio <= 1.15:
                overprice = (price_ratio - 1) * 100
                analysis['score_adjustment'] = -10
                analysis['warnings'].append(
                    f"Slightly overpriced: {overprice:.1f}% above market value"
                )
            else:
                overprice = (price_ratio - 1) * 100
                analysis['score_adjustment'] = -25
                analysis['warnings'].append(
                    f"Overpriced: {overprice:.1f}% above market value"
                )

        return analysis

    def _analyze_condition(self, listing: Listing) -> Dict:
        """Analyze condition keywords in title and description."""
        analysis = {
            'score_adjustment': 0,
            'reasons': []
        }

        text = f"{listing.title} {listing.description}".lower()

        # Check for good condition keywords
        good_matches = [kw for kw in self.good_condition_keywords if kw in text]
        if good_matches:
            analysis['score_adjustment'] = 15
            analysis['reasons'].append(
                f"Excellent condition: mentions '{good_matches[0]}'"
            )

        # Check for bad condition keywords
        bad_matches = [kw for kw in self.bad_condition_keywords if kw in text]
        if bad_matches:
            analysis['score_adjustment'] = -20
            analysis['reasons'].append(
                f"Poor condition: mentions '{bad_matches[0]}'"
            )

        return analysis

    def _analyze_quality(self, listing: Listing) -> Dict:
        """Analyze the quality of the listing itself."""
        analysis = {
            'score_adjustment': 0,
            'reasons': [],
            'warnings': []
        }

        # Check if title is too short or too generic
        if len(listing.title) < 10:
            analysis['score_adjustment'] = -5
            analysis['warnings'].append("Very short title - may lack details")

        # Check if description exists
        if listing.description and len(listing.description) > 50:
            analysis['score_adjustment'] = 5
            analysis['reasons'].append("Detailed description provided")

        # Check if image exists
        if listing.image_url:
            analysis['score_adjustment'] = 5
            analysis['reasons'].append("Image available")

        # Check for all caps (often indicates spam)
        if listing.title.isupper() and len(listing.title) > 5:
            analysis['score_adjustment'] = -10
            analysis['warnings'].append("Title is all caps - may be spam")

        return analysis

    def set_market_price(self, price: float):
        """Set the market price for comparison."""
        self.market_price = price

    def estimate_market_price(self, listings: List[Listing]) -> Optional[float]:
        """
        Estimate market price from a list of listings using statistical analysis.

        Returns the median price, filtering out outliers.
        """
        if not listings:
            return None

        prices = [l.price for l in listings if l.price > 0]

        if not prices:
            return None

        # Remove outliers using IQR method
        prices.sort()
        n = len(prices)

        if n < 3:
            return sum(prices) / n

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
