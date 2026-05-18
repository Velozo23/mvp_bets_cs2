"""
Parser de partidas da Liquipedia.

Objetivo:
- receber o wikitexto bruto retornado pela MediaWiki API
- identificar blocos de partidas
- extrair series e mapas em estruturas definidas em models.py
"""

from config import DATA_SOURCE
from models import MatchSeries
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

        series = MatchSeries(
            source=DATA_SOURCE,
            page_title=page_title,
            team1_name=team1_name,
            team2_name=team2_name,
            match_datetime_raw=date_raw,
            match_finished=match_finished,
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

        return team_name.strip()
    


