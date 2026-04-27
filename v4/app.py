from flask import Flask, render_template, request
from v3calculations import Calculations
from v3fetch_players import PlayerLookupError, DataRetrievalError

app = Flask(__name__)

MIN_ODDS = -250
MAX_ODDS = 250
SEASON = "2025-26"
REGULAR_SEASON = "Regular Season"


class InputValidationError(Exception):
    """Raised when web form input is missing or malformed."""


def parse_form(form_data):
    player = form_data.get("player", "").strip()
    spread_raw = form_data.get("spread", "").strip()
    odds_over_raw = form_data.get("odds_over", "").strip()
    odds_under_raw = form_data.get("odds_under", "").strip()

    if not player:
        raise InputValidationError("Player name is required.")

    try:
        spread = float(spread_raw)
    except ValueError as exc:
        raise InputValidationError("Spread must be a number.") from exc

    try:
        odds_over = int(odds_over_raw)
        odds_under = int(odds_under_raw)
    except ValueError as exc:
        raise InputValidationError("Over and under odds must be whole numbers.") from exc

    if odds_over == 0 or odds_under == 0:
        raise InputValidationError("Odds cannot be 0.")

    if not (MIN_ODDS <= odds_over <= MAX_ODDS):
        raise InputValidationError(f"Over odds must be between {MIN_ODDS} and {MAX_ODDS}.")

    if not (MIN_ODDS <= odds_under <= MAX_ODDS):
        raise InputValidationError(f"Under odds must be between {MIN_ODDS} and {MAX_ODDS}.")

    return {
        "player": player,
        "spread": spread,
        "odds_over": odds_over,
        "odds_under": odds_under,
    }


def prepare_results_for_display(results):
    over_lower, over_upper = results["over_ci"]
    under_lower, under_upper = results["under_ci"]

    return {
        "player": results["player"],
        "season": results["season"],
        "spread": results["spread"],
        "odds_over": results["odds_over"],
        "odds_under": results["odds_under"],
        "games": results["games"],
        "points": results["points"],
        "p_over_pct": results["p_over"] * 100,
        "p_under_pct": results["p_under"] * 100,
        "over_ci_lower_pct": over_lower * 100,
        "over_ci_upper_pct": over_upper * 100,
        "under_ci_lower_pct": under_lower * 100,
        "under_ci_upper_pct": under_upper * 100,
        "over_edge_pct": (results["p_over"] - results["over_implied"]) * 100,
        "under_edge_pct": (results["p_under"] - results["under_implied"]) * 100,
        "over_ev": results["over_ev"],
        "under_ev": results["under_ev"],
        "over_kelly_pct": results["over_kelly"] * 100,
        "under_kelly_pct": results["under_kelly"] * 100,
        "decision_over": results["decision_over"],
        "decision_under": results["decision_under"],
    }


@app.route("/", methods=["GET", "POST"])
def index():
    calculator = Calculations()
    error_message = None
    results = None

    form_values = {
        "player": "",
        "spread": "",
        "odds_over": "",
        "odds_under": "",
    }

    if request.method == "POST":
        form_values = {
            "player": request.form.get("player", ""),
            "spread": request.form.get("spread", ""),
            "odds_over": request.form.get("odds_over", ""),
            "odds_under": request.form.get("odds_under", ""),
        }

        try:
            parsed = parse_form(request.form)
            analysis = calculator.analyze_player(
                parsed["player"],
                SEASON,
                REGULAR_SEASON,
                parsed["spread"],
                parsed["odds_over"],
                parsed["odds_under"],
            )
            results = prepare_results_for_display(analysis)
        except InputValidationError as exc:
            error_message = f"Input Error: {exc}"
        except PlayerLookupError as exc:
            error_message = f"Player Error: {exc}"
        except DataRetrievalError as exc:
            error_message = f"API Error: {exc}"
        except Exception as exc:
            error_message = f"Unexpected Error: {exc}"

    return render_template(
        "index.html",
        error_message=error_message,
        results=results,
        form_values=form_values,
        min_odds=MIN_ODDS,
        max_odds=MAX_ODDS,
    )


if __name__ == "__main__":
    app.run(debug=True)
