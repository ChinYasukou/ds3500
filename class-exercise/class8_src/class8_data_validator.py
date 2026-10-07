import logging

logger = logging.getLogger(__name__)


def require_columns(df, required_columns):
    """Check that all required columns exist."""
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]
    if missing_columns:
        logger.error("Missing required columns: %s", missing_columns)
        raise ValueError(f"Missing required columns: {missing_columns}")

    logger.info("Validation completed")
    return df
