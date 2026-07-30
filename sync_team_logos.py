"""Sincroniza para o disco os logos oficiais dos times usados nas partidas."""

from __future__ import annotations

import argparse
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import API_BASE_URL, TEAM_LOGOS_DIR
from database import Database
from liquipedia_client import LiquipediaClient
from team_repository import TeamRepository, normalize_team_name


SAFE_ALIAS = re.compile(r"^[\w .-]{1,80}$", re.UNICODE)


@dataclass(frozen=True)
class ResolvedLogo:
    alias: str
    canonical_name: str
    liquipedia_page: str | None
    source_url: str
    theme: str


def build_logo_lookup_wikitext(aliases: list[str]) -> str:
    blocks = []
    for index, alias in enumerate(aliases):
        if not SAFE_ALIAS.fullmatch(alias):
            continue
        blocks.append(f'<div id="mvp-team-{index}">{{{{TeamIcon|{alias}}}}}</div>')
    return "\n".join(blocks)


def _largest_image_url(image) -> str | None:
    srcset = image.get("srcset", "")
    candidates = [
        item.strip().split(" ")[0]
        for item in srcset.split(",")
        if item.strip()
    ]
    return candidates[-1] if candidates else image.get("src")


def parse_logo_lookup_html(html: str, aliases: list[str]) -> list[ResolvedLogo]:
    soup = BeautifulSoup(html or "", "html.parser")
    resolved = []

    for index, alias in enumerate(aliases):
        container = soup.find(id=f"mvp-team-{index}")
        if container is None:
            continue

        team = container.select_one("[data-highlightingclass]")
        canonical_name = team.get("data-highlightingclass") if team else None
        if not canonical_name:
            continue

        image = container.select_one(".darkmode img") or container.select_one("img")
        source_url = _largest_image_url(image) if image else None
        if not source_url:
            continue

        link = container.select_one('a[href^="/counterstrike/"]')
        page = link.get("href") if link else None
        theme = "dark" if container.select_one(".darkmode img") else "all"
        resolved.append(
            ResolvedLogo(
                alias=alias,
                canonical_name=canonical_name,
                liquipedia_page=urljoin(API_BASE_URL, page) if page else None,
                source_url=urljoin(API_BASE_URL, source_url),
                theme=theme,
            )
        )

    return resolved


def resolve_logos(client: LiquipediaClient, aliases: list[str]) -> list[ResolvedLogo]:
    wikitext = build_logo_lookup_wikitext(aliases)
    params = {
        "action": "parse",
        "format": "json",
        "formatversion": "2",
        "title": "MVP Bets team logo lookup",
        "text": wikitext,
        "contentmodel": "wikitext",
        "prop": "text",
    }
    data = client.request(params, is_parse=True)
    html = data.get("parse", {}).get("text", "")
    return parse_logo_lookup_html(html, aliases)


def logo_extension(source_url: str, content_type: str | None) -> str:
    original_path = urlparse(source_url).path.split("/thumb/", 1)[-1]
    original_name = original_path.split("/", 2)[-1].split("/")[0]
    suffix = Path(original_name).suffix.lower()
    if suffix in {".png", ".webp", ".jpg", ".jpeg"}:
        return suffix
    return mimetypes.guess_extension((content_type or "").split(";", 1)[0]) or ".img"


def download_logo(client: LiquipediaClient, logo: ResolvedLogo, output_dir: Path) -> str:
    response = client.get_binary(logo.source_url)
    content_type = response.headers.get("Content-Type")
    if not content_type or not content_type.startswith("image/"):
        raise ValueError(f"Resposta não é uma imagem: {logo.source_url}")
    if len(response.content) > 5 * 1024 * 1024:
        raise ValueError(f"Logo excede 5 MB: {logo.canonical_name}")

    extension = logo_extension(logo.source_url, content_type)
    filename = f"{normalize_team_name(logo.canonical_name)}-{logo.theme}{extension}"
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary = output_dir / f".{filename}.tmp"
    destination = output_dir / filename
    temporary.write_bytes(response.content)
    temporary.replace(destination)
    return filename


def sync(force: bool = False) -> tuple[int, list[str]]:
    database = Database()
    database.initialize()
    repository = TeamRepository(database)
    client = LiquipediaClient()
    aliases = repository.discover_match_aliases()
    resolved = resolve_logos(client, aliases)
    failures = []
    downloaded = {}
    saved = 0

    for logo in resolved:
        try:
            key = (logo.canonical_name, logo.source_url)
            if key not in downloaded:
                existing = repository.find_by_alias(logo.alias)
                existing_file = (
                    Path(TEAM_LOGOS_DIR) / existing["logo_filename"]
                    if existing and existing["logo_filename"]
                    else None
                )
                if not force and existing_file and existing_file.is_file():
                    downloaded[key] = existing_file.name
                else:
                    downloaded[key] = download_logo(
                        client, logo, Path(TEAM_LOGOS_DIR)
                    )

            repository.save_team_logo(
                alias=logo.alias,
                canonical_name=logo.canonical_name,
                liquipedia_page=logo.liquipedia_page,
                logo_filename=downloaded[key],
                logo_source_url=logo.source_url,
                logo_theme=logo.theme,
            )
            saved += 1
            print(f"[OK] {logo.alias} -> {logo.canonical_name}")
        except Exception as error:
            failures.append(f"{logo.alias}: {error}")
            print(f"[ERRO] {failures[-1]}")

    unresolved = sorted(set(aliases) - {logo.alias for logo in resolved})
    for alias in unresolved:
        failures.append(f"{alias}: logo não encontrado na Liquipedia")
        print(f"[AVISO] {failures[-1]}")

    return saved, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Baixa novamente logos que já existem no cache.",
    )
    args = parser.parse_args()
    saved, failures = sync(force=args.force)
    print(f"\nTimes sincronizados: {saved}")
    print(f"Não sincronizados: {len(failures)}")


if __name__ == "__main__":
    main()
