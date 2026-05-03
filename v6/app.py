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


def get_edge_strength(edge_pct):
    """Classify edge strength using simple percentage thresholds."""
    if edge_pct <= 0:
        return "No Edge"
    if edge_pct >= 5:
        return "Strong Edge"
    if edge_pct >= 2:
        return "Moderate Edge"
    return "Weak Edge"


def get_strength_class(edge_strength):
    """Return a CSS-friendly class based on edge strength."""
    if edge_strength == "Strong Edge":
        return "strong"
    if edge_strength == "Moderate Edge":
        return "moderate"
    if edge_strength == "Weak Edge":
        return "weak"
    return "none"


def build_decision_explanation(side, decision):
    side_label = side.capitalize()

    if "Strong" in decision:
        return (
            f"This is labeled as a stronger {side_label} because the lower confidence "
            f"bound is still above the sportsbook implied probability. This means the "
            f"edge appears more reliable even when uncertainty is considered."
        )

    if "Weak" in decision:
        return (
            f"This is labeled as a weaker {side_label} because the estimated probability "
            f"beats the implied probability, but the confidence interval still overlaps "
            f"the implied probability. The bet may have value, but the estimate is less certain."
        )

    if "No Bet - No EV" in decision:
        return (
            f"This is labeled as no bet because the estimated {side_label} probability "
            f"does not beat the sportsbook implied probability."
        )

    if "Fake Edge" in decision:
        return (
            f"This is labeled as no bet because the edge is not supported strongly enough "
            f"by the confidence interval."
        )

    return (
        f"The {side_label} decision is based on comparing the estimated probability, "
        f"confidence interval, and sportsbook implied probability."
    )


def build_model_insight(side, model_probability, implied_probability, edge_pct, ci_lower, ci_upper, edge_strength):
    side_label = side.capitalize()

    if edge_pct <= 0:
        return (
            f"The model does not show a positive {side_label} edge. The estimated probability "
            f"({model_probability * 100:.2f}%) is not higher than the implied probability "
            f"({implied_probability * 100:.2f}%)."
        )

    if ci_lower > implied_probability:
        return (
            f"The model shows a {edge_strength.lower()} for the {side_label}. The estimated "
            f"probability is {model_probability * 100:.2f}% compared with an implied probability "
            f"of {implied_probability * 100:.2f}%, and the full confidence interval stays above "
            f"the implied probability."
        )

    if ci_lower <= implied_probability <= ci_upper:
        return (
            f"The model shows a possible {Side_label if False else side_label} edge, but uncertainty is present. "
            f"The estimated probability is {model_probability * 100:.2f}% compared with an implied "
            f"probability of {implied_probability * 100:.2f}%, but the confidence interval overlaps "
            f"the implied probability."
        )

    return (
        f"The model probability is higher than the implied probability, but the confidence interval "
        f"does not strongly support the edge. This should be treated carefully."
    )


def get_confidence_bar(ci_lower_pct, ci_upper_pct, model_probability_pct, implied_probability_pct):
    """
    Build simple percentage positions for a visual confidence range.
    Values are clamped to 0-100 for display.
    """
    left = max(0, min(100, ci_lower_pct))
    right = max(0, min(100, ci_upper_pct))
    model_pos = max(0, min(100, model_probability_pct))
    implied_pos = max(0, min(100, implied_probability_pct))
    width = max(1, right - left)

    return {
        "left": left,
        "width": width,
        "model_pos": model_pos,
        "implied_pos": implied_pos,
    }


def prepare_results_for_display(results):
    over_lower, over_upper = results["over_ci"]
    under_lower, under_upper = results["under_ci"]

    points = results["points"]
    recent_points = points[:10]

    p_over_pct = results["p_over"] * 100
    p_under_pct = results["p_under"] * 100
    over_implied_pct = results["over_implied"] * 100
    under_implied_pct = results["under_implied"] * 100
    over_edge_pct = (results["p_over"] - results["over_implied"]) * 100
    under_edge_pct = (results["p_under"] - results["under_implied"]) * 100

    over_edge_strength = get_edge_strength(over_edge_pct)
    under_edge_strength = get_edge_strength(under_edge_pct)

    over_ci_lower_pct = over_lower * 100
    over_ci_upper_pct = over_upper * 100
    under_ci_lower_pct = under_lower * 100
    under_ci_upper_pct = under_upper * 100

    return {
        "player": results["player"],
        "season": results["season"],
        "spread": results["spread"],
        "odds_over": results["odds_over"],
        "odds_under": results["odds_under"],
        "games": results["games"],

        "recent_points": recent_points,
        "points_shown": len(recent_points),
        "points_total": len(points),

        "average_points": results["average_points"],
        "median_points": results["median_points"],
        "min_points": results["min_points"],
        "max_points": results["max_points"],
        "std_dev_points": results["std_dev_points"],

        "p_over_pct": p_over_pct,
        "p_under_pct": p_under_pct,
        "over_ci_lower_pct": over_ci_lower_pct,
        "over_ci_upper_pct": over_ci_upper_pct,
        "under_ci_lower_pct": under_ci_lower_pct,
        "under_ci_upper_pct": under_ci_upper_pct,
        "over_implied_pct": over_implied_pct,
        "under_implied_pct": under_implied_pct,
        "over_edge_pct": over_edge_pct,
        "under_edge_pct": under_edge_pct,
        "over_ev": results["over_ev"],
        "under_ev": results["under_ev"],
        "over_kelly_pct": results["over_kelly"] * 100,
        "under_kelly_pct": results["under_kelly"] * 100,
        "decision_over": results["decision_over"],
        "decision_under": results["decision_under"],

        "over_edge_strength": over_edge_strength,
        "under_edge_strength": under_edge_strength,
        "over_strength_class": get_strength_class(over_edge_strength),
        "under_strength_class": get_strength_class(under_edge_strength),

        "over_explanation": build_decision_explanation("over", results["decision_over"]),
        "under_explanation": build_decision_explanation("under", results["decision_under"]),

        "over_model_insight": build_model_insight(
            "over",
            results["p_over"],
            results["over_implied"],
            over_edge_pct,
            over_lower,
            over_upper,
            over_edge_strength,
        ),
        "under_model_insight": build_model_insight(
            "under",
            results["p_under"],
            results["under_implied"],
            under_edge_pct,
            under_lower,
            under_upper,
            under_edge_strength,
        ),

        "over_confidence_bar": get_confidence_bar(
            over_ci_lower_pct, over_ci_upper_pct, p_over_pct, over_implied_pct
        ),
        "under_confidence_bar": get_confidence_bar(
            under_ci_lower_pct, under_ci_upper_pct, p_under_pct, under_implied_pct
        ),
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
