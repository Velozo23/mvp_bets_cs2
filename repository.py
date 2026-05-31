"""
Repositorio de persistencia do MVP.

Objetivo:
- salvar objetos MatchSeries e MatchMap no SQLite
- isolar comandos SQL da logica de parser e coleta
- manter a persistencia em uma camada propria
"""

from database import Database
from models import MatchSeries, MatchMap

class MatchRepository:
    """
    Repositorio responsavel por persistir series e mapas no banco.
    """

    def __init__(self, database=None):
        self.database = database or Database()

    def datetime_to_text(self, value):
        if value is None:
            return None

        return value.isoformat()
    
    def bool_to_int(self, value):
        return 1 if value else 0
    
    def save_series(self, connection, series: MatchSeries):
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO match_series (
                source,
                page_title,
                event_name,
                stage,
                team1_name,
                team2_name,
                match_datetime_raw,
                match_datetime,
                match_finished,
                series_type,
                series_score_team1,
                series_score_team2,
                series_winner,
                collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            series.source,
            series.page_title,
            series.event_name,
            series.stage,
            series.team1_name,
            series.team2_name,
            series.match_datetime_raw,
            self.datetime_to_text(series.match_datetime),
            self.bool_to_int(series.match_finished),
            series.series_type,
            series.series_score_team1,
            series.series_score_team2,
            series.series_winner,
            self.datetime_to_text(series.collected_at)
        ))

        return cursor.lastrowid
    

    def save_map(self, connection, series_id: int, match_map: MatchMap):
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO match_maps (
                series_id,
                map_order,
                map_name,
                map_finished,
                played,
                team1_score,
                team2_score,
                winner,
                had_overtime,
                team1_start_side,
                stats_id,
                vod_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                series_id,
                match_map.map_order,
                match_map.map_name,
                match_map.map_finished,
                self.bool_to_int(match_map.played),
                match_map.team1_score,
                match_map.team2_score,
                match_map.winner,
                self.bool_to_int(match_map.had_overtime),
                match_map.team1_start_side,
                match_map.stats_id,
                match_map.vod_url,
            ),
        )

   
    def save_maps(self, connection, series_id: int, maps: list[MatchMap]):
        for match_map in maps:
            self.save_map(connection, series_id, match_map)

    
    def save_full_series(self, series: MatchSeries):
        connection = self.database.get_connection()

        try:
            existing_series_id = self.find_existing_series_id(connection, series)

            if existing_series_id is not None:
                return existing_series_id

            series_id = self.save_series(connection, series)
            self.save_maps(connection, series_id, series.maps)
            connection.commit()

            return series_id

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()


    def find_existing_series_id(self, connection, series: MatchSeries):
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM match_series
            WHERE page_title = ?
            AND team1_name = ?
            AND team2_name = ?
            AND match_datetime_raw = ?
            LIMIT 1
            """,
            (
                series.page_title,
                series.team1_name,
                series.team2_name,
                series.match_datetime_raw,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row["id"]
    
