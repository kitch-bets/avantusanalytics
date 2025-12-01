"""
NFL Teaser Builder - LSX Analytics
Profitable sports betting teaser strategy with live odds integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import requests
from typing import Optional, Dict, List, Tuple


APP_TITLE = "NFL Teaser Builder - LSX Analytics"
API_BASE_URL = "https://api.the-odds-api.com/v4"


def american_to_decimal(odds: int) -> float:
    """
    Convert American odds to decimal multiplier on 1 unit risk.
    Example:
        -120 -> risk 1 to win 0.8333 -> decimal 1.8333
         150 -> risk 1 to win 1.5    -> decimal 2.5
    """
    if odds == 0:
        raise ValueError("Odds cannot be 0")
    if odds < 0:
        return 1 + 100 / abs(odds)
    else:
        return 1 + odds / 100


def break_even_prob(odds: int) -> float:
    """
    Break-even win probability for given American odds.
    """
    dec = american_to_decimal(odds)
    profit = dec - 1
    return 1 / (1 + profit)


def classify_teaser_leg(spread: float, total: float, prob: float, move_with_us: bool) -> Dict:
    """
    Apply the LSX teaser filters to a single leg.

    Core Rules (Non-negotiable):
    1. Only tease NFL spreads
    2. Only tease favorites of -7.5 to -8.5 down to -1.5 to -2.5 (crosses 3 and 7)
    3. Only tease underdogs of +1.5 to +2.5 up to +7.5 to +8.5 (crosses 3 and 7)
    4. Never tease large favorites
    5. Total must be 48 or under (ideally under 45)

    Returns dict with:
        qualifies: bool
        direction: 'favorite' / 'dog' / None
        teased_line: float or None
        reasons: str
    """
    reasons = []
    qualifies = True
    direction = None
    teased_line = None

    # Total check - critical for teaser value
    if total > 48:
        qualifies = False
        reasons.append(f"Total too high ({total:.1f} > 48)")

    # Line movement check
    if not move_with_us:
        qualifies = False
        reasons.append("Market not moving in our favor")

    # Probability check - need 69%+ to beat breakeven
    if prob < 0.69:
        qualifies = False
        reasons.append(f"Model probability too low ({prob:.1%} < 69%)")

    # Spread / key number check - THE MOST IMPORTANT FILTER
    # Must cross both 3 and 7 for maximum value
    if -8.5 <= spread <= -7.5:
        direction = "favorite"
        teased_line = spread + 6  # 6-point teaser
        if not (-2.5 <= teased_line <= -1.5):
            qualifies = False
            reasons.append(f"Teased favorite lands at {teased_line:+.1f}, outside -2.5 to -1.5 range")
    elif 1.5 <= spread <= 2.5:
        direction = "dog"
        teased_line = spread + 6  # 6-point teaser
        if not (7.5 <= teased_line <= 8.5):
            qualifies = False
            reasons.append(f"Teased dog lands at {teased_line:+.1f}, outside +7.5 to +8.5 range")
    else:
        qualifies = False
        reasons.append(f"Spread {spread:+.1f} not in teaser window (-8.5 to -7.5 or +1.5 to +2.5)")

    if direction is None:
        teased_line = None

    if qualifies and not reasons:
        reasons.append("✓ Passes all LSX teaser filters")

    return {
        "qualifies": qualifies,
        "direction": direction,
        "teased_line": teased_line,
        "reasons": "; ".join(reasons)
    }


class TeaserApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1300x700")

        # Set color scheme
        style = ttk.Style()
        style.theme_use('clam')

        self.games = []  # list of game dicts

        self._build_widgets()

    def _build_widgets(self):
        """Build all GUI components"""

        # ===== TOP: API FRAME =====
        api_frame = ttk.LabelFrame(self.root, text="Live NFL Odds (The Odds API)")
        api_frame.pack(fill="x", padx=10, pady=10)

        # API Key input
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_api_key = ttk.Entry(api_frame, width=50, show="*")
        self.entry_api_key.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Toggle show/hide key
        self.show_key_var = tk.BooleanVar(value=False)
        self.chk_show_key = ttk.Checkbutton(
            api_frame,
            text="Show",
            variable=self.show_key_var,
            command=self._toggle_api_key_visibility
        )
        self.chk_show_key.grid(row=0, column=2, padx=5, pady=5)

        # Bookmaker filter
        ttk.Label(api_frame, text="Bookmaker (optional):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_bookmaker = ttk.Combobox(
            api_frame,
            width=30,
            values=["", "DraftKings", "FanDuel", "BetMGM", "Caesars", "PointsBet"]
        )
        self.entry_bookmaker.set("")
        self.entry_bookmaker.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Fetch button
        self.btn_fetch_odds = ttk.Button(
            api_frame,
            text="Fetch NFL Odds",
            command=self.fetch_odds,
            width=20
        )
        self.btn_fetch_odds.grid(row=0, column=3, rowspan=2, padx=10, pady=5, sticky="ns")

        # Usage counter
        self.lbl_api_usage = ttk.Label(api_frame, text="API calls remaining: Unknown")
        self.lbl_api_usage.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)

        api_frame.columnconfigure(1, weight=1)

        # ===== MIDDLE: MANUAL INPUT FRAME =====
        input_frame = ttk.LabelFrame(self.root, text="Manual Game Entry")
        input_frame.pack(fill="x", padx=10, pady=5)

        # Row 0
        ttk.Label(input_frame, text="Game/Matchup:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_game = ttk.Entry(input_frame, width=30)
        self.entry_game.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Spread:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.entry_spread = ttk.Entry(input_frame, width=10)
        self.entry_spread.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="Total:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.entry_total = ttk.Entry(input_frame, width=10)
        self.entry_total.grid(row=0, column=5, padx=5, pady=5)

        # Row 1
        ttk.Label(input_frame, text="Model Win Prob (%):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_prob = ttk.Entry(input_frame, width=10)
        self.entry_prob.insert(0, "75")
        self.entry_prob.grid(row=1, column=1, padx=5, pady=5)

        self.move_var = tk.BooleanVar(value=True)
        self.chk_move = ttk.Checkbutton(
            input_frame,
            text="Market moving in our favor",
            variable=self.move_var
        )
        self.chk_move.grid(row=1, column=2, columnspan=2, sticky="w", padx=5, pady=5)

        ttk.Label(input_frame, text="Teaser Odds:").grid(row=1, column=4, sticky="w", padx=5, pady=5)
        self.entry_odds = ttk.Entry(input_frame, width=10)
        self.entry_odds.insert(0, "-120")
        self.entry_odds.grid(row=1, column=5, padx=5, pady=5)

        # Row 2 - Buttons
        self.btn_add = ttk.Button(input_frame, text="Add/Update Game", command=self.add_game)
        self.btn_add.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.btn_clear = ttk.Button(input_frame, text="Clear Inputs", command=self.clear_inputs)
        self.btn_clear.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.btn_filter = ttk.Button(input_frame, text="Run LSX Filters", command=self.run_filters)
        self.btn_filter.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        self.btn_clear_all = ttk.Button(input_frame, text="Clear All Games", command=self.clear_all_games)
        self.btn_clear_all.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        # ===== TABLE FRAME =====
        table_frame = ttk.LabelFrame(self.root, text="Teaser Candidates")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create table
        columns = ("game", "spread", "total", "prob", "move", "direction", "teased", "qualifies", "reasons")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        # Configure columns
        self.tree.heading("game", text="Game/Matchup")
        self.tree.heading("spread", text="Spread")
        self.tree.heading("total", text="Total")
        self.tree.heading("prob", text="Win Prob")
        self.tree.heading("move", text="Market")
        self.tree.heading("direction", text="Type")
        self.tree.heading("teased", text="Teased Line")
        self.tree.heading("qualifies", text="Qualifies")
        self.tree.heading("reasons", text="Analysis")

        self.tree.column("game", width=220)
        self.tree.column("spread", width=70, anchor="center")
        self.tree.column("total", width=70, anchor="center")
        self.tree.column("prob", width=90, anchor="center")
        self.tree.column("move", width=80, anchor="center")
        self.tree.column("direction", width=80, anchor="center")
        self.tree.column("teased", width=90, anchor="center")
        self.tree.column("qualifies", width=80, anchor="center")
        self.tree.column("reasons", width=450, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # ===== BOTTOM: EV CALCULATOR =====
        ev_frame = ttk.LabelFrame(self.root, text="2-Leg Teaser EV Calculator")
        ev_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            ev_frame,
            text="Select exactly 2 qualified legs above, then:"
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        self.btn_ev = ttk.Button(ev_frame, text="Compute EV", command=self.compute_ev, width=15)
        self.btn_ev.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.lbl_ev = ttk.Label(ev_frame, text="EV: Not calculated", foreground="blue")
        self.lbl_ev.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.lbl_breakeven = ttk.Label(ev_frame, text="Break-even: Not calculated")
        self.lbl_breakeven.grid(row=1, column=2, padx=5, pady=5, sticky="w")

    def _toggle_api_key_visibility(self):
        """Show or hide API key"""
        if self.show_key_var.get():
            self.entry_api_key.config(show="")
        else:
            self.entry_api_key.config(show="*")

    def clear_inputs(self):
        """Clear manual input fields"""
        self.entry_game.delete(0, tk.END)
        self.entry_spread.delete(0, tk.END)
        self.entry_total.delete(0, tk.END)
        self.entry_prob.delete(0, tk.END)
        self.entry_prob.insert(0, "75")
        self.move_var.set(True)

    def clear_all_games(self):
        """Clear all games from the list"""
        if messagebox.askyesno("Clear All", "Remove all games from the list?"):
            self.games = []
            self.refresh_table()

    def add_game(self):
        """Add or update a game manually"""
        try:
            game = self.entry_game.get().strip()
            if not game:
                raise ValueError("Game ID/matchup is required")

            spread = float(self.entry_spread.get())
            total = float(self.entry_total.get())
            prob_pct = float(self.entry_prob.get())
            prob = prob_pct / 100.0
            move_with_us = bool(self.move_var.get())

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return

        game_dict = {
            "game": game,
            "spread": spread,
            "total": total,
            "prob": prob,
            "move_with_us": move_with_us,
            "direction": None,
            "teased_line": None,
            "qualifies": False,
            "reasons": "Not yet filtered"
        }

        # Update if exists, else append
        for idx, g in enumerate(self.games):
            if g["game"] == game:
                self.games[idx] = game_dict
                break
        else:
            self.games.append(game_dict)

        self.refresh_table()
        messagebox.showinfo("Success", f"Game '{game}' added/updated")

    def refresh_table(self):
        """Refresh the treeview table"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Re-populate
        for g in self.games:
            prob_pct = g["prob"] * 100
            move_text = "✓" if g["move_with_us"] else "✗"
            teased = f"{g['teased_line']:+.1f}" if g["teased_line"] is not None else "-"
            qualifies_text = "YES" if g["qualifies"] else "NO"

            # Color code qualified rows
            tags = ("qualified",) if g["qualifies"] else ("not_qualified",)

            self.tree.insert(
                "",
                tk.END,
                values=(
                    g["game"],
                    f"{g['spread']:+.1f}",
                    f"{g['total']:.1f}",
                    f"{prob_pct:.1f}%",
                    move_text,
                    g["direction"] or "-",
                    teased,
                    qualifies_text,
                    g["reasons"]
                ),
                tags=tags
            )

        # Tag colors
        self.tree.tag_configure("qualified", background="#d4edda")
        self.tree.tag_configure("not_qualified", background="#f8d7da")

    def run_filters(self):
        """Apply LSX teaser filters to all games"""
        if not self.games:
            messagebox.showwarning("No Games", "Add some games first")
            return

        for idx, g in enumerate(self.games):
            result = classify_teaser_leg(
                spread=g["spread"],
                total=g["total"],
                prob=g["prob"],
                move_with_us=g["move_with_us"]
            )
            self.games[idx]["direction"] = result["direction"]
            self.games[idx]["teased_line"] = result["teased_line"]
            self.games[idx]["qualifies"] = result["qualifies"]
            self.games[idx]["reasons"] = result["reasons"]

        self.refresh_table()

        qualified_count = sum(1 for g in self.games if g["qualifies"])
        messagebox.showinfo(
            "Filters Complete",
            f"Found {qualified_count} qualified teaser legs out of {len(self.games)} total"
        )

    def fetch_odds(self):
        """
        Fetch live NFL odds from The Odds API
        """
        # Get and validate API key
        api_key_raw = self.entry_api_key.get()
        api_key = api_key_raw.strip()

        # Debug output
        print(f"[DEBUG] API key length: {len(api_key)}")
        print(f"[DEBUG] API key first 10 chars: {api_key[:10] if len(api_key) >= 10 else api_key}")

        if not api_key or len(api_key) < 10:
            messagebox.showerror(
                "API Key Required",
                "Please enter your API key from The Odds API.\n\n"
                "Get a free key at: https://the-odds-api.com/"
            )
            return

        bookmaker_filter = self.entry_bookmaker.get().strip() or None

        # API request
        url = f"{API_BASE_URL}/sports/americanfootball_nfl/odds"
        params = {
            "regions": "us",
            "markets": "spreads,totals",
            "oddsFormat": "american",
            "apiKey": api_key
        }

        try:
            print(f"[DEBUG] Fetching from: {url}")
            print(f"[DEBUG] Params: {params}")

            self.btn_fetch_odds.config(state="disabled", text="Fetching...")
            self.root.update()

            resp = requests.get(url, params=params, timeout=15)

            # Check for API errors
            if resp.status_code == 401:
                messagebox.showerror(
                    "Unauthorized",
                    "Invalid API key (401).\n\nCheck that your key is correct and active."
                )
                return
            elif resp.status_code == 429:
                messagebox.showerror(
                    "Rate Limited",
                    "Too many requests (429).\n\nYou've exceeded your API quota."
                )
                return

            resp.raise_for_status()

            # Check remaining requests
            requests_remaining = resp.headers.get('x-requests-remaining', 'Unknown')
            requests_used = resp.headers.get('x-requests-used', 'Unknown')
            self.lbl_api_usage.config(
                text=f"API calls remaining: {requests_remaining} (used: {requests_used})"
            )

        except requests.exceptions.Timeout:
            messagebox.showerror("Timeout", "Request timed out. Check your internet connection.")
            return
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Failed to fetch odds:\n{e}")
            return
        finally:
            self.btn_fetch_odds.config(state="normal", text="Fetch NFL Odds")

        # Parse response
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            messagebox.showerror("Parse Error", f"Could not parse API response:\n{e}")
            return

        if not isinstance(data, list):
            messagebox.showerror("Unexpected Response", f"API returned unexpected format:\n{data}")
            return

        # Process games
        imported = 0
        self.games = []  # Reset list

        for event in data:
            home = event.get("home_team", "HOME")
            away = event.get("away_team", "AWAY")

            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            # Select bookmaker
            chosen_book = None
            if bookmaker_filter:
                for bm in bookmakers:
                    if bm.get("title") == bookmaker_filter:
                        chosen_book = bm
                        break
            if chosen_book is None:
                chosen_book = bookmakers[0]

            markets = chosen_book.get("markets", [])
            spreads_market = None
            totals_market = None

            for m in markets:
                if m.get("key") == "spreads":
                    spreads_market = m
                elif m.get("key") == "totals":
                    totals_market = m

            if spreads_market is None or totals_market is None:
                continue

            # Get total
            total_point = None
            if totals_market.get("outcomes"):
                total_point = totals_market["outcomes"][0].get("point")

            # Create entries for each spread outcome
            for outcome in spreads_market.get("outcomes", []):
                team = outcome.get("name", "Team")
                point = outcome.get("point")
                if point is None:
                    continue

                spread = float(point)
                total_val = float(total_point) if total_point is not None else 47.0

                # Determine matchup label
                if team == home:
                    opponent = away
                    matchup = f"{team} vs {opponent}"
                else:
                    opponent = home
                    matchup = f"{team} @ {opponent}"

                # Default probability - YOU SHOULD UPDATE THIS WITH YOUR MODEL
                prob = 0.75

                game_dict = {
                    "game": matchup,
                    "spread": spread,
                    "total": total_val,
                    "prob": prob,
                    "move_with_us": True,  # Default to true
                    "direction": None,
                    "teased_line": None,
                    "qualifies": False,
                    "reasons": "Imported from API - run LSX filters"
                }

                self.games.append(game_dict)
                imported += 1

        self.refresh_table()

        messagebox.showinfo(
            "Import Complete",
            f"Imported {imported} spread legs from {len(data)} games.\n\n"
            f"Next: Click 'Run LSX Filters' to find qualifying teasers."
        )

    def compute_ev(self):
        """Calculate expected value for a 2-leg teaser"""
        # Get teaser odds
        try:
            odds = int(self.entry_odds.get())
            dec = american_to_decimal(odds)
            profit_per_unit = dec - 1.0
            be = break_even_prob(odds)
        except Exception as e:
            messagebox.showerror("Invalid Odds", f"Could not parse teaser odds: {e}")
            return

        # Get selected legs
        selected = self.tree.selection()
        if len(selected) != 2:
            messagebox.showwarning("Selection Error", "Please select exactly 2 legs in the table")
            return

        probs = []
        games_chosen = []

        for item in selected:
            values = self.tree.item(item, "values")
            game_name = values[0]
            prob_str = values[3]  # e.g., "75.0%"
            qualifies_str = values[7]

            if qualifies_str != "YES":
                messagebox.showwarning(
                    "Invalid Selection",
                    f"Game '{game_name}' is not a qualified teaser leg.\n\n"
                    "Only select games with 'YES' in the Qualifies column."
                )
                return

            try:
                p = float(prob_str.strip('%')) / 100.0
            except ValueError:
                messagebox.showerror("Data Error", f"Could not parse probability for '{game_name}'")
                return

            probs.append(p)
            games_chosen.append(game_name)

        # Calculate EV
        p_win = probs[0] * probs[1]
        ev = p_win * profit_per_unit - (1 - p_win) * 1.0

        # Determine if it's +EV
        if ev > 0:
            ev_color = "green"
            ev_verdict = "POSITIVE EV ✓"
        elif ev == 0:
            ev_color = "orange"
            ev_verdict = "BREAKEVEN"
        else:
            ev_color = "red"
            ev_verdict = "NEGATIVE EV ✗"

        self.lbl_ev.config(
            text=f"EV: {ev:+.4f} units ({ev_verdict}) | Win Prob: {p_win:.2%}",
            foreground=ev_color
        )

        self.lbl_breakeven.config(
            text=f"Break-even at {odds:+d}: {be:.2%} | Your edge: {p_win - be:+.2%}"
        )

        # Show detailed popup
        messagebox.showinfo(
            "Teaser EV Analysis",
            f"2-Leg Teaser at {odds:+d}\n\n"
            f"Leg 1: {games_chosen[0]} ({probs[0]:.1%})\n"
            f"Leg 2: {games_chosen[1]} ({probs[1]:.1%})\n\n"
            f"Combined Win Probability: {p_win:.2%}\n"
            f"Break-even Probability: {be:.2%}\n"
            f"Edge: {p_win - be:+.2%}\n\n"
            f"Expected Value: {ev:+.4f} units per 1 unit risked\n\n"
            f"Verdict: {ev_verdict}"
        )


def main():
    root = tk.Tk()
    app = TeaserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
