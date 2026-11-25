import sys
from pathlib import Path

import pytest
import requests
from streamlit.testing.v1 import AppTest

from . import api_client


SCRIPT = Path(__file__).with_name("streamlit_app.py")


@pytest.fixture
def app_runner(monkeypatch):
    monkeypatch.setitem(sys.modules, "api_client", api_client)

    def run(fetch):
        monkeypatch.setattr(api_client, "fetch_records", fetch)
        return AppTest.from_file(str(SCRIPT), default_timeout=15).run()

    return run


def test_sliders_send_parameters_and_empty_genres_keep_years(app_runner):
    calls = []

    def fetch(endpoint, params):
        calls.append((endpoint, params))
        if endpoint == "/analysis/genres":
            if params["min_movies"] == 6:
                return []
            return [{"genre": "Comedy", "movie_count": 3, "average_rating": 8.0}]
        if endpoint == "/analysis/years":
            return [{"release_year": 2024, "average_rating": 9.0, "rolling_rating": 8.67}]
        return [{"title": "Movie J", "release_year": 2023, "rating": 10.0, "genre": "Documentary"}]

    app = app_runner(fetch)
    assert not app.exception
    assert len(app.dataframe) == 3
    assert ("/analysis/years", {"window": 3}) in calls
    app.slider[0].set_value(6).run()
    assert not app.exception
    assert app.info[0].value == "No genres match this minimum movie count."
    assert len(app.dataframe) == 2
    app.slider[1].set_value(1).run()
    app.slider[2].set_value(10.0).run()
    assert ("/analysis/years", {"window": 1}) in calls
    assert ("/movies/filter", {"min_rating": 10.0}) in calls


def test_empty_results_show_messages(app_runner):
    app = app_runner(lambda endpoint, params: [])
    assert not app.exception
    assert len(app.info) == 3
    assert not app.dataframe


@pytest.mark.parametrize("failed_endpoint", ["/analysis/genres", "/analysis/years", "/movies/filter"])
def test_api_failure_shows_error_without_traceback(app_runner, failed_endpoint):
    def fetch(endpoint, params):
        if endpoint == failed_endpoint:
            raise requests.ConnectionError("API unavailable")
        return []

    app = app_runner(fetch)
    assert not app.exception
    assert len(app.error) == 1
    assert "Check that the API is running." in app.error[0].value


def test_fetch_records_passes_query_and_timeout(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            calls.append("checked")

        def json(self):
            assert "checked" in calls
            return [{"title": "Movie A"}]

    def get(url, **kwargs):
        assert url == api_client.API_URL + "/movies/filter"
        assert kwargs == {"params": {"min_rating": 8}, "timeout": 10}
        return Response()

    monkeypatch.setattr(api_client.requests, "get", get)
    assert api_client.fetch_records("/movies/filter", {"min_rating": 8}) == [{"title": "Movie A"}]
