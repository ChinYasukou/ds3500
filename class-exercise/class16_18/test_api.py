import sqlite3

import pytest
from fastapi.testclient import TestClient

from . import main
from .check_storage import BookStorage


@pytest.fixture
def storage(tmp_path):
    return BookStorage(tmp_path / "books.db")


@pytest.fixture
def client(storage, monkeypatch):
    monkeypatch.setattr(main, "storage", storage)
    monkeypatch.setattr(main, "cache", main.BookCache())
    with TestClient(main.app) as test_client:
        yield test_client


def test_storage_persists(storage):
    book_id = storage.add_book("Book A", 12.5)
    assert BookStorage(storage.db_path).get_book(book_id) == {
        "id": book_id, "title": "Book A", "price": 12.5,
    }


def test_failed_replacement_rolls_back(storage):
    storage.add_book("Book A", 12.5)
    storage.add_book("Book B", 25.0)
    before = storage.list_books()

    with pytest.raises(sqlite3.IntegrityError):
        storage.replace_books([("New Book", 20.0), (None, 10.0)])

    assert BookStorage(storage.db_path).list_books() == before


def test_add_and_get_book(client):
    response = client.post("/books", json={"title": "Book A", "price": 12.5})
    assert response.status_code == 200
    book = response.json()
    assert book == {"id": 1, "title": "Book A", "price": 12.5}
    assert client.get("/books/1").json() == book
    assert client.get("/books/999").status_code == 404
    assert client.post("/books", json={"title": "Invalid", "price": -1}).status_code == 422


def test_list_filters_sorts_and_limits(client, storage):
    for title, price in [("Low", 10), ("First", 20), ("Second", 20), ("Middle", 15)]:
        storage.add_book(title, price)

    response = client.get("/books", params={"min_price": 15, "limit": 2})
    assert response.status_code == 200
    assert [book["title"] for book in response.json()] == ["First", "Second"]
    assert client.get("/books?min_price=100").json() == []
    assert client.get("/books?limit=0").status_code == 422


@pytest.mark.parametrize("low,high,titles", [
    (10, 20, ["High", "Middle", "Low"]),
    (15, 15, ["Middle"]),
    (100, 200, []),
])
def test_search_includes_boundaries(client, storage, low, high, titles):
    for title, price in [("Low", 10), ("Middle", 15), ("High", 20)]:
        storage.add_book(title, price)

    response = client.get("/search/books", params={"min_price": low, "max_price": high})
    assert response.status_code == 200
    assert [book["title"] for book in response.json()] == titles


def test_search_validates_range(client):
    assert client.get("/search/books?min_price=20&max_price=10").status_code == 400
    assert client.get("/search/books?min_price=-1&max_price=10").status_code == 422
    assert client.get("/search/books?min_price=10").status_code == 422


def test_cache_hit_skips_database(client, monkeypatch):
    assert client.post("/books", json={"title": "Book A", "price": 12.5}).status_code == 200
    first = client.get("/books", params={"min_price": 0, "limit": 100})
    assert first.status_code == 200

    def fail_if_called(*args, **kwargs):
        pytest.fail("A cache hit should not query the database")

    monkeypatch.setattr(main.storage, "list_books", fail_if_called)
    second = client.get("/books", params={"min_price": 0, "limit": 100})
    assert second.status_code == 200
    assert second.json() == first.json()


def test_add_book_invalidates_cache(client):
    assert client.post("/books", json={"title": "Book A", "price": 12.5}).status_code == 200
    for limit in (1, 100):
        response = client.get("/books", params={"min_price": 0, "limit": limit})
        assert response.status_code == 200
        assert main.cache.get(0, limit) == response.json()
    previous = client.get("/books?min_price=0&limit=100").json()
    assert previous == main.cache.get(0, 100)

    assert client.post("/books", json={"title": "Book B", "price": 20}).status_code == 200
    assert main.cache.get(0, 1) is None
    assert main.cache.get(0, 100) is None
    response = client.get("/books?min_price=0&limit=100")
    assert response.status_code == 200
    assert [(book["title"], book["price"]) for book in response.json()] == [
        ("Book B", 20.0), ("Book A", 12.5),
    ]
    assert main.cache.get(0, 100) == response.json()


def test_cached_empty_list_skips_database(client, monkeypatch):
    assert client.get("/books?min_price=999").json() == []

    def fail_if_called(*args, **kwargs):
        pytest.fail("An empty cached list is still a cache hit")

    monkeypatch.setattr(main.storage, "list_books", fail_if_called)
    assert client.get("/books?min_price=999").json() == []


def test_cache_keys_and_expiration():
    cache = main.BookCache()
    assert cache.make_key(0, 100) == cache.make_key(0.0, 100)
    assert cache.make_key(1, 100) != cache.make_key(0, 100)
    assert cache.make_key(0, 1) != cache.make_key(0, 100)
    cache.set(0, 100, [])
    key = cache.make_key(0, 100)
    assert 0 < cache.client.ttl(key) <= 60
    cache.client.expire(key, 0)
    assert cache.get(0, 100) is None
