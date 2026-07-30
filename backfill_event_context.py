"""Preenche evento e fase das partidas já existentes no SQLite."""

from __future__ import annotations

import argparse
from contextlib import closing

from database import Database
from event_context import event_context_from_page, match_stage, parse_match_datetime


def backfill(dry_run: bool = False) -> int:
    database = Database()
    database.initialize()

    with closing(database.get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, page_title, event_name, stage, team1_name, team2_name,
                   match_datetime_raw, match_datetime
            FROM match_series
            ORDER BY id
            """
        ).fetchall()
        updates = []
        for row in rows:
            event_name, stage = event_context_from_page(row["page_title"])
            parsed_datetime = parse_match_datetime(row["match_datetime_raw"])
            stage = match_stage(
                event_name,
                stage,
                row["team1_name"],
                row["team2_name"],
                parsed_datetime,
            )
            match_datetime = (
                parsed_datetime.isoformat() if parsed_datetime is not None else None
            )
            if (
                row["event_name"] == event_name
                and row["stage"] == stage
                and row["match_datetime"] == match_datetime
            ):
                continue
            updates.append((event_name, stage, match_datetime, row["id"]))

        if updates and not dry_run:
            connection.executemany(
                """
                UPDATE match_series
                SET event_name = ?, stage = ?, match_datetime = ?
                WHERE id = ?
                """,
                updates,
            )
            connection.commit()

    return len(updates)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas informa quantos registros seriam atualizados.",
    )
    args = parser.parse_args()
    count = backfill(dry_run=args.dry_run)
    action = "seriam atualizadas" if args.dry_run else "atualizadas"
    print(f"Partidas {action}: {count}")


if __name__ == "__main__":
    main()
