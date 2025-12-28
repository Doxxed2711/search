#!/usr/bin/env python3
"""
Flask API Server for Marketplace Deal Finder

Handles:
- Push notifications to Android app
- User feedback collection
- ML model training
- Deal storage and retrieval
- User location updates
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import sys
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.price_predictor import PricePredictor
from database import ListingDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components
ml_model = PricePredictor()
db = ListingDatabase()

# Store user devices and locations
USERS_FILE = "api/users.json"
users_data = {}


def load_users():
    """Load user data from file."""
    global users_data
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                users_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            users_data = {}


def save_users():
    """Save user data to file."""
    try:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")


# Load users on startup
load_users()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ml_model_stats': ml_model.get_stats()
    })


@app.route('/api/register', methods=['POST'])
def register_device():
    """
    Register a device for push notifications.

    Expected JSON:
    {
        "device_id": "unique_device_id",
        "fcm_token": "firebase_token",
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "city": "San Francisco",
            "craigslist_area": "sfbay"
        }
    }
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        fcm_token = data.get('fcm_token')
        location = data.get('location', {})

        if not device_id or not fcm_token:
            return jsonify({'error': 'device_id and fcm_token required'}), 400

        users_data[device_id] = {
            'fcm_token': fcm_token,
            'location': location,
            'registered_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

        save_users()

        logger.info(f"Registered device: {device_id}")

        return jsonify({
            'status': 'success',
            'message': 'Device registered successfully',
            'device_id': device_id
        })

    except Exception as e:
        logger.error(f"Error registering device: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/update_location', methods=['POST'])
def update_location():
    """
    Update user location.

    Expected JSON:
    {
        "device_id": "unique_device_id",
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "city": "San Francisco",
            "craigslist_area": "sfbay"
        }
    }
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        location = data.get('location')

        if not device_id or not location:
            return jsonify({'error': 'device_id and location required'}), 400

        if device_id not in users_data:
            return jsonify({'error': 'Device not registered'}), 404

        users_data[device_id]['location'] = location
        users_data[device_id]['last_updated'] = datetime.now().isoformat()

        save_users()

        logger.info(f"Updated location for device: {device_id}")

        return jsonify({
            'status': 'success',
            'message': 'Location updated successfully'
        })

    except Exception as e:
        logger.error(f"Error updating location: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback on a deal.

    Expected JSON:
    {
        "device_id": "unique_device_id",
        "listing": {
            "title": "...",
            "price": 500,
            "market_price": 800,
            "url": "...",
            ...
        },
        "is_good_deal": true,
        "rating": 4  // optional 1-5
    }
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        listing = data.get('listing')
        is_good_deal = data.get('is_good_deal')
        rating = data.get('rating')

        if not device_id or listing is None or is_good_deal is None:
            return jsonify({'error': 'Missing required fields'}), 400

        # Add feedback to ML model
        ml_model.add_feedback(listing, is_good_deal, rating)

        logger.info(f"Received feedback from {device_id}: "
                   f"{listing.get('title')} - Good: {is_good_deal}")

        return jsonify({
            'status': 'success',
            'message': 'Feedback received',
            'model_stats': ml_model.get_stats()
        })

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/deals/new', methods=['POST'])
def notify_new_deal():
    """
    Receive a new deal from the scraper and send push notification.

    Expected JSON:
    {
        "deal": {
            "title": "...",
            "price": 500,
            "url": "...",
            "source": "Craigslist",
            "location": "San Francisco",
            "score": 85.5,
            "quality": "excellent"
        }
    }
    """
    try:
        data = request.json
        deal = data.get('deal')

        if not deal:
            return jsonify({'error': 'Deal data required'}), 400

        # Send push notification to all registered devices
        notifications_sent = send_push_notification(deal)

        logger.info(f"Sent {notifications_sent} notifications for: {deal.get('title')}")

        return jsonify({
            'status': 'success',
            'notifications_sent': notifications_sent
        })

    except Exception as e:
        logger.error(f"Error notifying new deal: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/deals', methods=['GET'])
def get_deals():
    """Get all good deals."""
    try:
        device_id = request.args.get('device_id')

        # Get deals from database
        deals = db.get_unnotified_good_deals()

        return jsonify({
            'status': 'success',
            'count': len(deals),
            'deals': deals
        })

    except Exception as e:
        logger.error(f"Error getting deals: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict_deal():
    """
    Predict if a listing is a good deal using ML model.

    Expected JSON:
    {
        "listing": {
            "title": "...",
            "description": "...",
            "price": 500,
            "market_price": 800,
            ...
        }
    }
    """
    try:
        data = request.json
        listing = data.get('listing')

        if not listing:
            return jsonify({'error': 'Listing data required'}), 400

        # Get prediction
        prediction = ml_model.predict_deal_quality(listing)

        return jsonify({
            'status': 'success',
            'prediction': prediction
        })

    except Exception as e:
        logger.error(f"Error predicting deal: {e}")
        return jsonify({'error': str(e)}), 500


def send_push_notification(deal: dict) -> int:
    """
    Send push notification to all registered devices.

    Args:
        deal: Deal information

    Returns:
        Number of notifications sent
    """
    # Import Firebase Admin SDK
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError:
        logger.warning("Firebase Admin SDK not installed. Install with: "
                      "pip install firebase-admin")
        return 0

    # Check if Firebase is initialized
    if not firebase_admin._apps:
        # Try to initialize Firebase
        cred_path = os.environ.get('FIREBASE_CREDENTIALS', 'api/firebase_credentials.json')
        if not os.path.exists(cred_path):
            logger.warning(f"Firebase credentials not found at {cred_path}")
            return 0

        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {e}")
            return 0

    notifications_sent = 0

    for device_id, user_data in users_data.items():
        fcm_token = user_data.get('fcm_token')

        if not fcm_token:
            continue

        try:
            # Create notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Great Deal Found! - {deal.get('quality', '').title()}",
                    body=f"{deal.get('title')} - ${deal.get('price')} ({deal.get('source')})"
                ),
                data={
                    'url': deal.get('url', ''),
                    'title': deal.get('title', ''),
                    'price': str(deal.get('price', 0)),
                    'score': str(deal.get('score', 0)),
                    'quality': deal.get('quality', ''),
                    'source': deal.get('source', ''),
                    'location': deal.get('location', ''),
                    'type': 'new_deal'
                },
                token=fcm_token
            )

            # Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent notification to {device_id}: {response}")
            notifications_sent += 1

        except Exception as e:
            logger.error(f"Error sending notification to {device_id}: {e}")

    return notifications_sent


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
