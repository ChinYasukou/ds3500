import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from class6_7_netflix_utils import (
    clean_text,
    drop_missing_rows,
    remove_duplicates,
    remove_iqr_outliers,
    show_overview,
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Explore Netflix titles"
    )
    parser.add_argument(
        "--input",
        default="data/messy_netflix_titles.csv",
        help="Path to the Netflix CSV file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show debug messages",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    input_path = Path(args.input)
    try:
        netflix_df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    logger.info(
        "Loaded %d rows and %d columns",
        netflix_df.shape[0],
        netflix_df.shape[1],
    )
    df_original = netflix_df.copy()

    show_overview(netflix_df)
    logger.info("Displayed DataFrame overview")

    before_count = len(netflix_df)
    netflix_df = remove_duplicates(netflix_df)
    logger.info(
        "Removed %d duplicate row(s)",
        before_count - len(netflix_df),
    )

    before_count = len(netflix_df)
    netflix_df = drop_missing_rows(netflix_df)
    logger.info(
        "Dropped %d rows with missing values",
        before_count - len(netflix_df),
    )

    before_count = len(netflix_df)
    try:
        netflix_df = remove_iqr_outliers(
            netflix_df,
            "runtime_minutes",
            1.5,
        )
    except ValueError as error:
        logger.error("Unable to remove outliers: %s", error)
        sys.exit(1)
    logger.info(
        "Removed %d runtime_minutes outlier(s)",
        before_count - len(netflix_df),
    )

    for column in ("title", "type", "country"):
        netflix_df[column] = netflix_df[column].apply(clean_text)
        logger.info("Cleaned text column: %s", column)

    report = {
        "rows_before": len(df_original),
        "rows_after": len(netflix_df),
        "rows_removed": len(df_original) - len(netflix_df),
        "columns": len(netflix_df.columns),
    }
    logger.info("Cleaning complete: %s", report)


if __name__ == "__main__":
    main()
