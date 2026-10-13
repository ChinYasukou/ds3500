import pandas as pd
import pytest

from class10_data_validator import validate_columns


@pytest.fixture
def sample_df():
    """Create a small DataFrame for testing."""
    return pd.DataFrame(
        {
            "title": ["Movie A", "Movie B"],
            "type": ["Movie", "Movie"],
            "release_year": [2020, 2021],
        }
    )


def test_validate_columns_with_valid_columns(sample_df):
    required_columns = ["title", "type", "release_year"]

    result = validate_columns(sample_df, required_columns)

    assert result.columns.tolist() == required_columns
    assert result is sample_df


def test_validate_columns_with_missing_column(sample_df):
    required_columns = ["title", "type", "release_year", "rating"]

    with pytest.raises(ValueError, match="Missing required columns") as error:
        validate_columns(sample_df, required_columns)

    assert "rating" in str(error.value)
