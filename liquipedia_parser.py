"""
Parser de partidas da Liquipedia.

Objetivo:
- receber o wikitexto bruto retornado pela MediaWiki API
- identificar blocos de partidas
- extrair series e mapas em estruturas definidas em models.py
"""

from config import DATA_SOURCE
from models import MatchSeries, MatchMap
import re

class LiquipediaMatchParser:
    """
    Parser responsavel por transformar wikitexto da Liquipedia
    em objetos estruturados de partidas.
    """

    def parse_page(self, wikitext, page_title):
        match_blocks = self.extract_match_blocks(wikitext)
        series_list = []

        for match_block in match_blocks:
            series = self.parse_match_block(match_block, page_title)

            if series is not None:
                series_list.append(series)

        return series_list
    

    def extract_match_blocks(self, wikitext):
        if not wikitext:
            return []
        
        blocks = []
        parts = wikitext.split("{{Match")

        for part in parts[1:]:
            block = "{{Match" + part
            blocks.append(block)

        return blocks
    
    def parse_match_block(self, match_block, page_title):
        opponent1_block = self.extract_field(match_block, "opponent1")
        opponent2_block = self.extract_field(match_block, "opponent2")
        date_raw = self.extract_field(match_block, "date")
        finished_raw = self.extract_field(match_block, "finished")
        

        team1_name = self.extract_team_name(opponent1_block)
        team2_name = self.extract_team_name(opponent2_block)

        match_finished = finished_raw == "true"
        maps = self.parse_maps(match_block)
        series_score_team1, series_score_team2 = self.calculate_series_score(maps)
        series_winner = self.infer_series_winner(series_score_team1, series_score_team2)
        series_type = self.infer_series_type(maps)

        series = MatchSeries(
            source=DATA_SOURCE,
            page_title=page_title,
            team1_name=team1_name,
            team2_name=team2_name,
            match_datetime_raw=date_raw,
            match_finished=match_finished,
            series_type=series_type,
            series_score_team1=series_score_team1,
            series_score_team2=series_score_team2,
            series_winner=series_winner,
            maps=maps
        )

        return series
    
    
    def extract_field(self, match_block, field_name):
        marker = f"|{field_name}="
        start_index = match_block.find(marker)

        if start_index == -1:
            return None

        value_start = start_index + len(marker)

        next_field_match = re.search(
            r"\|\w+=",
            match_block[value_start:]
        )

        if next_field_match is None:
            value = match_block[value_start:]
        else:
            value_end = value_start + next_field_match.start()
            value = match_block[value_start:value_end]

        return value.strip()
    
    def extract_team_name(self, opponent_block):
        if opponent_block is None:
            return None

        team_name = opponent_block.replace("{{TeamOpponent|", "")
        team_name = team_name.replace("}}", "")
        team_name = team_name.replace("<!--", "")
        team_name = team_name.replace("-->", "")
        team_name = team_name.strip()

        if team_name == "":
            return None

        return team_name
    

    def parse_maps(self, match_block):
        maps = []
        
        for map_order in range(1, 6):
            map_block = self.extract_map_block(match_block, map_order)

            if map_block is not None:
                parsed_map = self.parse_map_block(map_order, map_block)

                if parsed_map is not None:
                    maps.append(parsed_map)

        return maps
    
    def parse_map_block(self, map_order, map_block):
        map_name = self.clean_template_value(self.extract_field(map_block, "map"))
        map_finished = self.clean_template_value(self.extract_field(map_block, "finished"))
        team1_start_side = self.clean_template_value(self.extract_field(map_block, "t1firstside"))
        stats_id = self.clean_template_value(self.extract_field(map_block, "stats"))
        vod_url = self.clean_template_value(self.extract_field(map_block, "vod"))

        played = map_finished == "true"
        had_overtime = self.has_overtime(map_block)

        if played:
            team1_score, team2_score = self.calculate_map_score(map_block)
            winner = self.infer_map_winner(team1_score, team2_score)
        else:
            team1_score = None
            team2_score = None
            winner = "unknown"

        match_map = MatchMap(
            map_order=map_order,
            map_name=map_name,
            map_finished=map_finished,
            played=played,
            team1_start_side=team1_start_side,
            stats_id=stats_id,
            vod_url=vod_url,
            had_overtime=had_overtime,
            team1_score=team1_score,
            team2_score=team2_score,
            winner=winner
        )

        return match_map
    
    def extract_map_block(self, match_block, map_order):
        marker = f"|map{map_order}="
        start_index = match_block.find(marker)

        if start_index == -1:
            return None

        value_start = start_index + len(marker)
        
        next_map_marker = f"|map{map_order + 1}="
        next_map_index = match_block.find(next_map_marker, value_start)

        if next_map_index != -1:
            map_block = match_block[value_start:next_map_index]
            return map_block.strip()
        
        end_markers = [

            "\n    |hltv=",
            "\n    |twitch=",
            "\n    |youtube=",
            "\n    |kick=",
            "\n    }}",
        ]

        end_indexes = []

        for end_marker in end_markers:
            end_index = match_block.find(end_marker, value_start)

            if end_index != -1:
                end_indexes.append(end_index)

        if end_indexes:
            map_end = min(end_indexes)
            map_block = match_block[value_start:map_end]
        else:
            map_block = match_block[value_start:]

        return map_block.strip()
    

    def to_int(self, value):
        if value is None:
            return 0

        value = value.strip()

        if not value.isdigit():
            return 0

        return int(value)
    

    def calculate_map_score(self, map_block):
        t1t = self.to_int(self.extract_field(map_block, "t1t"))
        t1ct = self.to_int(self.extract_field(map_block, "t1ct"))
        t2t = self.to_int(self.extract_field(map_block, "t2t"))
        t2ct = self.to_int(self.extract_field(map_block, "t2ct"))

        team1_score = t1t + t1ct
        team2_score = t2t + t2ct

        overtime_team1_score, overtime_team2_score = self.calculate_overtime_score(map_block)

        team1_score += overtime_team1_score
        team2_score += overtime_team2_score

        return team1_score, team2_score
    

    def infer_map_winner(self, team1_score, team2_score):
        if team1_score > team2_score:
            return "team1"

        if team2_score > team1_score:
            return "team2"

        return "unknown"
    
    
    def calculate_series_score(self, maps):
        team1_score = 0
        team2_score = 0

        for match_map in maps:
            if match_map.played:
                if match_map.winner == "team1":
                    team1_score += 1
                elif match_map.winner == "team2":
                    team2_score += 1

        return team1_score, team2_score
    

    def infer_series_winner(self, team1_score, team2_score):
        if team1_score > team2_score:
            return "team1"

        if team2_score > team1_score:
            return "team2"

        return "unknown"
    
    
    def infer_series_type(self, maps):
        if not maps:
            return "unknown"

        max_map_order = max(match_map.map_order for match_map in maps)

        if max_map_order >= 5:
            return "bo5"

        if max_map_order >= 3:
            return "bo3"

        if max_map_order == 1:
            return "bo1"

        return "unknown"
    
    def clean_template_value(self, value):
        if value is None:
            return None

        value = value.replace("}}", "").strip()

        if value == "":
            return None

        return value
    
    def has_overtime(self, map_block):
        for overtime_order in range(1, 10):
            marker = f"|o{overtime_order}"

            if marker in map_block:
                return True

        return False

    
    def calculate_overtime_score(self, map_block):
        overtime_team1_score = 0
        overtime_team2_score = 0

        for overtime_order in range(1, 10):
            t1t = self.extract_field(map_block, f"o{overtime_order}t1t")
            t1ct = self.extract_field(map_block, f"o{overtime_order}t1ct")
            t2t = self.extract_field(map_block, f"o{overtime_order}t2t")
            t2ct = self.extract_field(map_block, f"o{overtime_order}t2ct")

            if t1t is None and t1ct is None and t2t is None and t2ct is None:
                continue

            overtime_team1_score += self.to_int(t1t) + self.to_int(t1ct)
            overtime_team2_score += self.to_int(t2t) + self.to_int(t2ct)

        return overtime_team1_score, overtime_team2_score
    
