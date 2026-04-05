"""Tests for ragwatch observability service."""

import pytest
from fastapi.testclient import TestClient

from ragwatch import app


@pytest.fixture
def client():
    return TestClient(app)


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_returns_prometheus_format(self, client):
        resp = client.get("/metrics")
        assert b"ragwatch" in resp.content

    def test_metrics_content_type_is_plain_text(self, client):
        resp = client.get("/metrics")
        assert "text/plain" in resp.headers["content-type"]


class TestMetricsSummary:
    def test_summary_returns_200(self, client):
        resp = client.get("/metrics/summary")
        assert resp.status_code == 200

    def test_summary_returns_json(self, client):
        resp = client.get("/metrics/summary")
        assert resp.headers["content-type"] == "application/json"

    def test_summary_has_required_fields(self, client):
        resp = client.get("/metrics/summary")
        data = resp.json()
        assert "status" in data
        assert "timestamp" in data
        assert "sources" in data

    def test_summary_sources_has_ragpipe_and_ragstuffer(self, client):
        resp = client.get("/metrics/summary")
        data = resp.json()
        assert "ragpipe" in data["sources"]
        assert "ragstuffer" in data["sources"]


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        resp = client.get("/health")
        assert resp.headers["content-type"] == "application/json"

    def test_health_status_is_ok_or_degraded(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] in ("ok", "degraded")
