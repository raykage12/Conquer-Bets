from nba_api.stats.endpoints import *
from nba_api.stats.static import *
import numpy as np
from v2fetch_players import PlayersMinutes
import time
import random
# v2
class Calculations:
    # Bootstrap function
    def bootstrap(self, player_points, spread):
        # Returns: p_over_point, p_under_point, lower_CI, upper_CI
        n = len(player_points)
        if n == 0:
            raise ValueError("player_points is empty; cannot bootstrap.")

        # 1) POINT ESTIMATE from the original sample (deterministic)
        over_count = 0
        for x in player_points:
            if x > spread:
                over_count += 1
        p_over_point = over_count / n
        p_under_point = 1.0 - p_over_point

        # 2) BOOTSTRAP DISTRIBUTION for uncertainty (CI)
        B = 200_000
        bootstrap_stats = []

        # Local bindings for speed (still pure python)
        points = player_points
        rr = random.randrange
        append = bootstrap_stats.append
        sp = spread

        for _ in range(B):
            over = 0
            for _ in range(n):
                if points[rr(n)] > sp:
                    over += 1
            append(over / n)

        bootstrap_stats.sort()

        lower = bootstrap_stats[int(0.025 * B)]
        upper = bootstrap_stats[int(0.975 * B)]

        return p_over_point, p_under_point, lower, upper

    
    
    # Calculate the implied odds for the over and the under
    def implied_odds(self, over_odds, under_odds):
        if over_odds > 0:
            over_odds = (100/ (over_odds+100))
        else:
            over_odds = (abs(over_odds) / (abs(over_odds) + 100))
        
        if under_odds > 0:
            under_odds = (100/ (under_odds+100))
        else:
            under_odds = (abs(under_odds) / (abs(under_odds) + 100))
        
        return over_odds, under_odds
    

    def calculate_EV(self, p_over, p_under, odds_over, odds_under):
        # Convert American odds into decimal odds
        if odds_over > 0:
            decimal_over = (1 + (odds_over / 100))
        else:
            decimal_over = (1 + (100 / abs(odds_over)))
        if odds_under > 0:
            decimal_under = (1 + (odds_under / 100))
        else:
            decimal_under = (1 + (100 / abs(odds_under)))

        # Calculate EV
        EV_over = ((p_over*(decimal_over - 1)) - (1 - p_over)) * 100
        EV_under = ((p_under*(decimal_under - 1)) - (1 - p_under)) * 100
        return EV_over, EV_under, decimal_over, decimal_under
    

    def calculate_kelly(self, p_over, p_under, odds_dec_over, odds_dec_under, ):
        # p = probability, q = 1 - p, b = decimal odds - 1
        # Kelly = (p(b) - (1 - p)) / b
        kelly_multiplier = 1/16 # ADJUST AS NEEDED

        # Calculate Kelly for both Over and Under
        over_kelly = (((p_over * (odds_dec_over - 1)) - (1 - p_over)) / (odds_dec_over - 1)) * kelly_multiplier
        under_kelly = (((p_under * (odds_dec_under-1)) - (1 - p_under)) / (odds_dec_under - 1)) * kelly_multiplier
                
        return over_kelly, under_kelly
    
    # Will determine the decision to make based off CI and implied odds
    def get_betting_decision(self, over_lower_CI, over_upper_CI, under_lower_CI, under_upper_CI, over_implied, under_implied, p_over, p_under):

        # ------------------ OVER DECISION ------------------
        if over_implied >= p_over:
            over_decision = "No Bet - No EV"
        else:
            # Strong Over: worst-case probability beats implied
            if over_lower_CI > over_implied:
                safety = over_lower_CI - over_implied
                over_decision = f"Strong Over - Safer Bet (safety +{safety*100:.2f}%)"

            # Weak Over: +EV but CI overlaps implied
            elif over_lower_CI < over_implied < over_upper_CI:
                safety = over_lower_CI - over_implied
                if safety > -0.15:
                    over_decision = f"Weak Over - Some Risk (safety {safety*100:.2f}%)"
                else:
                    over_decision = f"Weak Over - Too Risky (safety {safety*100:.2f}%)"

            else:
                over_decision = "No Bet - Fake Edge"


        # ------------------ UNDER DECISION ------------------
        if under_implied >= p_under:
            under_decision = "No Bet - No EV"
        else:
            # Strong Under
            if under_lower_CI > under_implied:
                safety = under_lower_CI - under_implied
                under_decision = f"Strong Under - Safer Bet (safety +{safety*100:.2f}%)"

            # Weak Under
            elif under_lower_CI < under_implied < under_upper_CI:
                safety = under_lower_CI - under_implied
                if safety > -0.5:
                    under_decision = f"Weak Under - Some Risk (safety {safety*100:.2f}%)"
                else:
                    under_decision = f"Weak Under - Too Risky (safety {safety*100:.2f}%)"

            else:
                under_decision = "No Bet - Fake Edge"

        return over_decision, under_decision



    # Engine that calls other functions to complete entire calculations of the:
    # Bootstrap: Prob(over/under) and get the CI - calculate implied odds - calculate EV - calculate Kelly Criterion
    def get_results(self, player, Season, regular_season, spread, odds_over, odds_under):
        # Get player id
        try:
            id = players.find_players_by_full_name(player)[0]["id"]
        except Exception as e:
            print(f"{player}: no data")
            return
        # Go to points function to get all players points in the season
        get_points = PlayersMinutes()
        player_points = get_points.points(id, Season, regular_season)

        # Start bootstrap
        p_over, p_under, lower, upper = self.bootstrap(player_points, spread)
        # lower and upper flipped for the under probability
        p_under_lower = 1 - upper
        p_under_upper = 1- lower

        # Convert odds to implied odds
        over_implied, under_implied = self.implied_odds(odds_over, odds_under)

        # Calculate EV using bootstrap
        over_EV, under_EV, over_dec_odds, under_dec_odds = self.calculate_EV(p_over, p_under, odds_over, odds_under)

        # Calculate Kelly Criterion
        over_kelly, under_kelly = self.calculate_kelly(p_over, p_under, over_dec_odds, under_dec_odds)

        # Determine actiong for the bet
        decision_over, decision_under = self.get_betting_decision(lower, upper, p_under_lower, p_under_upper, over_implied, under_implied, p_over, p_under)


        # RESULTS
        print("-"*27, player.upper(), '-'*27)
        print(f"Games:{len(player_points)} -- Points:{player_points}")
        print(f"p(O{spread})({odds_over}): {(p_over*100) - (over_implied*100):.2f}% [{(lower * 100):.2f}% , {(upper * 100):.2f}%]   over EV: {over_EV:.2f}%  Kelly: {(over_kelly*100):.2f}%  Decision: {decision_over}")
        print(f"p(U{spread})({odds_under}), {(p_under*100) - (under_implied*100):.2f}% [{(p_under_lower * 100):.2f}% , {(p_under_upper * 100):.2f}%]   under EV: {under_EV:.2f}%  Kelly: {(under_kelly*100):.2f}%  Decision: {decision_under}")

