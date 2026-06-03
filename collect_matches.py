from config import TARGET_PAGES
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


def main():
    database = Database()
    database.initialize()

    client = LiquipediaClient()
    parser = LiquipediaMatchParser()
    validator = MatchValidator()
    repository = MatchRepository(database)

    total_saved = 0

    for page_title in TARGET_PAGES:
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


