"""
Sportsbook scrapers package
"""
from .base_scraper import BaseScraper
from .draftkings_scraper import DraftKingsScraper
from .fanduel_scraper import FanDuelScraper
from .betmgm_scraper import BetMGMScraper
from .caesars_scraper import CaesarsScraper

__all__ = [
    'BaseScraper',
    'DraftKingsScraper',
    'FanDuelScraper',
    'BetMGMScraper',
    'CaesarsScraper',
]
