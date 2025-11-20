# Avantus Analytics - NFL Odds Scraper

Real-time NFL odds aggregation from popular sportsbooks including DraftKings, FanDuel, BetMGM, and Caesars.

## Features

- **Real-time NFL Odds**: Fetch current odds for all NFL games
- **Multiple Sportsbooks**: Support for 8+ major US sportsbooks
- **Multiple Markets**: Moneyline, spreads, and totals
- **Odds Comparison**: Find the best lines across all books
- **RESTful API**: Easy-to-use Flask API endpoints
- **Caching**: Built-in caching to reduce API calls
- **Fallback Scrapers**: Direct web scraping as backup

## Supported Sportsbooks

- DraftKings
- FanDuel
- BetMGM
- Caesars
- PointsBet
- Bovada
- MyBookie
- BetUS

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Get API Key

Get a free API key from [The Odds API](https://the-odds-api.com/):
- Free tier: 500 requests/month
- No credit card required

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API key
ODDS_API_KEY=your_api_key_here
```

### 4. Run the API Server

```bash
python backend/app.py
```

Server will start at `http://localhost:5000`

### 5. Test the Scraper

```bash
python test_scraper.py
```

## API Endpoints

### Get All NFL Odds

```bash
GET /api/odds/nfl
```

**Query Parameters:**
- `markets`: Comma-separated list (h2h, spreads, totals)
- `bookmakers`: Comma-separated list of sportsbook keys

**Example:**
```bash
curl "http://localhost:5000/api/odds/nfl?markets=h2h,spreads&bookmakers=draftkings,fanduel"
```

**Response:**
```json
{
  "games": [
    {
      "id": "abc123",
      "home_team": "Kansas City Chiefs",
      "away_team": "Buffalo Bills",
      "commence_time": "2025-11-24T01:20:00Z",
      "bookmakers": [
        {
          "key": "draftkings",
          "title": "DraftKings",
          "markets": {
            "h2h": {
              "Kansas City Chiefs": {"price": -140},
              "Buffalo Bills": {"price": 120}
            },
            "spreads": {
              "Kansas City Chiefs": {"point": -2.5, "price": -110},
              "Buffalo Bills": {"point": 2.5, "price": -110}
            }
          }
        }
      ]
    }
  ],
  "count": 15,
  "timestamp": "2025-11-20T12:00:00"
}
```

### Get Specific Game Odds

```bash
GET /api/odds/nfl/<event_id>
```

### Compare Odds Across Books

```bash
GET /api/odds/compare?home_team=Kansas%20City%20Chiefs
```

### List Available Sportsbooks

```bash
GET /api/sportsbooks
```

### Health Check

```bash
GET /api/health
```

## Usage Examples

### Python

```python
import requests

# Get all NFL odds
response = requests.get('http://localhost:5000/api/odds/nfl')
odds_data = response.json()

for game in odds_data['games']:
    print(f"{game['away_team']} @ {game['home_team']}")

    for bookmaker in game['bookmakers']:
        print(f"  {bookmaker['title']}")
        if 'h2h' in bookmaker['markets']:
            for team, odds in bookmaker['markets']['h2h'].items():
                print(f"    {team}: {odds['price']}")
```

### JavaScript/Fetch

```javascript
fetch('http://localhost:5000/api/odds/nfl')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.count} games`);
    data.games.forEach(game => {
      console.log(`${game.away_team} @ ${game.home_team}`);
    });
  });
```

### cURL

```bash
# Get all odds
curl http://localhost:5000/api/odds/nfl | jq

# Get specific markets
curl "http://localhost:5000/api/odds/nfl?markets=spreads" | jq

# Get specific bookmakers
curl "http://localhost:5000/api/odds/nfl?bookmakers=draftkings,fanduel" | jq
```

## Architecture

```
avantusanalytics/
├── backend/
│   ├── app.py                  # Flask API server
│   ├── scrapers/               # Individual sportsbook scrapers
│   │   ├── base_scraper.py
│   │   ├── draftkings_scraper.py
│   │   ├── fanduel_scraper.py
│   │   ├── betmgm_scraper.py
│   │   └── caesars_scraper.py
│   └── services/
│       └── odds_api_service.py # The Odds API integration
├── index.html                  # Frontend betting picks page
├── requirements.txt
├── .env.example
└── test_scraper.py            # Test/demo script
```

## Data Flow

1. **Primary Method**: Uses The Odds API for reliable, real-time data
2. **Fallback Method**: Direct web scraping (less reliable, use sparingly)
3. **Caching**: 5-minute cache to reduce API calls
4. **API Response**: Standardized JSON format across all sources

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
ODDS_API_KEY=your_api_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
CACHE_DURATION=300
```

## Rate Limits

The Odds API free tier provides:
- 500 requests/month
- Request tracking via response headers

The API includes caching to minimize requests:
- Default cache: 5 minutes
- Configurable via `CACHE_DURATION`

## Development

### Running in Development

```bash
# Set Flask to development mode
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run the server
python backend/app.py
```

### Adding New Sportsbooks

1. Create a new scraper in `backend/scrapers/`
2. Extend `BaseScraper` class
3. Implement `scrape_nfl_games()` method
4. Add to `backend/scrapers/__init__.py`
5. Add endpoint in `backend/app.py`

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

CMD ["python", "backend/app.py"]
```

## Legal & Compliance

- **Terms of Service**: Respect sportsbook ToS when scraping
- **Rate Limiting**: Implement appropriate delays
- **Educational Use**: This code is for educational purposes
- **Gambling Disclaimer**: Check local gambling laws
- **API Usage**: The Odds API has usage limits and terms

## Troubleshooting

### API Key Issues

```
Error: No API key configured
```
**Solution**: Set `ODDS_API_KEY` in `.env` file

### Import Errors

```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Install dependencies: `pip install -r requirements.txt`

### No Games Returned

```json
{"games": [], "count": 0}
```
**Possible causes**:
- NFL season ended
- API key invalid
- Network issues

## Resources

- [The Odds API Documentation](https://the-odds-api.com/liveapi/guides/v4/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Responsible Gambling](https://www.ncpgambling.org/)

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check The Odds API documentation
- Review Flask documentation

## Roadmap

- [ ] Add player props support
- [ ] Implement historical odds tracking
- [ ] Add odds movement alerts
- [ ] Create dashboard UI
- [ ] Add more sports (NBA, MLB, etc.)
- [ ] Implement arbitrage detection
- [ ] Add database for odds history

---

**Disclaimer**: This software is for educational and informational purposes only. Always gamble responsibly and check your local laws regarding sports betting.
