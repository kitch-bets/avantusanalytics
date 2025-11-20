"""
BetMGM sportsbook scraper
"""
from typing import Dict, List, Optional
import logging
import json
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BetMGMScraper(BaseScraper):
    """Scraper for BetMGM sportsbook odds"""

    BASE_URL = "https://sports.betmgm.com"
    NFL_URL = f"{BASE_URL}/en/sports/football-11/betting/usa-9/nfl-35"

    @property
    def sportsbook_name(self) -> str:
        return "BetMGM"

    def scrape_nfl_games(self) -> List[Dict]:
        """
        Scrape NFL game odds from BetMGM

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

            # BetMGM uses dynamic content loading
            # Look for JSON data in script tags
            script_tags = soup.find_all('script', type='application/json')

            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    games.extend(self._parse_games_from_json(data))
                except Exception as e:
                    logger.debug(f"Could not parse script: {e}")

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
            if isinstance(data, dict):
                # Navigate BetMGM's data structure
                for key, value in data.items():
                    if isinstance(value, dict) and 'fixture' in value:
                        game = self._extract_game_from_fixture(value)
                        if game:
                            games.append(game)
        except Exception as e:
            logger.debug(f"Error parsing BetMGM JSON: {e}")
        return games

    def _parse_games_from_html(self, soup) -> List[Dict]:
        """Parse games from HTML"""
        games = []

        # BetMGM HTML structure template
        game_containers = soup.find_all('div', class_=['grid-event', 'event-row'])

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

    def _extract_game_from_fixture(self, fixture: Dict) -> Optional[Dict]:
        """Extract game data from fixture"""
        try:
            return {
                'sportsbook': self.sportsbook_name,
                'away_team': fixture.get('awayTeam', {}).get('name', 'Unknown'),
                'home_team': fixture.get('homeTeam', {}).get('name', 'Unknown'),
                'start_time': fixture.get('startTime'),
                'spread': {'away': {'line': 0, 'odds': 0}, 'home': {'line': 0, 'odds': 0}},
                'total': {'over': {'line': 0, 'odds': 0}, 'under': {'line': 0, 'odds': 0}},
                'moneyline': {'away': 0, 'home': 0},
            }
        except Exception as e:
            logger.debug(f"Error extracting fixture: {e}")
            return None
