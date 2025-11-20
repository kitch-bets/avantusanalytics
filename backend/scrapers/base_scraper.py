"""
Base scraper class for sportsbook odds scraping
"""
import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for sportsbook scrapers"""

    def __init__(self, user_agent: str = None):
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.cache = {}
        self.cache_duration = 300  # 5 minutes

    @property
    @abstractmethod
    def sportsbook_name(self) -> str:
        """Return the name of the sportsbook"""
        pass

    @abstractmethod
    def scrape_nfl_games(self) -> List[Dict]:
        """
        Scrape NFL game odds from the sportsbook

        Returns:
            List of dictionaries containing game odds data
        """
        pass

    def get_page(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            BeautifulSoup object or None if request fails
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                logger.info(f"Returning cached data for {key}")
                return data
        return None

    def set_cached_data(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = (data, time.time())

    def format_odds(self, odds: str) -> int:
        """
        Convert odds string to American odds integer

        Args:
            odds: Odds string (e.g., "-110", "+150")

        Returns:
            Integer odds value
        """
        try:
            return int(odds.replace('+', '').replace('−', '-'))
        except (ValueError, AttributeError):
            return 0

    def calculate_implied_probability(self, american_odds: int) -> float:
        """
        Calculate implied probability from American odds

        Args:
            american_odds: American odds (e.g., -110, +150)

        Returns:
            Implied probability as a percentage
        """
        if american_odds < 0:
            return abs(american_odds) / (abs(american_odds) + 100) * 100
        else:
            return 100 / (american_odds + 100) * 100
