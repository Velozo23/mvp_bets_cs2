from config import (
    DISCOVERY_CATALOG_PAGES,
    DISCOVERY_MAX_DEPTH,
    DISCOVERY_RENDERED_CATALOG_PAGES,
    DISCOVERY_YEARS_BACK,
    ORGANIZER_PAGE_PREFIXES,
    TARGET_PAGES,
)
from database import Database
from liquipedia_client import LiquipediaClient
from liquipedia_parser import LiquipediaMatchParser
from repository import MatchRepository
from validators import MatchValidator


BLOCKING_WARNINGS = {
    "Team 1 name is missing.",
    "Team 2 name is missing.",
    "Match datetime is missing.",
}


def has_blocking_warning(warnings):
    for warning in warnings:
        if warning in BLOCKING_WARNINGS:
            return True

    return False


def collect_page(page_title, client, parser, validator, repository):
    print("-" * 80)
    print(f"Collecting data for page: {page_title}")
    print("-" * 80)

    wikitext = client.get_page_content(page_title)

    if not wikitext:
        print("Nenhum conteudo encontrado para a pagina.")
        return 0
    
    series_list = parser.parse_page(wikitext, page_title)

    print(f"Series encontradas: {len(series_list)}")

    saved_count = 0
    skipped_count = 0

    for series in series_list:
        warnings = validator.validate_series(series)

        if has_blocking_warning(warnings):
            print(f"Ignorando serie invalida: {series.team1_name} vs {series.team2_name}")
            for warning in warnings:
                print(f"  - {warning}")

            skipped_count += 1
            continue

        if warnings:
            print(f"Warnings em {series.team1_name} vs {series.team2_name}:")
            for warning in warnings:
                print(f"  - {warning}")

        repository.save_full_series(series)
        saved_count += 1
        
    print(f"Series salvas: {saved_count}")
    print(f"Series ignoradas: {skipped_count}")

    return saved_count


def discover_pages(
    client,
    initial_pages,
    catalog_pages=None,
    rendered_catalog_pages=None,
    organizer_prefixes=None,
    max_depth=DISCOVERY_MAX_DEPTH,
):
    """
    Descobre eventos das organizadoras configuradas a partir de catalogos.

    As paginas explicitas continuam sendo coletadas. Eventos encontrados no
    catalogo entram em uma fila limitada, que permite localizar uma camada de
    subpaginas como Qualifier, Playoffs e Stage sem rastrear a wiki inteira.
    """
    catalog_pages = catalog_pages or DISCOVERY_CATALOG_PAGES
    if rendered_catalog_pages is None:
        rendered_catalog_pages = DISCOVERY_RENDERED_CATALOG_PAGES
    organizer_prefixes = organizer_prefixes or ORGANIZER_PAGE_PREFIXES
    discovered = set(initial_pages)
    queue = []
    visited = set()

    for catalog_page in catalog_pages:
        wikitext = client.get_page_content(catalog_page)
        candidates = client.extract_candidate_pages(wikitext)
        relevant = client.filter_organizer_pages(
            candidates,
            organizer_prefixes,
            years_back=DISCOVERY_YEARS_BACK,
        )
        queue.extend((page, 0) for page in relevant)

    for catalog_page in rendered_catalog_pages:
        candidates = client.get_page_links(catalog_page)
        relevant = client.filter_organizer_pages(
            candidates,
            organizer_prefixes,
            years_back=DISCOVERY_YEARS_BACK,
        )
        queue.extend((page, 0) for page in relevant)

    # Sementes explicitas tambem podem revelar subpaginas.
    queue.extend((page, 0) for page in initial_pages)

    while queue:
        page_title, depth = queue.pop(0)
        if page_title in visited:
            continue
        visited.add(page_title)

        wikitext = client.get_page_content(page_title)
        if not wikitext:
            continue

        if client.has_match_content(wikitext):
            discovered.add(page_title)

        if depth >= max_depth:
            continue

        candidates = client.extract_candidate_pages(wikitext)
        relevant = client.filter_organizer_pages(
            candidates,
            organizer_prefixes,
            years_back=DISCOVERY_YEARS_BACK,
        )
        queue.extend((page, depth + 1) for page in relevant if page not in visited)

    return sorted(discovered)


def main():
    database = Database()
    database.initialize()

    client = LiquipediaClient()
    parser = LiquipediaMatchParser()
    validator = MatchValidator()
    repository = MatchRepository(database)

    initial_pages = list(TARGET_PAGES)
    pages_to_collect = discover_pages(client, initial_pages)

    print(f"Paginas descobertas: {len(pages_to_collect)}")

    total_saved = 0

    for page_title in pages_to_collect:
        saved_count = collect_page(
            page_title,
            client,
            parser,
            validator,
            repository
        )

        total_saved += saved_count

    print("-" * 80)
    print(f"Total de series salvas: {total_saved}")
    print("-" * 80)

    return total_saved > 0

if __name__ == "__main__":
    main()
