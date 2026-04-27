from v3calculations import Calculations
from v3fetch_players import PlayerLookupError, DataRetrievalError


class InputValidationError(Exception):
    """Raised when user input is missing or malformed."""


MIN_ODDS = -250
MAX_ODDS = 250
SEASON = "2025-26"
REGULAR_SEASON = "Regular Season"


def parse_entry(raw_entry):
    parts = raw_entry.strip().split()
    if len(parts) < 4:
        raise InputValidationError(
            "Please enter: spread over_odds under_odds player_name"
        )

    try:
        spread = float(parts[0])
    except ValueError as exc:
        raise InputValidationError("Spread must be a number.") from exc

    try:
        odds_over = int(parts[1])
        odds_under = int(parts[2])
    except ValueError as exc:
        raise InputValidationError("Over and under odds must be whole numbers.") from exc

    if odds_over == 0 or odds_under == 0:
        raise InputValidationError("Odds cannot be 0.")

    if not (MIN_ODDS <= odds_over <= MAX_ODDS):
        raise InputValidationError(
            f"Over odds must be between {MIN_ODDS} and {MAX_ODDS}."
        )

    if not (MIN_ODDS <= odds_under <= MAX_ODDS):
        raise InputValidationError(
            f"Under odds must be between {MIN_ODDS} and {MAX_ODDS}."
        )

    player = " ".join(parts[3:]).strip()
    if not player:
        raise InputValidationError("Player name is required.")

    return {
        "player": player,
        "spread": spread,
        "odds_over": odds_over,
        "odds_under": odds_under,
    }

def main():
    calculator = Calculations()

    while True:
        raw_entry = input(
            "\nEnter: spread over_odds under_odds player_name\n"
            "Example: 32.5 -110 -110 LeBron James\n> "
        )

        if raw_entry.strip().lower() in {"q", "quit", "exit"}:
            print("Exiting Conquer Bets.")
            break

        try:
            parsed = parse_entry(raw_entry)
            results = calculator.analyze_player(
                parsed["player"],
                SEASON,
                REGULAR_SEASON,
                parsed["spread"],
                parsed["odds_over"],
                parsed["odds_under"],
            )
            print(calculator.format_results(results))
        except InputValidationError as exc:
            print(f"Input Error: {exc}")
        except PlayerLookupError as exc:
            print(f"Player Error: {exc}")
        except DataRetrievalError as exc:
            print(f"API Error: {exc}")
        except Exception as exc:
            print(f"Unexpected Error: {exc}")


if __name__ == "__main__":
    main()
