import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client():
    main.movies.clear()
    main.movies.update({
        1: {"id": 1, "title": "Movie A", "release_year": 2020},
        2: {"id": 2, "title": "Movie B", "release_year": 2021},
    })
    main.demo_movie_examples.clear()
    with TestClient(main.app) as test_client:
        yield test_client


def test_health_and_documentation(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200


def test_movie_workflow(client):
    response = client.get("/movies", params={"limit": 1})
    assert response.status_code == 200
    assert response.json() == [
        {"title": "Movie A", "release_year": 2020, "id": 1}
    ]

    response = client.post("/movies", json={"title": "Movie C", "release_year": 2022})
    assert response.status_code == 200
    assert response.json() == {"title": "Movie C", "release_year": 2022, "id": 3}

    response = client.get("/movies", params={"limit": 10})
    assert response.status_code == 200
    assert [movie["id"] for movie in response.json()] == [1, 2, 3]
    assert len(client.get("/movies").json()) == 2


@pytest.mark.parametrize("body", [{"title": "Movie D"}, {"title": "Movie D", "release_year": "unknown"}])
def test_invalid_movie_body(client, body):
    response = client.post("/movies", json=body)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "release_year"]
    assert len(main.movies) == 2


@pytest.mark.parametrize("path", ["/movies?limit=0", "/demo/movies?limit=0", "/demo/movies/abc"])
def test_invalid_parameters(client, path):
    assert client.get(path).status_code == 422


def test_demo_endpoints(client):
    assert client.get("/demo/movies/2").json() == {"requested_id": 2}
    assert client.get("/demo/movies").json() == {"requested_limit": 2}
    assert client.get("/demo/movies?limit=1").json() == {"requested_limit": 1}
    movie = {"title": "Movie C", "release_year": 2022}
    assert client.post("/demo/movies", json=movie).json() == movie
    assert client.post("/demo/movie-examples", json=movie).json() == {**movie, "id": 1}
    assert client.post("/demo/movie-examples", json=movie).json()["id"] == 2
    assert len(main.movies) == 2


def test_upload_and_retrieve_netflix(client):
    from pathlib import Path
    import pandas as pd

    path = Path(__file__).resolve().parents[1] / "data" / "messy_netflix_titles.csv"
    expected = pd.read_csv(path)
    response = client.post("/inspect-csv", files={"file": (path.name, path.read_bytes(), "text/csv")})
    assert response.status_code == 200
    info = response.json()
    assert info["filename"] == path.name
    assert (info["rows"], info["columns"]) == expected.shape
    assert info["column_names"] == expected.columns.tolist()
    response = client.get(f"/datasets/{info['dataset_id']}/shape")
    assert response.status_code == 200
    assert response.json() == {"dataset_id": info["dataset_id"], "rows": 25, "columns": 7}


@pytest.mark.parametrize("filename,content", [
    ("requirements.txt", b"fastapi"),
    ("empty.csv", b""),
    ("broken.csv", b'title,year\n"unclosed,2020'),
    ("undecodable.csv", b"title\n\xff\xfe"),
])
def test_invalid_csv_upload(client, filename, content):
    response = client.post("/inspect-csv", files={"file": (filename, content)})
    assert response.status_code == 400
    assert "detail" in response.json()
    assert client.get("/health").json() == {"status": "ok"}


def test_missing_dataset_and_invalid_id(client):
    assert client.get("/datasets/999999/shape").status_code == 404
    assert client.get("/datasets/abc/shape").status_code == 422
    assert client.post("/inspect-csv").status_code == 422


def test_class13_demo_endpoints(client):
    response = client.post("/demo/inspect-csv", files={"file": ("demo.csv", b"a\n1\n")})
    assert response.status_code == 200
    assert response.json() == {"filename": "demo.csv", "size_bytes": 4}
    assert client.get("/demo/movie-lookup/1").json()["title"] == "Movie A"
    assert client.get("/demo/movie-lookup/99999").status_code == 404


def test_storage_returns_independent_copies():
    import pandas as pd
    from src import DataStorage

    storage = DataStorage()
    original = pd.DataFrame({"title": ["Movie A"]})
    first = storage.save_data(original, "first.csv")
    second = storage.save_data(original, "second.csv")
    assert (first, second) == (1, 2)
    original.loc[0, "title"] = "changed"
    retrieved = storage.get_data(first)
    assert retrieved.loc[0, "title"] == "Movie A"
    retrieved.loc[0, "title"] = "changed again"
    assert storage.get_data(first).loc[0, "title"] == "Movie A"
    assert storage.get_data(999) is None
