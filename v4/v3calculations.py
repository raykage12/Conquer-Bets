import random
from v3fetch_players import PlayersMinutes, PlayerLookupError, DataRetrievalError


class Calculations:
    def __init__(self):
        self.players_service = PlayersMinutes()

    def bootstrap(self, player_points, spread):
        n = len(player_points)
        if n == 0:
            raise ValueError("Player has no games played.")

        over_count = 0
        for value in player_points:
            if value > spread:
                over_count += 1
        p_over_point = over_count / n
        p_under_point = 1.0 - p_over_point

        B = 200_000
        bootstrap_stats = []

        points = player_points
        rand_index = random.randrange
        append = bootstrap_stats.append

        for _ in range(B):
            over = 0
            for _ in range(n):
                if points[rand_index(n)] > spread:
                    over += 1
            append(over / n)

        bootstrap_stats.sort()
        lower = bootstrap_stats[int(0.025 * B)]
        upper = bootstrap_stats[int(0.975 * B)]

        return p_over_point, p_under_point, lower, upper

    def implied_odds(self, over_odds, under_odds):
        if over_odds > 0:
            over_implied = 100 / (over_odds + 100)
        else:
            over_implied = abs(over_odds) / (abs(over_odds) + 100)

        if under_odds > 0:
            under_implied = 100 / (under_odds + 100)
        else:
            under_implied = abs(under_odds) / (abs(under_odds) + 100)

        return over_implied, under_implied

    def calculate_ev(self, p_over, p_under, odds_over, odds_under):
        if odds_over > 0:
            decimal_over = 1 + (odds_over / 100)
        else:
            decimal_over = 1 + (100 / abs(odds_over))

        if odds_under > 0:
            decimal_under = 1 + (odds_under / 100)
        else:
            decimal_under = 1 + (100 / abs(odds_under))

        ev_over = ((p_over * (decimal_over - 1)) - (1 - p_over)) * 100
        ev_under = ((p_under * (decimal_under - 1)) - (1 - p_under)) * 100
        return ev_over, ev_under, decimal_over, decimal_under

    def calculate_kelly(self, p_over, p_under, odds_dec_over, odds_dec_under):
        kelly_multiplier = 1 / 16

        over_kelly = (
            ((p_over * (odds_dec_over - 1)) - (1 - p_over)) / (odds_dec_over - 1)
        ) * kelly_multiplier
        under_kelly = (
            ((p_under * (odds_dec_under - 1)) - (1 - p_under))
            / (odds_dec_under - 1)
        ) * kelly_multiplier

        return over_kelly, under_kelly

    def get_betting_decision(
        self,
        over_lower_ci,
        over_upper_ci,
        under_lower_ci,
        under_upper_ci,
        over_implied,
        under_implied,
        p_over,
        p_under,
    ):
        if over_implied >= p_over:
            over_decision = "No Bet - No EV"
        else:
            if over_lower_ci > over_implied:
                safety = over_lower_ci - over_implied
                over_decision = f"Strong Over - Safer Bet (safety +{safety * 100:.2f}%)"
            elif over_lower_ci < over_implied < over_upper_ci:
                safety = over_lower_ci - over_implied
                if safety > -0.15:
                    over_decision = f"Weak Over - Some Risk (safety {safety * 100:.2f}%)"
                else:
                    over_decision = f"Weak Over - Too Risky (safety {safety * 100:.2f}%)"
            else:
                over_decision = "No Bet - Fake Edge"

        if under_implied >= p_under:
            under_decision = "No Bet - No EV"
        else:
            if under_lower_ci > under_implied:
                safety = under_lower_ci - under_implied
                under_decision = f"Strong Under - Safer Bet (safety +{safety * 100:.2f}%)"
            elif under_lower_ci < under_implied < under_upper_ci:
                safety = under_lower_ci - under_implied
                if safety > -0.5:
                    under_decision = f"Weak Under - Some Risk (safety {safety * 100:.2f}%)"
                else:
                    under_decision = f"Weak Under - Too Risky (safety {safety * 100:.2f}%)"
            else:
                under_decision = "No Bet - Fake Edge"

        return over_decision, under_decision

    def analyze_player(self, player, season, regular_season, spread, odds_over, odds_under):
        player_id = self.players_service.find_player_id(player)
        player_points = self.players_service.points(player_id, season, regular_season)

        p_over, p_under, lower, upper = self.bootstrap(player_points, spread)
        p_under_lower = 1 - upper
        p_under_upper = 1 - lower

        over_implied, under_implied = self.implied_odds(odds_over, odds_under)
        over_ev, under_ev, over_dec_odds, under_dec_odds = self.calculate_ev(
            p_over,
            p_under,
            odds_over,
            odds_under,
        )
        over_kelly, under_kelly = self.calculate_kelly(
            p_over,
            p_under,
            over_dec_odds,
            under_dec_odds,
        )
        decision_over, decision_under = self.get_betting_decision(
            lower,
            upper,
            p_under_lower,
            p_under_upper,
            over_implied,
            under_implied,
            p_over,
            p_under,
        )

        return {
            "player": player,
            "season": season,
            "spread": spread,
            "odds_over": odds_over,
            "odds_under": odds_under,
            "games": len(player_points),
            "points": player_points,
            "p_over": p_over,
            "p_under": p_under,
            "over_ci": (lower, upper),
            "under_ci": (p_under_lower, p_under_upper),
            "over_implied": over_implied,
            "under_implied": under_implied,
            "over_ev": over_ev,
            "under_ev": under_ev,
            "over_kelly": over_kelly,
            "under_kelly": under_kelly,
            "decision_over": decision_over,
            "decision_under": decision_under,
        }

    def format_results(self, results):
        over_lower, over_upper = results["over_ci"]
        under_lower, under_upper = results["under_ci"]

        lines = [
            "-" * 27 + f" {results['player'].upper()} " + "-" * 27,
            f"Games:{results['games']} -- Points:{results['points']}",
            (
                f"p(O{results['spread']})({results['odds_over']}): "
                f"{(results['p_over'] * 100) - (results['over_implied'] * 100):.2f}% "
                f"[{(over_lower * 100):.2f}% , {(over_upper * 100):.2f}%]   "
                f"over EV: {results['over_ev']:.2f}%  "
                f"Kelly: {(results['over_kelly'] * 100):.2f}%  "
                f"Decision: {results['decision_over']}"
            ),
            (
                f"p(U{results['spread']})({results['odds_under']}): "
                f"{(results['p_under'] * 100) - (results['under_implied'] * 100):.2f}% "
                f"[{(under_lower * 100):.2f}% , {(under_upper * 100):.2f}%]   "
                f"under EV: {results['under_ev']:.2f}%  "
                f"Kelly: {(results['under_kelly'] * 100):.2f}%  "
                f"Decision: {results['decision_under']}"
            ),
        ]
        return "\n".join(lines)
