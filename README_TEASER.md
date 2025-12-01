# NFL Teaser Builder - LSX Analytics

A quantitative sports betting tool for finding profitable NFL teaser opportunities using strict mathematical filters and live odds integration.

## What is a Teaser?

A teaser is a parlay where you adjust each spread by 6 points in your favor. For example:
- Patriots -8.5 becomes Patriots -2.5
- Browns +2.0 becomes Browns +8.0

**The key insight:** Teasers are ONLY profitable when they cross the key numbers 3 and 7.

## Core Strategy (Non-Negotiable Rules)

This application implements a proven, empirically back-tested teaser strategy:

### 1. Only Tease These Lines

- **Favorites -7.5 to -8.5** → Tease down to -1.5 to -2.5 (crosses 7 and 3)
- **Underdogs +1.5 to +2.5** → Tease up to +7.5 to +8.5 (crosses 3 and 7)

### 2. Additional Filters

- ✅ Game total must be ≤48 (ideally <45)
- ✅ Model probability must be ≥69% to beat breakeven
- ✅ Market must be moving in your direction
- ❌ Never tease large favorites (e.g., -12.5 to -6.5)
- ❌ Never tease totals (except rare weather-affected unders)

### 3. Profit Model

- **Breakeven:** 73% win rate on each leg for a 2-team -120 teaser
- **Target:** 75%+ win rate per leg
- **Edge:** Small but real, compounds over time

**Example:**
- Two legs at 75% each = 56.25% chance both hit
- True odds: +128
- Books offer: -120
- **Result: Positive expected value**

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get a Free API Key

1. Visit [The Odds API](https://the-odds-api.com/)
2. Sign up for a free account
3. Copy your API key (500 free calls/month)

### 3. Run the Application

```bash
python lsx_teaser_gui.py
```

## Usage Guide

### Step 1: Fetch Live Odds

1. Paste your API key in the "API Key" field
2. (Optional) Select a specific bookmaker (DraftKings, FanDuel, etc.)
3. Click **"Fetch NFL Odds"**
4. The table will populate with current NFL spreads and totals

### Step 2: Run LSX Filters

1. Click **"Run LSX Filters"**
2. The app will analyze each game and identify qualifying teaser legs
3. Qualified legs will show **"YES"** in green
4. Non-qualified legs will show **"NO"** in red with reasons why they failed

### Step 3: Calculate Expected Value

1. Select exactly **2 qualified legs** (green rows) in the table
2. Click **"Compute EV"**
3. The app shows:
   - Combined win probability
   - Expected value per unit risked
   - Your edge vs. breakeven
   - Whether the teaser is +EV or -EV

### Step 4: Manual Entry (Optional)

If you want to add games manually or test custom scenarios:

1. Fill in the "Manual Game Entry" fields
2. Click **"Add/Update Game"**
3. Run filters and calculate EV as above

## Understanding the Output

### Table Columns

| Column | Meaning |
|--------|---------|
| **Game/Matchup** | Team @ Opponent |
| **Spread** | Original spread (negative = favorite) |
| **Total** | Game total (over/under) |
| **Win Prob** | Your model's probability at the teased line |
| **Market** | ✓ = line movement in your favor |
| **Type** | "favorite" or "dog" |
| **Teased Line** | The adjusted spread after 6-point tease |
| **Qualifies** | YES/NO based on LSX filters |
| **Analysis** | Why it passed or failed |

### EV Calculation

- **Positive EV (green):** Expected profit over time ✓
- **Negative EV (red):** Expected loss over time ✗
- **Breakeven (orange):** No edge

**You only want to bet teasers with positive EV.**

## Example Workflow

Let's say you fetch odds and see:

```
Chiefs -8.0 @ Bengals (Total: 46.5)
Browns +2.0 vs Steelers (Total: 44.0)
```

**After running LSX filters:**

1. Chiefs -8.0 → Teases to -2.0 ✓
   - Crosses 7 and 3
   - Total under 48 ✓
   - Qualifies: YES

2. Browns +2.0 → Teases to +8.0 ✓
   - Crosses 3 and 7
   - Total under 48 ✓
   - Qualifies: YES

**Select both, compute EV:**

```
Leg 1: Chiefs (75% win prob)
Leg 2: Browns (76% win prob)
Combined: 57% chance both hit
Breakeven at -120: 54.5%
Edge: +2.5%
EV: +0.048 units

Verdict: POSITIVE EV ✓
```

**This is a bet worth making.**

## Customization

### Update Model Probabilities

The default win probability is **75%**. To use your own model:

**Option 1:** Manually update after importing
1. Double-click a game in the manual entry
2. Enter your custom probability
3. Click "Add/Update Game"

**Option 2:** Integrate your model
- Edit the `fetch_odds()` function in `lsx_teaser_gui.py`
- Replace `prob = 0.75` with your model's output
- Could be based on EPA, QBCI, power ratings, etc.

### Adjust Teaser Odds

Default is **-120** (standard 2-team teaser).

To change:
1. Update the "Teaser Odds" field (e.g., -115, -130)
2. The EV calculation will automatically adjust

## API Usage Limits

**Free tier:** 500 calls/month

**Each "Fetch NFL Odds" uses 1 call.**

The app shows remaining calls in the UI.

**Tips to conserve calls:**
- Only fetch once per day (lines don't change that fast)
- Use manual entry for custom scenarios
- Upgrade to paid tier if needed ($5-15/month)

## Important Notes

### This is NOT Gambling Advice

This tool is for:
- ✅ Educational purposes
- ✅ Quantitative analysis
- ✅ Understanding betting math
- ❌ Not financial advice
- ❌ Not a guarantee of profit

### Variance is Real

Even with +EV bets:
- Short-term losses are expected
- You need 25-50 bets minimum to evaluate performance
- Never bet more than you can afford to lose
- Track ROI over a rolling sample

### Bookmaker Limits

If you consistently win:
- Books may limit your account
- Sharp books (Pinnacle, Circa) are more tolerant
- Recreational books (DraftKings, FanDuel) limit faster

## Troubleshooting

### "API Key Required" error
- Make sure you pasted your key correctly
- Key should be 30+ characters long
- Try clicking the "Show" checkbox to verify

### "Unauthorized (401)" error
- Your API key is invalid or expired
- Generate a new key at the-odds-api.com

### "Rate Limited (429)" error
- You've exceeded your 500 calls/month
- Wait until next month or upgrade

### No games showing after fetch
- NFL season might be over
- Check that you selected the right sport
- Try a different bookmaker

### All games show "NO" in Qualifies
- The current week might not have any teaser-worthy lines
- This is normal - profitable teasers are rare
- Try adjusting the model probability threshold

## Next Steps

### Advanced Features to Add

1. **Auto-import from your model**
   - Read CSV of projections
   - Auto-map to API odds
   - Calculate probabilities automatically

2. **Historical tracking**
   - Save past teasers to SQLite
   - Track ROI over time
   - Variance analysis

3. **Line shopping**
   - Compare multiple books
   - Find the best teaser odds
   - Arbitrage opportunities

4. **Alerts**
   - Email/SMS when qualified teasers appear
   - Scheduled daily scans

Let me know if you want help implementing any of these!

## Credits

Strategy framework based on:
- Stanford Wong's "Sharp Sports Betting"
- Key number analysis from Pinnacle's trading team
- LSX Analytics quantitative research

## License

MIT License - Use at your own risk

## Support

Questions? Issues? Create a GitHub issue or contact the development team.

---

**Remember:** The house always has an edge in the long run. This tool helps you find the rare spots where you might have a mathematical edge. Bet responsibly.
