"""
Odds API Service - Primary data source for sportsbook odds
Uses The Odds API (https://the-odds-api.com/) for reliable, real-time odds data
"""
import requests
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OddsAPIService:
    """Service for fetching odds from The Odds API"""

    BASE_URL = "https://api.the-odds-api.com/v4"

    # Popular US sportsbooks available via The Odds API
    SPORTSBOOKS = [
        'draftkings',
        'fanduel',
        'betmgm',
        'caesars',
        'pointsbetus',
        'bovada',
        'mybookieag',
        'betus',
        'lowvig',
        'williamhill_us',
    ]

    def __init__(self, api_key: str = None):
        """
        Initialize the Odds API service

        Args:
            api_key: The Odds API key (get free key at https://the-odds-api.com/)
        """
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        if not self.api_key:
            logger.warning("No Odds API key provided. Set ODDS_API_KEY environment variable.")

        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        self.session = requests.Session()

    def get_nfl_odds(
        self,
        markets: List[str] = None,
        sportsbooks: List[str] = None,
        regions: str = 'us'
    ) -> Dict:
        """
        Get NFL odds from The Odds API

        Args:
            markets: List of markets to fetch (e.g., ['h2h', 'spreads', 'totals'])
            sportsbooks: List of sportsbooks to include (defaults to all)
            regions: Region for odds (default: 'us')

        Returns:
            Dictionary with odds data
        """
        if not self.api_key:
            logger.error("Cannot fetch odds without API key")
            return {'error': 'No API key configured', 'games': []}

        # Default markets: moneyline (h2h), spreads, totals
        if markets is None:
            markets = ['h2h', 'spreads', 'totals']

        # Check cache
        cache_key = f"nfl_odds_{','.join(markets)}"
        cached = self._get_cached_data(cache_key)
        if cached:
            return cached

        try:
            # Construct API endpoint
            url = f"{self.BASE_URL}/sports/americanfootball_nfl/odds"

            params = {
                'apiKey': self.api_key,
                'regions': regions,
                'markets': ','.join(markets),
                'oddsFormat': 'american',
                'dateFormat': 'iso',
            }

            # Add sportsbook filter if specified
            if sportsbooks:
                params['bookmakers'] = ','.join(sportsbooks)

            logger.info("Fetching NFL odds from The Odds API...")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Check remaining API requests
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            logger.info(f"API requests - Used: {used}, Remaining: {remaining}")

            # Transform data to our format
            result = self._transform_odds_data(data, markets)

            # Cache the result
            self._set_cached_data(cache_key, result)

            return result

        except requests.RequestException as e:
            logger.error(f"Error fetching from Odds API: {e}")
            return {'error': str(e), 'games': []}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {'error': str(e), 'games': []}

    def get_nfl_event_odds(self, event_id: str) -> Dict:
        """
        Get odds for a specific NFL event

        Args:
            event_id: The event ID from The Odds API

        Returns:
            Dictionary with event odds
        """
        if not self.api_key:
            return {'error': 'No API key configured'}

        try:
            url = f"{self.BASE_URL}/sports/americanfootball_nfl/events/{event_id}/odds"

            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american',
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching event odds: {e}")
            return {'error': str(e)}

    def _transform_odds_data(self, data: List[Dict], markets: List[str]) -> Dict:
        """
        Transform Odds API response to our standardized format

        Args:
            data: Raw data from The Odds API
            markets: Markets that were requested

        Returns:
            Transformed odds data
        """
        games = []

        for event in data:
            try:
                game = {
                    'id': event.get('id'),
                    'sport': event.get('sport_key'),
                    'commence_time': event.get('commence_time'),
                    'home_team': event.get('home_team'),
                    'away_team': event.get('away_team'),
                    'bookmakers': []
                }

                # Process each bookmaker
                for bookmaker in event.get('bookmakers', []):
                    book_data = {
                        'key': bookmaker.get('key'),
                        'title': bookmaker.get('title'),
                        'last_update': bookmaker.get('last_update'),
                        'markets': {}
                    }

                    # Process each market
                    for market in bookmaker.get('markets', []):
                        market_key = market.get('key')
                        book_data['markets'][market_key] = self._parse_market(market)

                    game['bookmakers'].append(book_data)

                games.append(game)

            except Exception as e:
                logger.error(f"Error transforming event: {e}")
                continue

        return {
            'games': games,
            'count': len(games),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _parse_market(self, market: Dict) -> Dict:
        """Parse a specific market (h2h, spreads, totals)"""
        market_key = market.get('key')
        outcomes = market.get('outcomes', [])

        if market_key == 'h2h':
            # Moneyline
            result = {}
            for outcome in outcomes:
                result[outcome['name']] = {
                    'price': outcome.get('price'),
                    'point': outcome.get('point')
                }
            return result

        elif market_key == 'spreads':
            # Spread betting
            result = {}
            for outcome in outcomes:
                result[outcome['name']] = {
                    'price': outcome.get('price'),
                    'point': outcome.get('point')
                }
            return result

        elif market_key == 'totals':
            # Over/Under
            result = {}
            for outcome in outcomes:
                result[outcome['name']] = {
                    'price': outcome.get('price'),
                    'point': outcome.get('point')
                }
            return result

        return {}

    def get_available_sports(self) -> List[Dict]:
        """Get list of available sports from The Odds API"""
        if not self.api_key:
            return []

        try:
            url = f"{self.BASE_URL}/sports"
            params = {'apiKey': self.api_key}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching sports: {e}")
            return []

    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                logger.info(f"Returning cached data for {key}")
                return data
        return None

    def _set_cached_data(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = (data, datetime.now())
