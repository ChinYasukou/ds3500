import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parent / "data" / "books.db"
INSERT_BOOK = "INSERT INTO books (title, price) VALUES (?, ?)"
SELECT_BOOK = "SELECT id, title, price FROM books WHERE id = ?"
CREATE_BOOKS = """
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL
    )
"""


class BookStorage:
    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute(CREATE_BOOKS)
            connection.commit()
        finally:
            connection.close()

    def add_book(self, title, price):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.execute(INSERT_BOOK, (title, price))
            book_id = cursor.lastrowid
            connection.commit()
            logger.debug("Added book: id=%d", book_id)
            return book_id
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_book(self, book_id):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(SELECT_BOOK, (book_id,)).fetchone()
            logger.debug("Get book: id=%s, found=%s", book_id, row is not None)
            return dict(row) if row is not None else None
        finally:
            connection.close()

    def list_books(self, min_price=0, limit=100):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                SELECT id, title, price FROM books
                WHERE price >= ? ORDER BY price DESC, id ASC LIMIT ?
                """,
                (min_price, limit),
            ).fetchall()
            logger.debug("Listed %d books", len(rows))
            return [dict(row) for row in rows]
        finally:
            connection.close()


    def replace_books(self, books):
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("DELETE FROM books")
            cursor = connection.executemany(INSERT_BOOK, books)
            connection.commit()
            logger.debug("Replaced books: rows=%d", cursor.rowcount)
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()

    def search_books(self, min_price, max_price):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                SELECT id, title, price FROM books
                WHERE price >= ? AND price <= ?
                ORDER BY price DESC, id ASC
                """,
                (min_price, max_price),
            ).fetchall()
            logger.debug("Found %d books in price range", len(rows))
            return [dict(row) for row in rows]
        finally:
            connection.close()


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(CREATE_BOOKS)
        # Reset the classroom sample so repeated runs give the same output.
        connection.execute("DELETE FROM books")
        connection.commit()

        book_id = connection.execute(INSERT_BOOK, ("Book A", 12.5)).lastrowid
        connection.commit()
        connection.execute(INSERT_BOOK, ("Book B", 25.0))
        connection.execute(INSERT_BOOK, ("Book C", 18.0))
        connection.commit()
        connection.executemany(INSERT_BOOK, [("Book D", 15.0), ("Book E", 10.0)])
        connection.commit()

        row = connection.execute(SELECT_BOOK, (book_id,)).fetchone()
        print(dict(row))
        rows = connection.execute("SELECT * FROM books ORDER BY id LIMIT ?", (5,)).fetchall()
        print([dict(row) for row in rows])
        rows = connection.execute(
            "SELECT title, price FROM books WHERE price >= ? ORDER BY price DESC LIMIT ?",
            (15, 2),
        ).fetchall()
        print([dict(row) for row in rows])

        print(connection.execute("SELECT COUNT(*) AS total FROM books").fetchone()["total"])
        connection.execute("UPDATE books SET price = ? WHERE id = ?", (13.0, book_id))
        connection.commit()
        print(connection.execute(SELECT_BOOK, (book_id,)).fetchone()["price"])
        connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        connection.commit()
        print(connection.execute(SELECT_BOOK, (book_id,)).fetchone())
    finally:
        connection.close()

    storage = BookStorage()
    book_id = storage.add_book("Book A", 12.5)
    logger.info("Added book: id=%d", book_id)
    book = storage.get_book(book_id)
    print(book["title"])
    print(book["price"])
    books = storage.list_books(min_price=15, limit=2)
    print([(book["title"], book["price"]) for book in books])

    try:
        storage.replace_books([("New Book", 20.0), (None, 10.0)])
    except sqlite3.IntegrityError:
        print("Replacement failed; original books kept.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    main()
