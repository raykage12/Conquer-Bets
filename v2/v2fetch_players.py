from nba_api.stats.endpoints import *
from nba_api.stats.static import *
import time
# v2
class PlayersMinutes():
    # Get the teams roster
    def team_roster(self, name, Season):
            time.sleep(.5)
            # lookup team by team name (eg. Lakers, Bulls)
            team = teams.find_teams_by_nickname(name)[0]['id']
            # Get team roster in dataframe format
            roster = commonteamroster.CommonTeamRoster(season=Season, team_id=team).get_data_frames()[0]
            # team_players stores only the players column from the roster dataframe
            team_players = roster[["PLAYER"]]
            #print(team_players)
            return team_players
    
    # Get player points
    def points(self, id, Season, regular_season):
        time.sleep(.5) # sleep so dont time out
        # Get player stats
        stats = playergamelog.PlayerGameLog(player_id=id, season=Season, season_type_all_star=regular_season).get_data_frames()[0]
        # Only get points
        points = stats[['PTS']]
        # List to store points
        all_game_points = []
        # Go through each game to collect points and store in list
        for i in range(len(points)):
            current_game_points = points.iloc[i,0]
            all_game_points.append(int(current_game_points))
        return all_game_points

    # Function to find the id of the player
    def find_player_id(self, player):
        try:
            return players.find_players_by_full_name(player)[0]["id"]
        except Exception as e:
            return None

    # Get the average minutes for each player for all games played in regular season
    def calculate_avg_minutes(self, id, Season, regular_season):
        time.sleep(.5)
        # Get all the stats for the player in regular season
        player_stats = playergamelog.PlayerGameLog(player_id=id, season=Season, season_type_all_star=regular_season).get_data_frames()[0]
        # Saves on the players minutes in every game
        player_minutes = player_stats[["MIN"]]
        games = len(player_minutes) # number of games
        # counter to store avg
        avg = 0

        # loop through all games to add minutes of every game, then divide by games to get average
        for i in range(len(player_minutes)):
            mins = int(player_minutes.iloc[i, 0])
            avg += mins
        if len(player_minutes) > 0:
            avg /= len(player_minutes)
        else:
            avg = 0
        return avg, games
        
    # Starting function that will get the avg minutes of players calling other functions
    def get_player_minutes(self, team, Season, regular_season):
        minutes = {}
        team_players = self.team_roster(team, Season)
        
        # For loop to get player id then calculate players avg minutes
        for i in range(len(team_players)):
            player = team_players.iloc[i, 0]
            # call find_player_id function to get player id for player in list
            player_id = self.find_player_id(player)
            if player_id:
                avg_minutes, games = self.calculate_avg_minutes(player_id, Season, regular_season)
                # Sets key value for player and their id
                minutes[player] = [round(avg_minutes, 2), games]

        # Sorts the minutes dictionary from highest mins to lowest
        sorted_minutes = sorted(minutes.items(), key=lambda x:x[1], reverse=True)
        sorted_minutes = sorted_minutes[:8]
        print(f"{team} players with most minutes: ")
        # Displays the top 5 players with most avg minutes
        for player, mins in sorted_minutes:
            print(f"{player}: mins: {mins[0]} games: {mins[1]}")
        return sorted_minutes