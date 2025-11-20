"""
Caesars sportsbook scraper
"""
from typing import Dict, List, Optional
import logging
import json
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CaesarsScraper(BaseScraper):
    """Scraper for Caesars sportsbook odds"""

    BASE_URL = "https://sportsbook.caesars.com"
    NFL_URL = f"{BASE_URL}/us/nfl"

    @property
    def sportsbook_name(self) -> str:
        return "Caesars"

    def scrape_nfl_games(self) -> List[Dict]:
        """
        Scrape NFL game odds from Caesars

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

            # Caesars uses JavaScript rendering
            script_tags = soup.find_all('script')

            for script in script_tags:
                if script.string and ('__NEXT_DATA__' in script.string or 'window.__' in script.string):
                    try:
                        json_str = script.string
                        if '__NEXT_DATA__' in json_str:
                            json_str = json_str.split('__NEXT_DATA__')[1].split('</script>')[0].strip(' =;')
                        data = json.loads(json_str)
                        games.extend(self._parse_games_from_json(data))
                    except Exception as e:
                        logger.debug(f"Could not parse script: {e}")

            # Fallback to HTML
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
                # Navigate Caesars data structure
                props = data.get('props', {})
                page_props = props.get('pageProps', {})
                events = page_props.get('events', [])

                for event in events:
                    game = {
                        'sportsbook': self.sportsbook_name,
                        'away_team': event.get('awayCompetitor', {}).get('name', 'Unknown'),
                        'home_team': event.get('homeCompetitor', {}).get('name', 'Unknown'),
                        'start_time': event.get('startTime'),
                        'spread': self._extract_spread_from_event(event),
                        'total': self._extract_total_from_event(event),
                        'moneyline': self._extract_moneyline_from_event(event),
                    }
                    games.append(game)
        except Exception as e:
            logger.debug(f"Error parsing Caesars JSON: {e}")
        return games

    def _parse_games_from_html(self, soup) -> List[Dict]:
        """Parse games from HTML"""
        games = []

        game_containers = soup.find_all('div', class_=['event-item', 'game-line'])

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
        """Extract spread from event"""
        return {'away': {'line': 0, 'odds': 0}, 'home': {'line': 0, 'odds': 0}}

    def _extract_total_from_event(self, event: Dict) -> Dict:
        """Extract total from event"""
        return {'over': {'line': 0, 'odds': 0}, 'under': {'line': 0, 'odds': 0}}

    def _extract_moneyline_from_event(self, event: Dict) -> Dict:
        """Extract moneyline from event"""
        return {'away': 0, 'home': 0}
