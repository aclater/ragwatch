"""Live integration tests for ragwatch.

Tests run against the live ragwatch service (:9090).
Requires ragwatch and upstream services (ragpipe, ragstuffer, ragorchestrator) to be running.

Run with:
    PYTHONPATH=. pytest tests/test_live.py -v --ragwatch-url=http://localhost:9090

Skip in CI (service not available):
    SKIP_LIVE_TESTS=1 pytest tests/test_live.py -v -m "not live"
"""

import os

import httpx
import pytest

RAGWATCH_URL = os.environ.get("RAGWATCH_URL", "http://localhost:9090")
TIMEOUT = 30.0


def _is_ragwatch_available() -> bool:
    try:
        httpx.get(f"{RAGWATCH_URL}/health", timeout=5)
        return True
    except Exception:
        return False


pytestmark = [
    pytest.mark.skipif(
        os.environ.get("SKIP_LIVE_TESTS") == "1" or not _is_ragwatch_available(),
        reason="ragwatch not available — set SKIP_LIVE_TESTS=1 to skip",
    ),
]


@pytest.fixture
def ragwatch_url():
    return RAGWATCH_URL


# ── Health and connectivity ────────────────────────────────────────────────────


def test_health_returns_200(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/health", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")


def test_metrics_returns_prometheus_format(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics", timeout=10)
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text
    assert "ragwatch" in text


def test_metrics_summary_returns_json(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    data = resp.json()
    assert "status" in data
    assert "timestamp" in data
    assert "sources" in data


def test_all_services_scraped(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data = resp.json()
    sources = data.get("sources", {})
    assert "ragpipe" in sources, f"ragpipe not in sources: {list(sources.keys())}"
    assert "ragstuffer" in sources, f"ragstuffer not in sources: {list(sources.keys())}"
    assert "ragorchestrator" in sources, f"ragorchestrator not in sources: {list(sources.keys())}"


# ── Metrics content ───────────────────────────────────────────────────────────


def test_ragpipe_metrics_present(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data = resp.json()
    assert "ragpipe" in data, "ragpipe not in summary"
    pipe_data = data["ragpipe"]
    assert "queries_total" in pipe_data


def test_ragstuffer_metrics_present(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data = resp.json()
    assert "ragstuffer" in data, "ragstuffer not in summary"
    stuffer_data = data["ragstuffer"]
    assert "documents_ingested_total" in stuffer_data or "chunks_created_total" in stuffer_data


def test_ragorchestrator_metrics_present(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data = resp.json()
    assert "ragorchestrator" in data, "ragorchestrator not in summary"
    orch_data = data["ragorchestrator"]
    assert "queries_total" in orch_data


def test_metrics_have_last_scraped_timestamp(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data = resp.json()
    sources = data.get("sources", {})
    for name in ("ragpipe", "ragstuffer", "ragorchestrator"):
        assert name in sources, f"{name} not in sources"
        assert "up" in sources[name], f"{name} missing 'up' field"


def test_stale_metrics_flagged(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data = resp.json()
    sources = data.get("sources", {})
    for name, source_data in sources.items():
        assert "up" in source_data, f"{name} missing 'up' boolean"
        assert isinstance(source_data["up"], bool), f"{name} 'up' should be boolean, got {type(source_data['up'])}"


# ── Scrape behavior ───────────────────────────────────────────────────────────


def test_unavailable_service_handled_gracefully(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/health", timeout=10)
    assert resp.status_code == 200
    resp = httpx.get(f"{ragwatch_url}/metrics", timeout=10)
    assert resp.status_code == 200
    resp = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    assert resp.status_code == 200


def test_metrics_update_over_time(ragwatch_url):
    resp1 = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data1 = resp1.json()
    timestamp1 = data1.get("timestamp")
    assert timestamp1 is not None
    sources1 = data1.get("sources", {})
    pipe_count1 = sources1.get("ragpipe", {}).get("metric_count", 0)

    import time

    time.sleep(2)

    resp2 = httpx.get(f"{ragwatch_url}/metrics/summary", timeout=10)
    data2 = resp2.json()
    timestamp2 = data2.get("timestamp")
    assert timestamp2 is not None
    assert timestamp2 >= timestamp1, "timestamp should not go backwards"
    sources2 = data2.get("sources", {})
    pipe_count2 = sources2.get("ragpipe", {}).get("metric_count", 0)
    assert pipe_count2 >= pipe_count1, "metric count should not decrease between scrapes"


def test_ragwatch_up_gauge_present(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics", timeout=10)
    text = resp.text
    assert "ragwatch_up" in text, "ragwatch_up gauge should be present in metrics"


def test_scrape_duration_histogram_present(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics", timeout=10)
    text = resp.text
    assert "ragwatch_scrape_duration_seconds" in text, "scrape duration histogram should be present"


def test_scrape_error_counter_present(ragwatch_url):
    resp = httpx.get(f"{ragwatch_url}/metrics", timeout=10)
    text = resp.text
    assert "ragwatch_scrape_errors_total" in text, "scrape errors counter should be present"
