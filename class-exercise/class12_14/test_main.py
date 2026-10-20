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
