"""
Camada de banco de dados SQLite do MVP.

Objetivo:
- criar o arquivo SQLite local
- abrir conexoes com o banco
- criar as tabelas usadas para persistir series e mapas
"""

import os
import sqlite3

from config import DATABASE_DIR, DATABASE_FILENAME

class Database:
    """
    Responsavel por gerenciar conexao e estrutura do SQLite.
    """

    
    def __init__(self):
        self.database_dir = DATABASE_DIR
        self.database_filename = DATABASE_FILENAME
        self.database_path = os.path.join(self.database_dir, self.database_filename)

    
    def ensure_database_dir(self):
        os.makedirs(self.database_dir, exist_ok=True)

    
    def get_connection(self):
        self.ensure_database_dir()

        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row

        return connection
    

    def create_tables(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                page_title TEXT NOT NULL,
                event_name TEXT,
                stage TEXT,
                team1_name TEXT,
                team2_name TEXT,
                match_datetime_raw TEXT,
                match_datetime TEXT,
                match_finished INTEGER NOT NULL DEFAULT 0,
                series_type TEXT,
                series_score_team1 INTEGER NOT NULL DEFAULT 0,
                series_score_team2 INTEGER NOT NULL DEFAULT 0,
                series_winner TEXT,
                collected_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_maps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                map_order INTEGER NOT NULL,
                map_name TEXT,
                map_finished TEXT,
                played INTEGER NOT NULL DEFAULT 0,
                team1_score INTEGER,
                team2_score INTEGER,
                winner TEXT,
                had_overtime INTEGER NOT NULL DEFAULT 0,
                team1_start_side TEXT,
                stats_id TEXT,
                vod_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES match_series(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                liquipedia_page TEXT,
                logo_filename TEXT,
                logo_source_url TEXT,
                logo_theme TEXT,
                logo_updated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                normalized_alias TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_aliases_team_id
            ON team_aliases(team_id)
        """)

        connection.commit()
        connection.close()


    def initialize(self):
        self.create_tables()
