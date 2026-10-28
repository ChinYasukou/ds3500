import io
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from middleware import log_requests
from src import CSVInfo, DataStorage, MovieInput, MovieResponse, ProcessConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Movie API")
app.middleware("http")(log_requests)

movies = {
    1: {"id": 1, "title": "Movie A", "release_year": 2020},
    2: {"id": 2, "title": "Movie B", "release_year": 2021},
}
demo_movie_examples = []
storage = DataStorage()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/demo/movies/{movie_id}")
def demo_get_movie(movie_id: int):
    return {"requested_id": movie_id}


@app.get("/demo/movies")
def demo_list_movies(limit: int = Query(default=2, ge=1)):
    return {"requested_limit": limit}


@app.post("/demo/movies")
def demo_add_movie(movie: MovieInput):
    return movie.model_dump()


@app.post("/demo/movie-examples", response_model=MovieResponse)
def demo_add_movie_example(movie: MovieInput):
    movie_id = len(demo_movie_examples) + 1
    record = movie.model_dump()
    record["id"] = movie_id
    demo_movie_examples.append(record)
    return record


@app.get("/movies", response_model=list[MovieResponse])
def list_movies(limit: int = Query(default=2, ge=1)):
    records = list(movies.values())[:limit]
    logger.info("Returned %d movies", len(records))
    return records


@app.post("/movies", response_model=MovieResponse)
def add_movie(movie: MovieInput):
    movie_id = len(movies) + 1
    record = movie.model_dump()
    record["id"] = movie_id
    movies[movie_id] = record
    logger.info("Added movie: id=%d", movie_id)
    return record


@app.post("/demo/inspect-csv")
async def demo_inspect_csv(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size_bytes": len(contents)}


@app.get("/demo/movie-lookup/{movie_id}", response_model=MovieResponse)
def demo_lookup_movie(movie_id: int):
    movie = movies.get(movie_id)
    if movie is None:
        logger.warning("Movie not found: %d", movie_id)
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.post("/inspect-csv", response_model=CSVInfo)
async def inspect_csv(file: UploadFile = File(...)):
    filename = file.filename or ""
    if Path(filename).suffix.lower() != ".csv":
        logger.warning("Unsupported file extension: %s", filename)
        raise HTTPException(status_code=400, detail="Upload a CSV file")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning("Cannot read CSV: %s", error)
        raise HTTPException(
            status_code=400, detail="Cannot read the uploaded CSV"
        ) from error

    dataset_id = storage.save_data(df, filename)
    logger.info("Stored CSV: id=%d, filename=%s", dataset_id, filename)
    return CSVInfo(
        filename=filename,
        rows=df.shape[0],
        columns=df.shape[1],
        column_names=list(df.columns),
        dataset_id=dataset_id,
    )


@app.get("/datasets/{dataset_id}/shape")
def get_dataset_shape(dataset_id: int):
    df = storage.get_data(dataset_id)
    if df is None:
        logger.warning("Dataset not found: %d", dataset_id)
        raise HTTPException(status_code=404, detail="Dataset not found")
    logger.info("Retrieved dataset shape: id=%d", dataset_id)
    return {"dataset_id": dataset_id, "rows": df.shape[0], "columns": df.shape[1]}


@app.post("/demo/process-config")
def demo_process_config(config: ProcessConfig):
    df = pd.DataFrame({"title": ["Movie A", "Movie A", "Movie B", None]})
    settings = config.model_dump()
    if settings["processing"]["remove_duplicates"]:
        df = df.drop_duplicates()
    if settings["processing"]["drop_missing"]:
        df = df.dropna()
    return {"rows": len(df)}
