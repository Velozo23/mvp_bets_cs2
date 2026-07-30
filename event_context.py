"""Normalização do nome do evento e da fase a partir da página Liquipedia."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone


STAGE_PATTERN = re.compile(
    r"^(?:"
    r"stage\s+\d+|"
    r"playoffs?|"
    r"group(?:\s+stage|\s+[a-z0-9]+)?|"
    r"closed\s+qualifier|open\s+qualifier|qualifiers?|"
    r"quarterfinals?|semifinals?|grand\s+finals?|finals?"
    r")$",
    re.IGNORECASE,
)

TIMEZONE_OFFSETS = {
    "UTC": 0,
    "GMT": 0,
    "CET": 1,
    "CEST": 2,
    "CST": 8,
}

OFFICIAL_EVENT_NAMES = {
    "blast/open/2026/spring": "BLAST Open Rotterdam 2026",
    "cs asia championships/2026": "CS Asia Championships 2026",
    "intel extreme masters/2026/cologne": "IEM Cologne Major 2026",
}


def humanize_page_part(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ")).strip()


def event_context_from_page(page_title: str) -> tuple[str | None, str | None]:
    """
    Deriva um nome estável de evento e uma fase a partir do caminho da página.

    Exemplos:
    Intel_Extreme_Masters/2026/Cologne/Stage_1
      -> ("Intel Extreme Masters Cologne 2026", "Stage 1")
    BLAST/Open/2026/Spring
      -> ("BLAST Open Spring 2026", None)
    """
    parts = [
        humanize_page_part(part)
        for part in (page_title or "").split("/")
        if humanize_page_part(part)
    ]
    if not parts:
        return None, None

    stage = None
    if len(parts) > 1 and STAGE_PATTERN.fullmatch(parts[-1]):
        stage = parts.pop()

    normalized_base = "/".join(part.casefold() for part in parts)
    official_name = OFFICIAL_EVENT_NAMES.get(normalized_base)
    if official_name:
        return official_name, stage

    years = [part for part in parts if re.fullmatch(r"20\d{2}", part)]
    names = [part for part in parts if part not in years]
    event_name = " ".join([*names, *years]).strip() or None
    return event_name, stage


def parse_match_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    match = re.search(
        r"([A-Za-z]+ \d{1,2}, 20\d{2})\s*-\s*(\d{1,2}:\d{2})",
        value,
    )
    if not match:
        return None
    abbreviation = re.search(r"\{\{Abbr/([A-Za-z]+)", value)
    timezone_name = abbreviation.group(1).upper() if abbreviation else "UTC"
    offset = TIMEZONE_OFFSETS.get(timezone_name)
    if offset is None:
        return None
    parsed = datetime.strptime(
        f"{match.group(1)} {match.group(2)}", "%B %d, %Y %H:%M"
    )
    return parsed.replace(tzinfo=timezone(timedelta(hours=offset)))


def match_stage(
    event_name: str | None,
    default_stage: str | None,
    team1_name: str | None,
    team2_name: str | None,
    match_datetime: datetime | None,
) -> str | None:
    """Refina fases que não aparecem no caminho da página do evento."""
    teams = {
        (team1_name or "").casefold(),
        (team2_name or "").casefold(),
    }
    if event_name == "IEM Cologne Major 2026" and teams == {
        "germany",
        "poland",
    }:
        return "Showmatch"

    if event_name == "BLAST Open Rotterdam 2026" and match_datetime:
        match_date = match_datetime.date().isoformat()
        if match_date == "2026-03-29":
            return "Grand Final"
        if match_date >= "2026-03-27":
            return "Playoffs"
        return "Group Stage"

    return default_stage
