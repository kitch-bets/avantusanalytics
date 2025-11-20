"""
FanDuel sportsbook scraper
"""
from typing import Dict, List, Optional
import logging
import json
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FanDuelScraper(BaseScraper):
    """Scraper for FanDuel sportsbook odds"""

    BASE_URL = "https://sportsbook.fanduel.com"
    NFL_URL = f"{BASE_URL}/navigation/nfl"

    @property
    def sportsbook_name(self) -> str:
        return "FanDuel"

    def scrape_nfl_games(self) -> List[Dict]:
        """
        Scrape NFL game odds from FanDuel

        Returns:
            List of game odds dictionaries
        """
        cached = self.get_cached_data('nfl_games')
        if cached:
            return cached

        logger.info(f"Scraping {self.sportsbook_name} NFL odds...")

        try:
            soup = self.get_page(self.NFL_URL)
            if not soup:
                logger.error(f"Failed to fetch {self.sportsbook_name} page")
                return []

            games = []

            # FanDuel also uses JavaScript-heavy rendering
            script_tags = soup.find_all('script')

            for script in script_tags:
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    try:
                        # Extract initial state data
                        json_str = script.string.split('window.__INITIAL_STATE__=')[1].split(';</script>')[0]
                        data = json.loads(json_str)
                        games.extend(self._parse_games_from_json(data))
                    except Exception as e:
                        logger.debug(f"Could not parse initial state: {e}")

            # Fallback to HTML parsing
            if not games:
                games = self._parse_games_from_html(soup)

            self.set_cached_data('nfl_games', games)
            logger.info(f"Found {len(games)} games from {self.sportsbook_name}")
            return games

        except Exception as e:
            logger.error(f"Error scraping {self.sportsbook_name}: {e}")
            return []

    def _parse_games_from_json(self, data: Dict) -> List[Dict]:
        """Parse games from JSON data"""
        games = []
        try:
            # Navigate the FanDuel data structure
            # This is a template - actual structure varies
            events = data.get('events', {})
            for event_id, event in events.items():
                game = {
                    'sportsbook': self.sportsbook_name,
                    'game_id': event_id,
                    'away_team': event.get('awayTeamName', 'Unknown'),
                    'home_team': event.get('homeTeamName', 'Unknown'),
                    'start_time': event.get('openDate'),
                    'spread': self._extract_spread_from_event(event),
                    'total': self._extract_total_from_event(event),
                    'moneyline': self._extract_moneyline_from_event(event),
                }
                games.append(game)
        except Exception as e:
            logger.debug(f"Error parsing FanDuel JSON: {e}")
        return games

    def _parse_games_from_html(self, soup) -> List[Dict]:
        """Parse games from HTML"""
        games = []

        # FanDuel HTML structure template
        game_containers = soup.find_all('div', {'aria-label': lambda x: x and 'vs' in str(x).lower()})

        for container in game_containers[:10]:
            try:
                game = {
                    'sportsbook': self.sportsbook_name,
                    'away_team': '',
                    'home_team': '',
                    'spread': {'away': {'line': 0, 'odds': 0}, 'home': {'line': 0, 'odds': 0}},
                    'total': {'over': {'line': 0, 'odds': 0}, 'under': {'line': 0, 'odds': 0}},
                    'moneyline': {'away': 0, 'home': 0},
                }
                games.append(game)
            except Exception as e:
                logger.debug(f"Error parsing game: {e}")

        return games

    def _extract_spread_from_event(self, event: Dict) -> Dict:
        """Extract spread from event data"""
        return {'away': {'line': 0, 'odds': 0}, 'home': {'line': 0, 'odds': 0}}

    def _extract_total_from_event(self, event: Dict) -> Dict:
        """Extract total from event data"""
        return {'over': {'line': 0, 'odds': 0}, 'under': {'line': 0, 'odds': 0}}

    def _extract_moneyline_from_event(self, event: Dict) -> Dict:
        """Extract moneyline from event data"""
        return {'away': 0, 'home': 0}
