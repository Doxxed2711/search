# Marketplace Deal Scraper

An intelligent marketplace scraper that continuously monitors **Facebook Marketplace**, **OfferUp**, and **Craigslist** for specific items and uses AI-powered analysis to filter good deals from bad deals.

## Features

- 🔍 **Multi-Platform Scraping**: Monitors Craigslist, OfferUp, and Facebook Marketplace
- 🤖 **AI-Powered Deal Analysis**: Uses intelligent algorithms to identify good deals based on:
  - Price comparison against market value
  - Condition keywords analysis
  - Listing quality assessment
  - Scam/red flag detection
- 🔔 **Smart Notifications**: Desktop notifications and console alerts for good deals
- 💾 **Duplicate Detection**: SQLite database tracks seen listings to avoid duplicates
- ⚙️ **Customizable**: Interactive setup for search terms, price thresholds, and scan intervals
- 📊 **Auto Price Detection**: Automatically estimates market price from listings if not specified
- 🎯 **Quality Scoring**: Rates each deal as excellent/good/fair/poor/bad with confidence scores

## Installation

### 1. Clone or Download

```bash
git clone <your-repo-url>
cd search
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Platform-specific notifications** are installed automatically based on your OS:
- Windows: `win10toast`
- macOS: `pync`
- Linux: `notify2`

### 3. Optional: Better Facebook Scraping

Facebook has strong anti-scraping measures. For better results, you can install Selenium:

```bash
pip install selenium webdriver-manager
```

Note: This requires Chrome/Chromium browser installed on your system.

## Quick Start

### Interactive Setup (Recommended for First Time)

```bash
python marketplace_scraper.py --setup
```

This will guide you through configuring:
- What item to search for
- Expected market price (optional, auto-detects if not provided)
- What discount percentage makes a "good deal"
- Geographic location (for Craigslist)
- How often to check for new listings
- Which marketplaces to search

### Run with Default Settings

```bash
python marketplace_scraper.py
```

### Run Once (Single Scan)

```bash
python marketplace_scraper.py --once
```

## Configuration

The scraper uses a `config.json` file for settings. You can either:
1. Use `--setup` flag for interactive configuration
2. Manually edit `config.json`

### Example Configuration

```json
{
  "search_query": "macbook pro",
  "location": {
    "craigslist": "sfbay",
    "offerup": "",
    "facebook": ""
  },
  "market_price": 800.0,
  "price_threshold": 0.7,
  "scan_interval_minutes": 15,
  "enabled_sources": ["craigslist", "offerup", "facebook"],
  "notifications": {
    "desktop": true,
    "sound": false
  },
  "deal_quality_filter": "good"
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `search_query` | Item to search for | "laptop" |
| `market_price` | Expected market price (null = auto-detect) | null |
| `price_threshold` | Ratio for good deals (0.7 = 30% discount) | 0.7 |
| `scan_interval_minutes` | Minutes between scans | 15 |
| `enabled_sources` | List of marketplaces to search | All three |
| `location.craigslist` | Craigslist subdomain (e.g., "sfbay", "newyork") | "sfbay" |
| `notifications.desktop` | Enable desktop notifications | true |
| `notifications.sound` | Enable sound alerts | false |

### Craigslist Location Codes

Find your area code at: https://www.craigslist.org/about/sites

Examples:
- San Francisco Bay Area: `sfbay`
- New York: `newyork`
- Los Angeles: `losangeles`
- Seattle: `seattle`
- Chicago: `chicago`

## How the AI Deal Analyzer Works

The deal analyzer uses a sophisticated scoring system:

### 1. Price Analysis (up to +30 points)
- Compares listing price to market price
- Calculates discount percentage
- Flags suspiciously low prices as potential scams

### 2. Condition Keywords (+15 or -20 points)
- **Good keywords**: "new", "mint", "excellent", "like new", "sealed"
- **Bad keywords**: "broken", "damaged", "for parts", "not working"

### 3. Listing Quality (+5 points each)
- Has detailed description
- Has images
- Proper capitalization (all caps = spam flag)

### 4. Red Flag Detection (Immediate rejection)
- Scam keywords: "replica", "fake", "financing available"
- Price too low (< 20% of market value)

### Final Score Interpretation
- **80-100**: Excellent deal (buy immediately!)
- **65-79**: Good deal (worth considering)
- **50-64**: Fair deal (at market price)
- **30-49**: Poor deal (overpriced)
- **0-29**: Bad deal (avoid)

## Usage Examples

### Search for a Laptop

```bash
python marketplace_scraper.py --setup
# Enter "laptop" when prompted
# Enter expected price: $500
# Set discount threshold: 30%
```

### Search for Gaming Console

```bash
python marketplace_scraper.py --setup
# Enter "PS5" or "Xbox Series X"
# Enter expected price: $500
# Set discount threshold: 20%
```

### Search for Furniture

```bash
python marketplace_scraper.py --setup
# Enter "leather couch"
# Leave price blank (will auto-detect)
# Set discount threshold: 40%
```

## Output

When good deals are found, you'll see:

```
================================================================================
🎉 FOUND 3 GOOD DEALS!
================================================================================

1. MacBook Pro 2020 M1 - Like New
   💰 Price: $650.00
   📍 Source: Craigslist
   📌 Location: San Francisco
   ⭐ Quality: EXCELLENT (Score: 85.5/100)
   🔗 URL: https://sfbay.craigslist.org/...

2. MacBook Pro 2019 - Excellent Condition
   💰 Price: $550.00
   📍 Source: OfferUp
   ⭐ Quality: GOOD (Score: 72.3/100)
   🔗 URL: https://offerup.com/...
================================================================================
```

## Database

The scraper maintains a SQLite database (`listings.db`) that tracks:
- All seen listings (prevents duplicate notifications)
- Deal quality scores
- Notification status
- First seen / last seen timestamps

### View Database Stats

Stats are logged after each scan cycle:

```
Database stats: {
  'total_listings': 156,
  'good_deals': 12,
  'notified': 12,
  'pending_notifications': 0
}
```

## Logs

All activity is logged to:
- Console (INFO level)
- `scraper.log` file (detailed)

## Troubleshooting

### Facebook Marketplace Returns No Results

Facebook has strong anti-scraping measures:
1. Install Selenium: `pip install selenium webdriver-manager`
2. Install Chrome/Chromium browser
3. Consider using Facebook Graph API for production use

### Desktop Notifications Not Working

Install platform-specific package:
- **Windows**: `pip install win10toast`
- **macOS**: `pip install pync`
- **Linux**: `pip install notify2` (requires `libnotify`)

### No Listings Found

1. Check your internet connection
2. Verify search query is specific enough
3. Try different Craigslist location code
4. Check `scraper.log` for detailed errors

### Too Many False Positives

Adjust in `config.json`:
- Increase `price_threshold` (e.g., 0.6 = 40% discount required)
- Set more accurate `market_price`
- Change `deal_quality_filter` to "excellent"

## Advanced Features

### Custom Scan Schedule

Edit `config.json` to change scan frequency:

```json
{
  "scan_interval_minutes": 30  // Check every 30 minutes
}
```

### Disable Specific Marketplaces

```json
{
  "enabled_sources": ["craigslist"]  // Only Craigslist
}
```

### Auto-Price Detection

Leave `market_price` as `null` to automatically estimate from listings:

```json
{
  "market_price": null  // Will analyze prices and estimate median
}
```

## Project Structure

```
search/
├── marketplace_scraper.py    # Main script
├── config.py                 # Configuration management
├── deal_analyzer.py          # AI deal analysis engine
├── database.py               # SQLite database wrapper
├── notifier.py               # Notification system
├── scrapers/
│   ├── __init__.py
│   ├── base.py              # Base scraper class
│   ├── craigslist.py        # Craigslist scraper
│   ├── offerup.py           # OfferUp scraper
│   └── facebook.py          # Facebook Marketplace scraper
├── config.json              # Configuration file
├── listings.db              # SQLite database
├── scraper.log              # Log file
└── requirements.txt         # Dependencies
```

## Limitations

1. **Facebook Marketplace**: Limited success without Selenium due to JavaScript rendering
2. **Rate Limiting**: Marketplaces may block requests if scraped too frequently
3. **Structure Changes**: Websites may change HTML structure, breaking scrapers
4. **Geographic Restrictions**: Some marketplaces require specific locations

## Legal & Ethical Considerations

- ⚠️ **Check Terms of Service**: Web scraping may violate website ToS
- 🤝 **Be Respectful**: Don't overwhelm servers (use reasonable scan intervals)
- 📜 **For Personal Use**: This tool is intended for personal deal finding
- 🔒 **No Authentication**: Doesn't handle login/authentication (by design)

## Future Enhancements

Potential improvements:
- [ ] Selenium integration for better Facebook scraping
- [ ] Email notifications
- [ ] SMS/text message alerts
- [ ] Web dashboard for viewing deals
- [ ] Machine learning for better deal prediction
- [ ] More marketplaces (eBay, Mercari, etc.)
- [ ] Price history tracking
- [ ] Deal recommendations based on user preferences

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational and personal use only. Always respect website terms of service and use responsibly. The developers are not responsible for any misuse of this software.

---

**Happy Deal Hunting!** 🎉
