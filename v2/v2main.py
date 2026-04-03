from v2fetch_players import PlayersMinutes
from v2calculations import Calculations
import time

# MAIN MENU
def main():
    #minutes = PlayersMinutes()
    get_calculations = Calculations()

    while True:
        Season = '2025-26' # current season
        regular_season = 'Regular Season' # regular season games

        try:
            # Player data entry
            entry = input("\nEnter 'spead, O_odds, U_odds, name': ")
            entry = entry.split()
            player = " ".join(entry[3:])
            spread = float(entry[0])
            odds_over = int(entry[1])
            odds_under = int(entry[2])
            get_calculations.get_results(player, Season, regular_season, spread, odds_over, odds_under)
        except Exception as e:
            print("Invalid Entry. Try Again")

if __name__ == "__main__":
     main()