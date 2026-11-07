import logging

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

if __package__:
    from .check_storage import BookStorage
else:
    from check_storage import BookStorage

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class BookInput(BaseModel):
    title: str
    price: float = Field(ge=0, allow_inf_nan=False)


class BookResponse(BookInput):
    id: int


app = FastAPI(title="Books Database API")
storage = BookStorage()


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int):
    book = storage.get_book(book_id)
    if book is None:
        logger.warning("Book not found: %d", book_id)
        raise HTTPException(status_code=404, detail="Book not found")
    logger.info("Retrieved book: id=%d", book_id)
    return book


@app.post("/books", response_model=BookResponse)
def add_book(book: BookInput):
    book_id = storage.add_book(book.title, book.price)
    logger.info("Added book: id=%d", book_id)
    return storage.get_book(book_id)


@app.get("/books", response_model=list[BookResponse])
def list_books(min_price: float = Query(default=0, ge=0), limit: int = Query(default=100, ge=1)):
    books = storage.list_books(min_price=min_price, limit=limit)
    logger.info("Listed %d books", len(books))
    return books


@app.get("/search/books", response_model=list[BookResponse])
def search_books(min_price: float = Query(ge=0), max_price: float = Query(ge=0)):
    if min_price > max_price:
        logger.warning("Reversed price range: %s to %s", min_price, max_price)
        raise HTTPException(status_code=400, detail="min_price must not exceed max_price")
    books = storage.search_books(min_price, max_price)
    logger.info("Found %d books in price range", len(books))
    return books
