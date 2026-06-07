"""
Inspecao dos dados armazenados no SQLite usando pandas.
"""

import pandas as pd

from database import Database


def load_data(connection):
    series_df = pd.read_sql_query(
        "SELECT * FROM match_series",
        connection,
    )

    maps_df = pd.read_sql_query(
        "SELECT * FROM match_maps",
        connection,
    )

    return series_df, maps_df


def print_summary(series_df, maps_df):
    print("-" * 80)
    print("RESUMO DO BANCO")
    print(f"Total de series: {len(series_df)}")
    print(f"Total de mapas: {len(maps_df)}")

    print("\nSeries por campeonato:")
    print(series_df.groupby("page_title").size())


def print_valid_matches(series_df):
    valid_matches = series_df[
        series_df["team1_name"].notna()
        & series_df["team2_name"].notna()
        & series_df["match_datetime_raw"].notna()
        & series_df["match_datetime_raw"].ne("")
    ]

    columns = [
        "id",
        "page_title",
        "team1_name",
        "series_score_team1",
        "series_score_team2",
        "team2_name",
        "series_type",
        "series_winner",
    ]

    print("\nPARTIDAS VALIDAS")
    print(valid_matches[columns].to_string(index=False))



def print_invalid_matches(series_df):
    invalid_matches = series_df[
        series_df["team1_name"].isna()
        | series_df["team2_name"].isna()
        | series_df["match_datetime_raw"].isna()
        | series_df["match_datetime_raw"].eq("")
    ]

    print("\nREGISTROS INVALIDOS")
    print(invalid_matches.to_string(index=False))



def main():
    database = Database()
    connection = database.get_connection()

    try:
        series_df, maps_df = load_data(connection)

        print_summary(series_df, maps_df)
        print_valid_matches(series_df)
        print_invalid_matches(series_df)

    finally:
        connection.close()


if __name__ == "__main__":
    main()