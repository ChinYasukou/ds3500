import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
DATA_PATH = Path(__file__).resolve().parent / "data" / "class20_movies.csv"


def summarize_genres(df, min_movies=1):
    summary = df.groupby("genre", as_index=False).agg(
        movie_count=("title", "count"),
        average_rating=("rating", "mean"),
    )
    summary = summary.loc[summary["movie_count"] >= min_movies].sort_values(
        ["average_rating", "genre"], ascending=[False, True]
    )
    summary["average_rating"] = summary["average_rating"].round(2)
    logger.debug("Genre summary: groups=%d", len(summary))
    return summary


def summarize_years(df, window=3):
    summary = df.groupby("release_year", as_index=False).agg(
        average_rating=("rating", "mean")
    ).sort_values("release_year")
    summary["rolling_rating"] = summary["average_rating"].rolling(
        window=window, min_periods=1
    ).mean()
    columns = ["average_rating", "rolling_rating"]
    summary[columns] = summary[columns].round(2)
    logger.debug("Year summary: years=%d, window=%d", len(summary), window)
    return summary


def filter_movies(df, min_rating):
    columns = ["title", "release_year", "rating", "genre"]
    return df.loc[df["rating"] >= min_rating, columns].copy()


def main():
    df = pd.read_csv(DATA_PATH)
    print(summarize_genres(df).to_string(index=False))
    print(summarize_years(df).to_string(index=False))


if __name__ == "__main__":
    main()
