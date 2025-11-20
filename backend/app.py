"""
Avantus Analytics - NFL Odds Scraper API
Flask application serving real-time NFL odds from multiple sportsbooks
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv

from services.odds_api_service import OddsAPIService
from scrapers import DraftKingsScraper, FanDuelScraper, BetMGMScraper, CaesarsScraper

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize services
odds_api_service = OddsAPIService()


@app.route('/')
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'Avantus Analytics - NFL Odds API',
        'version': '1.0.0',
        'description': 'Real-time NFL odds from popular sportsbooks',
        'endpoints': {
            '/api/odds/nfl': 'Get all NFL game odds',
            '/api/odds/nfl/<event_id>': 'Get specific game odds',
            '/api/odds/compare': 'Compare odds across sportsbooks',
            '/api/sportsbooks': 'List available sportsbooks',
            '/api/health': 'API health check',
        }
    })


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    api_configured = bool(os.getenv('ODDS_API_KEY'))

    return jsonify({
        'status': 'healthy',
        'api_configured': api_configured,
        'message': 'API is running' if api_configured else 'API key not configured - set ODDS_API_KEY'
    })


@app.route('/api/odds/nfl', methods=['GET'])
def get_nfl_odds():
    """
    Get NFL game odds from all sportsbooks

    Query parameters:
        - markets: Comma-separated list (h2h,spreads,totals)
        - bookmakers: Comma-separated list of sportsbook keys
    """
    try:
        # Parse query parameters
        markets_param = request.args.get('markets', 'h2h,spreads,totals')
        markets = markets_param.split(',')

        bookmakers_param = request.args.get('bookmakers')
        bookmakers = bookmakers_param.split(',') if bookmakers_param else None

        # Fetch odds from The Odds API
        result = odds_api_service.get_nfl_odds(
            markets=markets,
            sportsbooks=bookmakers
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in get_nfl_odds: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/odds/nfl/<event_id>', methods=['GET'])
def get_event_odds(event_id):
    """Get odds for a specific NFL event"""
    try:
        result = odds_api_service.get_nfl_event_odds(event_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_event_odds: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/odds/compare', methods=['GET'])
def compare_odds():
    """
    Compare odds across multiple sportsbooks to find the best lines

    Query parameters:
        - home_team: Home team name
        - away_team: Away team name
    """
    try:
        home_team = request.args.get('home_team')
        away_team = request.args.get('away_team')

        # Get all odds
        all_odds = odds_api_service.get_nfl_odds()

        if 'error' in all_odds:
            return jsonify(all_odds), 400

        # Find the specific game
        game = None
        for g in all_odds.get('games', []):
            if home_team and g['home_team'] == home_team:
                game = g
                break
            elif away_team and g['away_team'] == away_team:
                game = g
                break

        if not game:
            return jsonify({
                'error': 'Game not found',
                'home_team': home_team,
                'away_team': away_team
            }), 404

        # Compare odds across bookmakers
        comparison = _compare_bookmaker_odds(game)

        return jsonify(comparison)

    except Exception as e:
        logger.error(f"Error in compare_odds: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sportsbooks', methods=['GET'])
def get_sportsbooks():
    """Get list of available sportsbooks"""
    sportsbooks = [
        {'key': 'draftkings', 'name': 'DraftKings'},
        {'key': 'fanduel', 'name': 'FanDuel'},
        {'key': 'betmgm', 'name': 'BetMGM'},
        {'key': 'caesars', 'name': 'Caesars'},
        {'key': 'pointsbetus', 'name': 'PointsBet'},
        {'key': 'bovada', 'name': 'Bovada'},
        {'key': 'mybookieag', 'name': 'MyBookie'},
        {'key': 'betus', 'name': 'BetUS'},
    ]

    return jsonify({
        'sportsbooks': sportsbooks,
        'count': len(sportsbooks)
    })


@app.route('/api/scrape/draftkings', methods=['GET'])
def scrape_draftkings():
    """Scrape DraftKings (fallback method)"""
    try:
        scraper = DraftKingsScraper()
        games = scraper.scrape_nfl_games()
        return jsonify({'sportsbook': 'DraftKings', 'games': games})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/fanduel', methods=['GET'])
def scrape_fanduel():
    """Scrape FanDuel (fallback method)"""
    try:
        scraper = FanDuelScraper()
        games = scraper.scrape_nfl_games()
        return jsonify({'sportsbook': 'FanDuel', 'games': games})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/betmgm', methods=['GET'])
def scrape_betmgm():
    """Scrape BetMGM (fallback method)"""
    try:
        scraper = BetMGMScraper()
        games = scraper.scrape_nfl_games()
        return jsonify({'sportsbook': 'BetMGM', 'games': games})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/caesars', methods=['GET'])
def scrape_caesars():
    """Scrape Caesars (fallback method)"""
    try:
        scraper = CaesarsScraper()
        games = scraper.scrape_nfl_games()
        return jsonify({'sportsbook': 'Caesars', 'games': games})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _compare_bookmaker_odds(game: dict) -> dict:
    """
    Compare odds across bookmakers for a game

    Args:
        game: Game data with multiple bookmakers

    Returns:
        Comparison dictionary with best odds for each market
    """
    comparison = {
        'game': {
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'commence_time': game['commence_time']
        },
        'best_odds': {
            'moneyline': {'home': None, 'away': None},
            'spread': {'home': None, 'away': None},
            'total': {'over': None, 'under': None}
        }
    }

    # Find best moneyline odds
    for bookmaker in game.get('bookmakers', []):
        h2h = bookmaker['markets'].get('h2h', {})

        # Home moneyline
        if game['home_team'] in h2h:
            price = h2h[game['home_team']].get('price')
            if price and (not comparison['best_odds']['moneyline']['home'] or
                         price > comparison['best_odds']['moneyline']['home']['price']):
                comparison['best_odds']['moneyline']['home'] = {
                    'bookmaker': bookmaker['title'],
                    'price': price
                }

        # Away moneyline
        if game['away_team'] in h2h:
            price = h2h[game['away_team']].get('price')
            if price and (not comparison['best_odds']['moneyline']['away'] or
                         price > comparison['best_odds']['moneyline']['away']['price']):
                comparison['best_odds']['moneyline']['away'] = {
                    'bookmaker': bookmaker['title'],
                    'price': price
                }

    # Similar logic for spreads and totals would go here...

    return comparison


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'

    logger.info(f"Starting Avantus Analytics API on port {port}")
    logger.info(f"Debug mode: {debug}")

    if not os.getenv('ODDS_API_KEY'):
        logger.warning("⚠️  ODDS_API_KEY not set! Get a free API key at https://the-odds-api.com/")
        logger.warning("⚠️  Set it in .env file or environment variable")

    app.run(host='0.0.0.0', port=port, debug=debug)
