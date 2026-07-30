"""Persistência do catálogo de times e dos metadados de seus logos."""

from __future__ import annotations

import re
import unicodedata
from contextlib import closing
from datetime import datetime, timezone

from database import Database


def normalize_team_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return text


class TeamRepository:
    def __init__(self, database=None):
        self.database = database or Database()

    def discover_match_aliases(self) -> list[str]:
        with closing(self.database.get_connection()) as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT trim(team_name) AS team_name
                FROM (
                    SELECT team1_name AS team_name FROM match_series
                    UNION ALL
                    SELECT team2_name AS team_name FROM match_series
                )
                WHERE team_name IS NOT NULL AND trim(team_name) != ''
                ORDER BY team_name COLLATE NOCASE
                """
            ).fetchall()
        return [row["team_name"] for row in rows]

    def save_team_logo(
        self,
        *,
        alias: str,
        canonical_name: str,
        liquipedia_page: str | None,
        logo_filename: str,
        logo_source_url: str,
        logo_theme: str = "dark",
    ) -> int:
        normalized_name = normalize_team_name(canonical_name)
        normalized_alias = normalize_team_name(alias)
        now = datetime.now(timezone.utc).isoformat()

        connection = self.database.get_connection()
        try:
            connection.execute(
                """
                INSERT INTO teams (
                    canonical_name, normalized_name, liquipedia_page,
                    logo_filename, logo_source_url, logo_theme,
                    logo_updated_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(normalized_name) DO UPDATE SET
                    canonical_name = excluded.canonical_name,
                    liquipedia_page = excluded.liquipedia_page,
                    logo_filename = excluded.logo_filename,
                    logo_source_url = excluded.logo_source_url,
                    logo_theme = excluded.logo_theme,
                    logo_updated_at = excluded.logo_updated_at,
                    updated_at = excluded.updated_at
                """,
                (
                    canonical_name,
                    normalized_name,
                    liquipedia_page,
                    logo_filename,
                    logo_source_url,
                    logo_theme,
                    now,
                    now,
                ),
            )
            team_id = connection.execute(
                "SELECT id FROM teams WHERE normalized_name = ?",
                (normalized_name,),
            ).fetchone()["id"]
            connection.execute(
                """
                INSERT INTO team_aliases (team_id, alias, normalized_alias)
                VALUES (?, ?, ?)
                ON CONFLICT(normalized_alias) DO UPDATE SET
                    team_id = excluded.team_id,
                    alias = excluded.alias
                """,
                (team_id, alias, normalized_alias),
            )
            connection.commit()
            return team_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def find_by_alias(self, alias: str):
        normalized_alias = normalize_team_name(alias)
        with closing(self.database.get_connection()) as connection:
            return connection.execute(
                """
                SELECT t.*, a.alias
                FROM team_aliases a
                JOIN teams t ON t.id = a.team_id
                WHERE a.normalized_alias = ?
                """,
                (normalized_alias,),
            ).fetchone()
