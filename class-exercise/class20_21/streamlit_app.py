import logging

import pandas as pd
import requests
import streamlit as st

if __package__:
    from .api_client import fetch_records
else:
    from api_client import fetch_records

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Movie Explorer", layout="wide")
st.title("Movie Explorer")
st.write("Explore genre summaries and yearly rating trends.")

st.header("Which genres have the highest average ratings?")
min_movies = st.slider("Minimum movies per genre", 1, 6, 3)
try:
    records = fetch_records("/analysis/genres", {"min_movies": min_movies})
except requests.RequestException as error:
    logger.warning("Cannot retrieve genre summary: %s", error)
    st.error("Cannot load genre data. Check that the API is running.")
    st.stop()

if not records:
    st.info("No genres match this minimum movie count.")
else:
    genre_df = pd.DataFrame(records)
    st.dataframe(genre_df, hide_index=True)
    st.bar_chart(genre_df, x="genre", y="average_rating")
    logger.info("Displayed genre summary: groups=%d", len(genre_df))

st.header("How have ratings changed over time?")
window = st.slider("Rolling window (yearly observations)", 1, 6, 3)
try:
    records = fetch_records("/analysis/years", {"window": window})
except requests.RequestException as error:
    logger.warning("Cannot retrieve yearly trend: %s", error)
    st.error("Cannot load yearly data. Check that the API is running.")
    st.stop()

if not records:
    st.info("No yearly rating data is available.")
else:
    year_df = pd.DataFrame(records)
    st.dataframe(year_df, hide_index=True)
    st.line_chart(year_df, x="release_year", y=["average_rating", "rolling_rating"])
    logger.info("Displayed yearly trend: years=%d, window=%d", len(year_df), window)

st.header("Which movies meet your minimum rating?")
min_rating = st.slider("Minimum movie rating", 0.0, 10.0, 8.0, 0.5)
try:
    records = fetch_records("/movies/filter", {"min_rating": min_rating})
except requests.RequestException as error:
    logger.warning("Cannot retrieve filtered movies: %s", error)
    st.error("Cannot load movies. Check that the API is running.")
    st.stop()

if not records:
    st.info("No movies meet this minimum rating.")
else:
    st.dataframe(pd.DataFrame(records), hide_index=True)
    logger.info("Displayed movies: rows=%d, min_rating=%s", len(records), min_rating)
