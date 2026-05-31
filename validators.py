"""
Validadores de dados do MVP.

Objetivo:
- identificar series e mapas incompletos ou inconsistentes
- separar problemas de qualidade de dados da logica de parsing
- permitir que a coleta continue mesmo quando uma partida tiver dados parciais
"""

from models import MatchSeries, MatchMap

class MatchValidator:
    """
    Validador responsavel por analisar objetos MatchSeries e MatchMap.
    """

    def validate_series(self, series: MatchSeries) -> list:

        warnings = []

        if series.team1_name is None:
            warnings.append("Team 1 name is missing.")

        if series.team2_name is None:
            warnings.append("Team 2 name is missing.")

        if series.match_datetime_raw is None:
            warnings.append("Match datetime is missing.")

        if series.maps is None or len(series.maps) == 0:
            warnings.append("No maps found in the series.")

        for match_map in series.maps:
            map_warnings = self.validate_map(match_map)

            for warning in map_warnings:
                warnings.append(f"Map {match_map.map_order}: {warning}")

        return warnings


    def validate_map(self, match_map: MatchMap) -> list:
        warnings = []

        if match_map.map_name is None:
            warnings.append("Map name is missing.")

        if match_map.map_finished is None:
            warnings.append("Map finished status is missing.")

        if match_map.played is True:
            if match_map.team1_score is None:
                warnings.append("Team 1 score is missing.")

            if match_map.team2_score is None:
                warnings.append("Team 2 score is missing.")

            if (
                match_map.team1_score is not None
                and match_map.team2_score is not None
                and match_map.team1_score == match_map.team2_score
            ):
                warnings.append("tied_finished_map.")

            if match_map.winner == "unknown":
                warnings.append("unknown_map_winner.")
        
        if match_map.played is False:
            if match_map.map_finished != "skip" and match_map.map_finished is not None:
                warnings.append("not_played_unexpected_status.")

        return warnings


    def is_complete_series(self, series: MatchSeries) -> bool:
        warnings = self.validate_series(series)

        blocking_warnings = {
            "Team 1 name is missing.",
            "Team 2 name is missing.",
            "No maps found in the series.",
        }

        for warning in warnings:
            if warning in blocking_warnings:
                return False

        return True
    

