#!/usr/bin/env python3
"""
Test script for Avantus Analytics NFL Odds Scraper
Demonstrates how to use the odds API service
"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.odds_api_service import OddsAPIService
from scrapers import DraftKingsScraper, FanDuelScraper, BetMGMScraper, CaesarsScraper

# Load environment variables
load_dotenv()


def test_odds_api():
    """Test The Odds API service"""
    print("=" * 60)
    print("Testing Odds API Service")
    print("=" * 60)

    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        print("⚠️  Warning: ODDS_API_KEY not set!")
        print("Get a free API key at: https://the-odds-api.com/")
        print("Set it in .env file as: ODDS_API_KEY=your_key_here")
        print()
        return

    service = OddsAPIService(api_key)

    print("\n1. Fetching available sports...")
    sports = service.get_available_sports()
    if sports:
        print(f"Found {len(sports)} sports")
        nfl = [s for s in sports if 'nfl' in s.get('key', '').lower()]
        if nfl:
            print(f"NFL Sport: {nfl[0]}")
    print()

    print("2. Fetching NFL odds...")
    odds = service.get_nfl_odds(markets=['h2h', 'spreads', 'totals'])

    if 'error' in odds:
        print(f"❌ Error: {odds['error']}")
        return

    print(f"✅ Successfully fetched odds for {odds.get('count', 0)} games")
    print()

    # Display first game details
    if odds.get('games'):
        game = odds['games'][0]
        print("Sample Game Data:")
        print(f"  {game['away_team']} @ {game['home_team']}")
        print(f"  Game ID: {game['id']}")
        print(f"  Start Time: {game['commence_time']}")
        print(f"  Bookmakers: {len(game.get('bookmakers', []))}")

        if game.get('bookmakers'):
            bookmaker = game['bookmakers'][0]
            print(f"\n  Sample Bookmaker: {bookmaker['title']}")
            print(f"  Markets: {list(bookmaker.get('markets', {}).keys())}")

            # Show moneyline if available
            if 'h2h' in bookmaker['markets']:
                print(f"\n  Moneyline Odds:")
                for team, odds_data in bookmaker['markets']['h2h'].items():
                    print(f"    {team}: {odds_data.get('price')}")

    print()
    print("=" * 60)


def test_scrapers():
    """Test individual sportsbook scrapers"""
    print("=" * 60)
    print("Testing Individual Scrapers (Fallback Method)")
    print("=" * 60)
    print()

    scrapers = [
        ('DraftKings', DraftKingsScraper()),
        ('FanDuel', FanDuelScraper()),
        ('BetMGM', BetMGMScraper()),
        ('Caesars', CaesarsScraper()),
    ]

    for name, scraper in scrapers:
        print(f"Testing {name} scraper...")
        try:
            games = scraper.scrape_nfl_games()
            print(f"  ✅ Found {len(games)} games")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()

    print("=" * 60)
    print("\nNote: Web scraping is unreliable due to anti-bot measures.")
    print("For production use, The Odds API is recommended.")
    print("=" * 60)


def display_odds_comparison(odds_data):
    """Display a comparison of odds across sportsbooks"""
    print("\n" + "=" * 60)
    print("NFL Odds Comparison")
    print("=" * 60)

    if not odds_data.get('games'):
        print("No games available")
        return

    for game in odds_data['games'][:3]:  # Show first 3 games
        print(f"\n{game['away_team']} @ {game['home_team']}")
        print(f"Start: {game['commence_time']}")
        print("-" * 60)

        # Compare moneyline across bookmakers
        print("\nMoneyline Odds:")
        print(f"{'Sportsbook':<20} {'Away':<15} {'Home':<15}")
        print("-" * 60)

        for bookmaker in game.get('bookmakers', [])[:5]:  # Show first 5 books
            h2h = bookmaker['markets'].get('h2h', {})
            away_odds = h2h.get(game['away_team'], {}).get('price', 'N/A')
            home_odds = h2h.get(game['home_team'], {}).get('price', 'N/A')

            print(f"{bookmaker['title']:<20} {str(away_odds):<15} {str(home_odds):<15}")

        print()


def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Avantus Analytics - NFL Odds Scraper Test Suite       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Test Odds API (primary method)
    test_odds_api()

    # Optionally test scrapers (fallback method)
    choice = input("\nTest individual scrapers? (y/n): ").lower()
    if choice == 'y':
        test_scrapers()

    print("\n✨ Testing complete!")
    print("\nTo run the API server:")
    print("  python backend/app.py")
    print("\nAPI will be available at: http://localhost:5000")
    print()


if __name__ == '__main__':
    main()
