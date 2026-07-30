"""Valida cada partida e seu evento contra a página oficial de origem."""

from __future__ import annotations

from collections import defaultdict
from contextlib import closing

from database import Database
from event_context import event_context_from_page
from liquipedia_client import LiquipediaClient
from liquipedia_parser import LiquipediaMatchParser


def match_key(team1: str | None, team2: str | None, date_raw: str | None):
    return (
        (team1 or "").strip().casefold(),
        (team2 or "").strip().casefold(),
        (date_raw or "").strip(),
    )


def validate() -> tuple[int, list[str]]:
    database = Database()
    client = LiquipediaClient()
    parser = LiquipediaMatchParser()

    with closing(database.get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, page_title, event_name, team1_name, team2_name,
                   match_datetime_raw
            FROM match_series
            ORDER BY page_title, id
            """
        ).fetchall()

    by_page = defaultdict(list)
    for row in rows:
        by_page[row["page_title"]].append(row)

    validated = 0
    issues = []
    for page_title, page_rows in by_page.items():
        wikitext = client.get_page_content(page_title)
        if not wikitext:
            for row in page_rows:
                issues.append(
                    f"#{row['id']}: página de origem indisponível ({page_title})"
                )
            continue

        source_matches = parser.parse_page(wikitext, page_title)
        source_keys = {
            match_key(
                series.team1_name,
                series.team2_name,
                series.match_datetime_raw,
            )
            for series in source_matches
        }
        expected_event, _ = event_context_from_page(page_title)

        for row in page_rows:
            key = match_key(
                row["team1_name"],
                row["team2_name"],
                row["match_datetime_raw"],
            )
            if key not in source_keys:
                issues.append(
                    f"#{row['id']}: partida não localizada em {page_title}"
                )
                continue
            if row["event_name"] != expected_event:
                issues.append(
                    f"#{row['id']}: evento '{row['event_name']}' deveria ser "
                    f"'{expected_event}'"
                )
                continue
            validated += 1

        print(
            f"[OK] {page_title}: "
            f"{sum(1 for row in page_rows if match_key(row['team1_name'], row['team2_name'], row['match_datetime_raw']) in source_keys)}"
            f"/{len(page_rows)} partidas localizadas"
        )

    return validated, issues


def main() -> None:
    validated, issues = validate()
    print(f"\nPartidas validadas: {validated}")
    print(f"Pendências: {len(issues)}")
    for issue in issues:
        print(f"[PENDENTE] {issue}")


if __name__ == "__main__":
    main()
