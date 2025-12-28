# Complete Setup Guide - AI Marketplace Deal Finder

This guide walks you through setting up the complete system with ML training, API backend, and Android app.

## System Architecture

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│  Web Scrapers   │────────▶│  ML Model    │────────▶│   API Server    │
│ (Craigslist,    │         │ (Training &  │         │   (Flask +      │
│  OfferUp, FB)   │         │  Prediction) │         │    Firebase)    │
└─────────────────┘         └──────────────┘         └────────┬────────┘
                                                              │
                                                              │ Push
                                                              │ Notifications
                                                              ▼
                                                       ┌─────────────────┐
                                                       │  Android App    │
                                                       │  (Location +    │
                                                       │   Feedback)     │
                                                       └─────────────────┘
```

## Part 1: Server Setup (Python Backend)

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for cloning)

### Installation

1. **Clone or navigate to the project directory:**

```bash
cd /path/to/search
```

2. **Run the setup script:**

```bash
chmod +x setup_server.sh
./setup_server.sh
```

This will:
- Create a virtual environment
- Install all Python dependencies
- Set up required directories

3. **Configure Firebase (for push notifications):**

   a. Go to [Firebase Console](https://console.firebase.google.com/)

   b. Create a new project (or use existing)

   c. Add an Android app to your project:
      - Package name: `com.marketplace.dealfinder`
      - Download `google-services.json` (needed for Android app)

   d. Go to **Project Settings** → **Service Accounts**

   e. Click **"Generate New Private Key"**

   f. Save the JSON file as `api/firebase_credentials.json`

4. **Configure the scraper:**

```bash
source venv/bin/activate
python marketplace_scraper_ml.py --setup
```

Follow the interactive prompts to configure:
- What item to search for
- Expected market price (or leave blank for auto-detection)
- Discount threshold for "good deals"
- Geographic location
- Scan interval

### Running the System

**Option 1: Run everything together (recommended)**

```bash
chmod +x start_system.sh
./start_system.sh
```

**Option 2: Run components separately**

Terminal 1 - API Server:
```bash
source venv/bin/activate
python api/server.py
```

Terminal 2 - Scraper:
```bash
source venv/bin/activate
python marketplace_scraper_ml.py
```

## Part 2: Android App Setup

### Prerequisites

- Android Studio (latest version)
- Android SDK 24 or higher
- A physical Android device or emulator

### Installation

1. **Open Android Studio**

2. **Open the project:**
   - File → Open
   - Navigate to `/path/to/search/android_app`
   - Click OK

3. **Add Firebase configuration:**

   Copy the `google-services.json` file (from Firebase Console) to:
   ```
   android_app/app/google-services.json
   ```

4. **Update API Server URL:**

   Edit `android_app/app/src/main/java/com/marketplace/dealfinder/api/ApiClient.kt`:

   ```kotlin
   // For testing on physical device, use your computer's IP
   private const val BASE_URL = "http://YOUR_COMPUTER_IP:5000/"

   // For emulator:
   private const val BASE_URL = "http://10.0.2.2:5000/"
   ```

   To find your computer's IP:
   - **macOS/Linux**: `ifconfig | grep inet`
   - **Windows**: `ipconfig`

5. **Build and run:**
   - Connect your Android device (or start emulator)
   - Click "Run" (green play button) in Android Studio
   - Select your device

### Granting Permissions

When you first open the app, grant these permissions:
- **Location**: Required for auto-updating your area
- **Notifications**: Required for deal alerts

## Part 3: How It Works

### ML Training System

1. **Initial State**: The ML model starts with default weights
2. **User Feedback**: When you rate deals (👍/👎), the model learns
3. **Automatic Retraining**: After 10+ feedback samples, the model adjusts
4. **Continuous Improvement**: The more you use it, the better it gets at finding deals you like

### Location-Based Updates

1. App requests location permission
2. GPS tracks your location every 5 minutes
3. Location is geocoded to city name
4. Craigslist area is automatically mapped
5. Server updates scraper configuration
6. Deals are now searched in your current area

### Push Notification Flow

```
1. Scraper finds listing
2. ML model evaluates → Good deal!
3. Send to API server
4. API server → Firebase Cloud Messaging
5. FCM → Your Android phone
6. Notification appears with link
7. Tap to open listing in browser
8. Rate the deal to improve ML model
```

## Testing the System

### 1. Test API Server

```bash
curl http://localhost:5000/health
```

Should return JSON with status and ML model stats.

### 2. Test Scraper

```bash
python marketplace_scraper_ml.py --once
```

Runs a single scrape cycle.

### 3. Test Android App

1. Open app
2. Grant permissions
3. Pull down to refresh
4. Check if deals appear
5. Tap a deal to open details
6. Rate with 👍 or 👎
7. Check Settings to see ML model stats

### 4. Test Push Notifications

With everything running:
1. Wait for scraper to find a good deal
2. Check your Android phone for notification
3. Tap notification to open listing
4. Rate the deal

## Configuration

### config.json

```json
{
  "search_query": "macbook pro",
  "market_price": 800.0,
  "price_threshold": 0.7,
  "scan_interval_minutes": 15,
  "enabled_sources": ["craigslist", "offerup", "facebook"],
  "location": {
    "craigslist": "sfbay",
    "offerup": "",
    "facebook": ""
  },
  "notifications": {
    "desktop": true,
    "sound": false
  }
}
```

**Key Settings:**
- `search_query`: What to search for
- `market_price`: Expected price (null = auto-detect)
- `price_threshold`: 0.7 = 30% discount required
- `scan_interval_minutes`: How often to check

### Environment Variables

```bash
# API Server port
export PORT=5000

