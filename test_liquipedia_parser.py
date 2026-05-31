from liquipedia_client import LiquipediaClient
from liquipedia_parser import LiquipediaMatchParser
from validators import MatchValidator

PAGE_TITLE = "CS_Asia_Championships/2026"


def print_warnings(warnings):
    if not warnings:
        return

    print("Warnings:")

    for warning in warnings:
        print(f"  - {warning}")


def print_maps(maps):
    for match_map in maps:
        map_name = match_map.map_name or "TBD"

        if match_map.played:
            print(
                f"  Map {match_map.map_order}: "
                f"{map_name} | "
                f"{match_map.team1_score} x {match_map.team2_score} | "
                f"winner={match_map.winner} | "
                f"OT={match_map.had_overtime}"
            )
        else:
            map_status = match_map.map_finished or "not_played"

            print(
                f"  Map {match_map.map_order}: "
                f"{map_name} | "
                f"status={map_status}"
            )


def print_series(series_list, validator):
    print(f"Total de series encontradas: {len(series_list)}")

    for index, series in enumerate(series_list, start=1):
        team1_name = series.team1_name or "TBD"
        team2_name = series.team2_name or "TBD"
        warnings = validator.validate_series(series)

        print("-" * 80)
        print(f"[{index}] {team1_name} vs {team2_name}")
        print(f"Data: {series.match_datetime_raw}")
        print(
            f"Serie: {series.series_type} | "
            f"Score: {series.series_score_team1} x {series.series_score_team2} | "
            f"Winner: {series.series_winner}"
        )

        print_maps(series.maps)
        print_warnings(warnings)


def main():
    client = LiquipediaClient()
    parser = LiquipediaMatchParser()
    validator = MatchValidator()

    print(f"Buscando pagina: {PAGE_TITLE}")

    wikitext = client.get_page_content(PAGE_TITLE)

    if not wikitext:
        print("Nenhum conteudo retornado.")
        return

    series_list = parser.parse_page(wikitext, PAGE_TITLE)

    print_series(series_list, validator)

  
if __name__ == "__main__":
    main()
