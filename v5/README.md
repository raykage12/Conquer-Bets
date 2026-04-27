# Conquer Bets Flask Prototype

This version improves the previous Flask prototype by making the output easier to read and more useful for users.

## Improvements
- Displays recent point totals as formatted chips instead of a raw array
- Adds summary statistics: average, median, min, max, and standard deviation
- Adds decision explanations for over and under recommendations
- Improves webpage layout and readability
- Adds a simple "Running analysis..." button state while the form submits

## How to run
1. Install dependencies:
   `pip install -r requirements.txt`
2. Start the app:
   `python app.py`
3. Open the local Flask URL in your browser.

## Input
- Player name
- Spread
- Over odds
- Under odds

## Output
- Recent formatted point totals
- Summary statistics
- Over/under probability
- Confidence intervals
- Expected value
- Kelly bet size
- Betting decision and explanation