# Firebase credentials path
export FIREBASE_CREDENTIALS=api/firebase_credentials.json
```

## Troubleshooting

### API Server Issues

**Problem**: Server won't start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Use different port
PORT=5001 python api/server.py
```

**Problem**: Firebase errors
- Verify `api/firebase_credentials.json` exists
- Check file permissions
- Validate JSON format

### Android App Issues

**Problem**: Can't connect to server
- Check API URL in `ApiClient.kt`
- Verify server is running
- Check firewall settings
- Use computer's IP (not localhost) for physical device

**Problem**: No notifications
- Check Firebase setup
- Verify `google-services.json` is in correct location
- Grant notification permission
- Check FCM token in logs

**Problem**: Location not updating
- Grant location permission
- Check GPS is enabled
- View logs in Android Studio (Logcat)

### Scraper Issues

**Problem**: No listings found
- Check internet connection
- Try different Craigslist area code
- Enable verbose logging in `scraper.log`

**Problem**: Too many false positives
- Increase `price_threshold` in config.json
- Set more accurate `market_price`
- Provide more feedback to train the model

## ML Model Training Tips

### Getting Better Results

1. **Be Consistent**: Rate deals consistently (don't change criteria)
2. **Rate Frequently**: The more feedback, the better
3. **Be Specific**: Search for specific items, not generic terms
4. **Set Accurate Price**: Help the model with correct market price
5. **Wait for Training**: Give it 10-20 ratings before expecting good results

### Checking Model Performance

View stats in:
- Android app Settings screen
- API health endpoint: `http://localhost:5000/health`
- Log files: `scraper.log`

## Advanced Features

### Multiple Search Items

Run multiple instances:

```bash
# Terminal 1: Search for laptops
python marketplace_scraper_ml.py --config laptop_config.json

# Terminal 2: Search for furniture
python marketplace_scraper_ml.py --config furniture_config.json --api-url http://localhost:5000
```

### Custom Craigslist Areas

Edit location mapping in:
`android_app/app/src/main/java/com/marketplace/dealfinder/location/LocationManager.kt`

### Scheduled Running

Use cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# Run every hour
0 * * * * cd /path/to/search && ./start_system.sh
```

## Security Notes

- 🔒 Never commit `firebase_credentials.json` to Git
- 🔒 Don't expose API server to public internet without authentication
- 🔒 Use HTTPS in production
- 🔒 Keep Firebase credentials secure

## Next Steps

1. **Fine-tune the ML model** by rating 20+ deals
2. **Expand location mapping** for your area
3. **Add more marketplaces** (eBay, Mercari, etc.)
4. **Deploy to cloud** for 24/7 operation
5. **Share feedback** to improve the system

## Support

For issues or questions:
- Check `scraper.log` for detailed errors
- Review Android Logcat for app issues
- Verify Firebase setup
- Ensure all dependencies are installed

Happy deal hunting! 🎉
