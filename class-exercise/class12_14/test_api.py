import logging
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_requests_have_different_ids(client):
    first = client.get("/health").headers.get("X-Request-ID")
    second = client.get("/health").headers.get("X-Request-ID")
    assert first and second
    assert re.fullmatch(r"[0-9a-f]{8}", first)
    assert re.fullmatch(r"[0-9a-f]{8}", second)
    assert first != second


@pytest.mark.parametrize("duplicates,missing,rows", [
    (True, True, 2), (True, False, 3),
    (False, True, 3), (False, False, 4),
])
def test_processing_settings(client, duplicates, missing, rows):
    response = client.post("/demo/process-config", json={
        "processing": {"remove_duplicates": duplicates, "drop_missing": missing}
    })
    assert response.status_code == 200
    assert response.json() == {"rows": rows}


def test_default_processing_settings(client):
    response = client.post("/demo/process-config", json={})
    assert response.status_code == 200
    assert response.json() == {"rows": 2}


@pytest.mark.parametrize("path,status,level", [
    ("/health", 200, logging.INFO),
    ("/datasets/999999/shape", 404, logging.WARNING),
    ("/datasets/abc/shape", 422, logging.WARNING),
])
def test_request_summary_matches_response(client, caplog, path, status, level):
    with caplog.at_level(logging.INFO, logger="middleware"):
        response = client.get(path)
    assert response.status_code == status
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    summaries = [record for record in caplog.records if record.name == "middleware"]
    assert len(summaries) == 1
    assert summaries[0].levelno == level
    message = summaries[0].getMessage()
    assert f"request_id={request_id} GET {path} status={status}" in message
    assert re.search(r"duration=\d+\.\dms", message)


def test_unexpected_exception_is_logged_and_returns_safe_response(caplog):
    from middleware import log_requests

    test_app = FastAPI()
    test_app.middleware("http")(log_requests)

    @test_app.get("/fail")
    def fail():
        raise RuntimeError("private diagnostic")

    with caplog.at_level(logging.INFO, logger="middleware"):
        with TestClient(test_app) as test_client:
            response = test_client.get("/fail")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    request_id = response.headers["X-Request-ID"]
    records = [record for record in caplog.records if record.name == "middleware"]
    assert any(record.exc_info and request_id in record.getMessage() for record in records)
    assert any(record.levelno == logging.ERROR and "status=500" in record.getMessage() for record in records)
