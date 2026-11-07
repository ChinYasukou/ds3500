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
