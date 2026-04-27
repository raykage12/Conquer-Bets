# Conquer Bets Flask Prototype

This is a minimal Flask version of Conquer Bets built on top of the current backend analysis logic.

## Files
- `app.py` - Flask entry point
- `templates/index.html` - single-page form and results display
- `requirements.txt` - Python dependencies

## How to run
1. Install dependencies:
   `pip install -r requirements.txt`
2. Make sure `v3main.py`, `v3calculations.py`, and `v3fetch_players.py` are in the same project folder or importable in your Python path.
3. Start the app:
   `python app.py`
4. Open the local URL shown by Flask in your browser.

## Input
- Player name
- Spread
- Over odds
- Under odds

## Output
- Probability for over and under
- Confidence intervals
- Expected value
- Kelly bet size
- Betting decision
