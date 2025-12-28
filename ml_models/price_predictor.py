"""Machine Learning Price Predictor with User Feedback Training."""

import os
import pickle
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PricePredictor:
    """
    ML-based price predictor that learns from user feedback.

    Uses a combination of:
    1. Feature engineering (condition, age, keywords)
    2. User feedback (thumbs up/down on deals)
    3. Online learning to adapt over time
    """

    def __init__(self, model_path: str = "ml_models/price_model.pkl"):
        self.model_path = model_path
        self.feedback_path = "ml_models/feedback_data.json"
        self.model = None
        self.feature_stats = {
            'mean': {},
            'std': {}
        }
        self.feedback_data = []

        # Load existing model or initialize new one
        self._load_or_initialize()

    def _load_or_initialize(self):
        """Load existing model or initialize a new one."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.feature_stats = data.get('feature_stats', self.feature_stats)
                logger.info("Loaded existing ML model")
            except Exception as e:
                logger.warning(f"Error loading model: {e}. Initializing new model.")
                self._initialize_model()
        else:
            self._initialize_model()

        # Load feedback data
        if os.path.exists(self.feedback_path):
            try:
                with open(self.feedback_path, 'r') as f:
                    self.feedback_data = json.load(f)
                logger.info(f"Loaded {len(self.feedback_data)} feedback samples")
            except Exception as e:
                logger.warning(f"Error loading feedback: {e}")

    def _initialize_model(self):
        """Initialize a new model with default parameters."""
        # Using a simple weighted scoring system initially
        # Will evolve as user provides feedback
        self.model = {
            'type': 'weighted_scoring',
            'weights': {
                'price_ratio': 0.4,
                'condition_score': 0.25,
                'listing_quality': 0.15,
                'keyword_score': 0.15,
                'user_feedback': 0.05
            },
            'thresholds': {
                'excellent': 0.80,
                'good': 0.65,
                'fair': 0.50,
                'poor': 0.30
            }
        }
        logger.info("Initialized new ML model")

    def extract_features(self, listing_data: Dict) -> Dict[str, float]:
        """
        Extract features from a listing for prediction.

        Args:
            listing_data: Dict with keys: title, description, price,
                         market_price, image_url, posted_date, etc.

        Returns:
            Feature dictionary
        """
        features = {}

        # Price ratio feature
        price = listing_data.get('price', 0)
        market_price = listing_data.get('market_price', price)

        if market_price > 0:
            features['price_ratio'] = price / market_price
        else:
            features['price_ratio'] = 1.0

        # Condition keywords
        text = f"{listing_data.get('title', '')} {listing_data.get('description', '')}".lower()

        good_keywords = ['new', 'mint', 'excellent', 'perfect', 'unused', 'sealed',
                        'like new', 'pristine', 'barely used']
        bad_keywords = ['broken', 'damaged', 'cracked', 'scratched', 'worn',
                       'defective', 'not working', 'for parts']

        good_count = sum(1 for kw in good_keywords if kw in text)
        bad_count = sum(1 for kw in bad_keywords if kw in text)

        features['condition_score'] = max(0, min(1, (good_count - bad_count + 2) / 4))

        # Listing quality
        quality_score = 0.5
        if listing_data.get('description') and len(listing_data['description']) > 50:
            quality_score += 0.2
        if listing_data.get('image_url'):
            quality_score += 0.2
        if listing_data.get('title') and not listing_data['title'].isupper():
            quality_score += 0.1

        features['listing_quality'] = min(1.0, quality_score)

        # Keyword relevance score
        important_keywords = listing_data.get('search_keywords', [])
        if important_keywords:
            keyword_matches = sum(1 for kw in important_keywords if kw.lower() in text)
            features['keyword_score'] = min(1.0, keyword_matches / len(important_keywords))
        else:
            features['keyword_score'] = 0.5

        # User feedback score (starts at neutral)
        features['user_feedback'] = 0.5

        return features

    def predict_deal_quality(self, listing_data: Dict) -> Dict:
        """
        Predict if a listing is a good deal.

        Returns:
            Dict with keys: score, quality, is_good_deal, confidence
        """
        features = self.extract_features(listing_data)

        # Calculate weighted score
        weights = self.model['weights']
        score = sum(features.get(key, 0.5) * weight
                   for key, weight in weights.items())

        # Normalize to 0-100
        score = score * 100

        # Determine quality
        thresholds = self.model['thresholds']
        if score >= thresholds['excellent'] * 100:
            quality = 'excellent'
            is_good_deal = True
        elif score >= thresholds['good'] * 100:
            quality = 'good'
            is_good_deal = True
        elif score >= thresholds['fair'] * 100:
            quality = 'fair'
            is_good_deal = False
        elif score >= thresholds['poor'] * 100:
            quality = 'poor'
            is_good_deal = False
        else:
            quality = 'bad'
            is_good_deal = False

        # Calculate confidence based on feature completeness
        feature_count = len([v for v in features.values() if v != 0.5])
        confidence = min(100, 50 + (feature_count * 10))

        return {
            'score': score,
            'quality': quality,
            'is_good_deal': is_good_deal,
            'confidence': confidence,
            'features': features
        }

    def add_feedback(self, listing_data: Dict, is_good_deal: bool,
                    user_rating: float = None):
        """
        Add user feedback to train the model.

        Args:
            listing_data: The listing that was rated
            is_good_deal: User's thumbs up (True) or down (False)
            user_rating: Optional 1-5 star rating
        """
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'listing': {
                'title': listing_data.get('title'),
                'price': listing_data.get('price'),
                'market_price': listing_data.get('market_price'),
                'url': listing_data.get('url')
            },
            'features': self.extract_features(listing_data),
            'user_feedback': {
                'is_good_deal': is_good_deal,
                'rating': user_rating
            }
        }

        self.feedback_data.append(feedback_entry)

        # Save feedback
        self._save_feedback()

        # Retrain model if we have enough feedback
        if len(self.feedback_data) >= 10:
            self.retrain_model()

        logger.info(f"Added feedback for: {listing_data.get('title')} - "
                   f"Good deal: {is_good_deal}")

    def retrain_model(self):
        """Retrain the model based on accumulated feedback."""
        if len(self.feedback_data) < 5:
            logger.info("Not enough feedback data to retrain")
            return

        logger.info(f"Retraining model with {len(self.feedback_data)} feedback samples")

        # Analyze feedback to adjust weights and thresholds
        good_deals = [f for f in self.feedback_data
                     if f['user_feedback']['is_good_deal']]
        bad_deals = [f for f in self.feedback_data
                    if not f['user_feedback']['is_good_deal']]

        # Adjust thresholds based on feedback
        if good_deals:
            good_scores = []
            for deal in good_deals:
                features = deal['features']
                weights = self.model['weights']
                score = sum(features.get(key, 0.5) * weight
                          for key, weight in weights.items())
                good_scores.append(score)

            # Lower threshold to include more deals users marked as good
            avg_good_score = np.mean(good_scores) if good_scores else 0.65
            self.model['thresholds']['good'] = max(0.5, avg_good_score - 0.05)
            self.model['thresholds']['excellent'] = max(0.7, avg_good_score + 0.1)

        if bad_deals and good_deals:
            # Analyze which features differentiate good from bad
            for feature_name in ['price_ratio', 'condition_score', 'listing_quality', 'keyword_score']:
                good_values = [d['features'].get(feature_name, 0.5) for d in good_deals]
                bad_values = [d['features'].get(feature_name, 0.5) for d in bad_deals]

                # Calculate feature importance (simple approach)
                good_avg = np.mean(good_values)
                bad_avg = np.mean(bad_values)
                importance = abs(good_avg - bad_avg)

                # Adjust weight based on importance
                current_weight = self.model['weights'][feature_name]
                adjustment = importance * 0.1

                if good_avg > bad_avg:
                    self.model['weights'][feature_name] = min(0.6, current_weight + adjustment)
                else:
                    self.model['weights'][feature_name] = max(0.1, current_weight - adjustment)

        # Normalize weights to sum to 1.0
        total_weight = sum(self.model['weights'].values())
        for key in self.model['weights']:
            self.model['weights'][key] /= total_weight

        # Save updated model
        self._save_model()

        logger.info(f"Model retrained. New weights: {self.model['weights']}")
        logger.info(f"New thresholds: {self.model['thresholds']}")

    def _save_model(self):
        """Save the model to disk."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_stats': self.feature_stats
                }, f)
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _save_feedback(self):
        """Save feedback data to disk."""
        try:
            os.makedirs(os.path.dirname(self.feedback_path), exist_ok=True)
            with open(self.feedback_path, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")

    def get_stats(self) -> Dict:
        """Get model statistics."""
        total_feedback = len(self.feedback_data)
        good_feedback = sum(1 for f in self.feedback_data
                          if f['user_feedback']['is_good_deal'])

        return {
            'total_feedback': total_feedback,
            'good_deals_marked': good_feedback,
            'bad_deals_marked': total_feedback - good_feedback,
            'model_weights': self.model['weights'],
            'model_thresholds': self.model['thresholds']
        }
