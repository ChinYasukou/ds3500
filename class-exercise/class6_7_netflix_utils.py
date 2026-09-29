import logging

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
