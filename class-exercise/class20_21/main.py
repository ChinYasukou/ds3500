import logging

import pandas as pd
from fastapi import FastAPI, Query

if __package__:
    from .check_analysis import DATA_PATH, summarize_genres, summarize_years
else:
    from check_analysis import DATA_PATH, summarize_genres, summarize_years

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
app = FastAPI(title="Movie Analysis API")


@app.get("/analysis/genres", response_model=list[dict])
def get_genres(min_movies: int = Query(default=1, ge=1)):
    result = summarize_genres(pd.read_csv(DATA_PATH), min_movies=min_movies)
    logger.info("Returned genre summary: groups=%d", len(result))
    return result.to_dict(orient="records")


@app.get("/analysis/years", response_model=list[dict])
def get_years(window: int = Query(default=3, ge=1)):
    result = summarize_years(pd.read_csv(DATA_PATH), window=window)
    logger.info("Returned year summary: years=%d, window=%d", len(result), window)
    return result.to_dict(orient="records")
