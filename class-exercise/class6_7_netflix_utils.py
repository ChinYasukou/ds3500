import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)


def show_overview(df):
    """Display basic information about a DataFrame."""
    logger.debug("DataFrame shape: %s", df.shape)
    print(f"Shape: {df.shape}")
    print("First five rows:")
    print(df.head())
    print(f"Columns: {list(df.columns)}")
    print("Data types:")
    print(df.dtypes)


def remove_duplicates(df):
    """Remove exact duplicate rows."""
    before_count = len(df)
    result = df.drop_duplicates()
    logger.debug(
        "Removed duplicates: %d row(s) before, %d row(s) after",
        before_count,
        len(result),
    )
    return result


def drop_missing_rows(df):
    """Remove rows containing missing values."""
    before_count = len(df)
    result = df.dropna()
    logger.debug(
        "Dropped missing rows: %d row(s) before, %d row(s) after",
        before_count,
        len(result),
    )
    return result


def clean_text(value):
    """Normalize one text value."""
    value = value.strip().lower()
    return re.sub(r"\s+", " ", value)


def remove_iqr_outliers(df, column, threshold):
    """Remove IQR outliers from one column."""
    if column not in df.columns:
        logger.error("Column not found: %s", column)
        raise ValueError(f"Column not found: {column}")

    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - threshold * iqr
    upper_bound = q3 + threshold * iqr
    result = df[df[column].between(lower_bound, upper_bound)]

    logger.debug(
        "IQR bounds for %s: lower=%s, upper=%s; removed %d row(s)",
        column,
        lower_bound,
        upper_bound,
        len(df) - len(result),
    )
    return result
