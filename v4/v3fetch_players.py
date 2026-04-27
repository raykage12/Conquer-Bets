from nba_api.stats.endpoints import commonteamroster, playergamelog
from nba_api.stats.static import players, teams
import time


class PlayerLookupError(Exception):
    """Raised when a player cannot be found."""


class DataRetrievalError(Exception):
    """Raised when remote NBA data cannot be retrieved."""


class PlayersMinutes:
    def team_roster(self, name, season):
        time.sleep(0.5)
        try:
            team_id = teams.find_teams_by_nickname(name)[0]["id"]
            roster = commonteamroster.CommonTeamRoster(
                season=season,
                team_id=team_id,
            ).get_data_frames()[0]
            return roster[["PLAYER"]]
        except Exception as exc:
            raise DataRetrievalError(f"Unable to retrieve roster for '{name}'.") from exc

    def points(self, player_id, season, regular_season):
        time.sleep(0.5)
        try:
            stats = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star=regular_season,
            ).get_data_frames()[0]
        except Exception as exc:
            raise DataRetrievalError(
                "Unable to retrieve player game log from the NBA API."
            ) from exc

        if stats.empty:
            raise DataRetrievalError("No game log data was returned for that player.")

        points = stats[["PTS"]]
        return [int(points.iloc[i, 0]) for i in range(len(points))]

    def find_player_id(self, player_name):
        matches = players.find_players_by_full_name(player_name)
        if not matches:
            raise PlayerLookupError(f"No player found for '{player_name}'.")
        return matches[0]["id"]

    def calculate_avg_minutes(self, player_id, season, regular_season):
        time.sleep(0.5)
        try:
            player_stats = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star=regular_season,
            ).get_data_frames()[0]
        except Exception as exc:
            raise DataRetrievalError("Unable to retrieve player minutes data.") from exc

        player_minutes = player_stats[["MIN"]]
        total_minutes = 0

        for i in range(len(player_minutes)):
            total_minutes += int(player_minutes.iloc[i, 0])

        if len(player_minutes) > 0:
            avg = total_minutes / len(player_minutes)
        else:
            avg = 0

        return avg, len(player_minutes)

    def get_player_minutes(self, team, season, regular_season):
        minutes = {}
        team_players = self.team_roster(team, season)

        for i in range(len(team_players)):
            player_name = team_players.iloc[i, 0]
            try:
                player_id = self.find_player_id(player_name)
                avg_minutes, games = self.calculate_avg_minutes(
                    player_id, season, regular_season
                )
                minutes[player_name] = [round(avg_minutes, 2), games]
            except (PlayerLookupError, DataRetrievalError):
                continue

        sorted_minutes = sorted(minutes.items(), key=lambda x: x[1], reverse=True)
        return sorted_minutes[:8]
