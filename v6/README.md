# Conquer Bets Flask Prototype

This version focuses on final-week polish and interpretability for the Conquer Bets capstone project.

## Final Week Improvements
- Adds a clear model probability vs. sportsbook implied probability comparison
- Adds edge percentage and edge strength labels: No Edge, Weak Edge, Moderate Edge, Strong Edge
- Adds simple confidence interval visualization with model and implied probability markers
- Adds model insight explanations that explain why the output is useful
- Improves final UI formatting for presentation/demo readiness

## Previous Improvements
- Displays recent point totals as formatted chips instead of a raw array
- Adds summary statistics: average, median, min, max, and standard deviation
- Adds decision explanations for over and under recommendations
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
- Model probability vs. implied probability
- Edge percentage and edge strength
- Confidence interval visual range
- Expected value
- Kelly bet size
- Betting decision and explanation
