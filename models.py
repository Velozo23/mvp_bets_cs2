"""
Modelos de dados do MVP.

Objetivo:
- definir a estrutura padrao para series e mapas
- servir como contrato entre parser e persistencia
- evitar dicionarios soltos espalhados pelo projeto
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MatchMap:
    """
    Representa um mapa dentro de uma serie de CS2.
    """

    map_order: int
    map_name: str | None = None
    map_finished: str | None = None
    played: bool = False
    team1_score: int | None = None
    team2_score: int | None = None
    winner: str = "unknown"
    had_overtime: bool = False
    team1_start_side: str | None = None
    stats_id: str | None = None
    vod_url: str | None = None


@dataclass
class MatchSeries:
    """
    Representa uma serie/partida completa de CS2.
    """

    source: str
    page_title: str
    event_name: str | None = None
    stage: str | None = None
    team1_name: str | None = None
    team2_name: str | None = None
    match_datetime_raw: str | None = None
    match_datetime: datetime | None = None
    match_finished: bool = False
    series_type: str = "unknown"
    series_score_team1: int = 0
    series_score_team2: int = 0
    series_winner: str = "unknown"
    collected_at: datetime = field(default_factory=datetime.utcnow)
    maps: list[MatchMap] = field(default_factory=list)


