from importlib import import_module

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    analysis_api = import_module(".main", __package__)
    csv_path = tmp_path / "movies.csv"
    pd.DataFrame(
        [
            ("A", 2022, 9, "Drama"),
            ("B", 2020, 6, "Comedy"),
            ("C", 2020, 8, "Drama"),
            ("D", 2021, 7, "Comedy"),
            ("E", 2022, 10, "Documentary"),
        ],
        columns=["title", "release_year", "rating", "genre"],
    ).to_csv(csv_path, index=False)
    monkeypatch.setattr(analysis_api, "DATA_PATH", csv_path)
    return TestClient(analysis_api.app)


def test_genres_filter_small_groups_and_sort(client):
    response = client.get("/analysis/genres", params={"min_movies": 2})
    assert response.status_code == 200
    assert response.json() == [
        {"genre": "Drama", "movie_count": 2, "average_rating": 8.5},
        {"genre": "Comedy", "movie_count": 2, "average_rating": 6.5},
    ]


def test_genres_return_empty_result_when_no_groups_qualify(client):
    response = client.get("/analysis/genres", params={"min_movies": 3})
    assert response.status_code == 200
    assert response.json() == []


def test_years_use_requested_window_on_sorted_yearly_means(client):
    response = client.get("/analysis/years", params={"window": 2})
    assert response.status_code == 200
    assert response.json() == [
        {"release_year": 2020, "average_rating": 7.0, "rolling_rating": 7.0},
        {"release_year": 2021, "average_rating": 7.0, "rolling_rating": 7.0},
        {"release_year": 2022, "average_rating": 9.5, "rolling_rating": 8.25},
    ]


@pytest.mark.parametrize("path", ["/analysis/genres?min_movies=0", "/analysis/years?window=0"])
def test_analysis_rejects_nonpositive_parameters(client, path):
    assert client.get(path).status_code == 422


@pytest.mark.parametrize("minimum,titles", [
    (0, ["A", "B", "C", "D", "E"]),
    (8, ["A", "C", "E"]),
    (10, ["E"]),
])
def test_filter_movies_preserves_order(client, minimum, titles):
    response = client.get("/movies/filter", params={"min_rating": minimum})
    assert response.status_code == 200
    assert [record["title"] for record in response.json()] == titles
    assert all(record["rating"] >= minimum for record in response.json())
    assert set(response.json()[0]) == {"title", "release_year", "rating", "genre"}


@pytest.mark.parametrize("minimum", [-1, 11])
def test_filter_movies_rejects_invalid_ratings(client, minimum):
    assert client.get("/movies/filter", params={"min_rating": minimum}).status_code == 422
