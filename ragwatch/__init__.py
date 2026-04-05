"""ragwatch — observability aggregation service for rag-suite.

Scrapes metrics from ragpipe and ragstuffer, stores parsed samples in memory,
and exposes them via a JSON summary endpoint for Grafana dashboards.
"""

import logging
import threading
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse

from ragwatch.metrics import (
    get_metrics,
    ragwatch_last_scrape_timestamp,
    ragwatch_scrape_duration_seconds,
    ragwatch_scrape_errors_total,
    ragwatch_up,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ragwatch")

RAGPIPE_METRICS_URL = "http://localhost:8090/metrics"
RAGSTUFFER_METRICS_URL = "http://localhost:8091/metrics"
SCRAPE_INTERVAL = int(__import__("os").environ.get("RAGWATCH_SCRAPE_INTERVAL_SECS", "30"))

_scrape_lock = threading.Lock()
_latest: dict[str, dict[str, float]] = {"ragpipe": {}, "ragstuffer": {}}
_all_upstream_up = True


def _parse_metrics(text: str) -> dict[str, float]:
    samples: dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        try:
            value = float(parts[1])
        except ValueError:
            continue
        samples[name] = value
    return samples


def _scrape_source(name: str, url: str) -> dict[str, float]:
    start = time.monotonic()
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
        duration = time.monotonic() - start
        ragwatch_scrape_duration_seconds.labels(source=name).observe(duration)
        samples = _parse_metrics(resp.text)
        ragwatch_last_scrape_timestamp.labels(source=name).set(time.time())
        log.debug("Scraped %s: %d metrics in %.3fs", name, len(samples), duration)
        return samples
    except Exception:
        ragwatch_scrape_errors_total.labels(source=name).inc()
        ragwatch_scrape_duration_seconds.labels(source=name).observe(time.monotonic() - start)
        log.warning("Failed to scrape %s at %s", name, url)
        return {}


def _scrape_loop() -> None:
    global _latest, _all_upstream_up
    while True:
        pipe_samples = _scrape_source("ragpipe", RAGPIPE_METRICS_URL)
        stuffer_samples = _scrape_source("ragstuffer", RAGSTUFFER_METRICS_URL)
        all_up = bool(pipe_samples) and bool(stuffer_samples)
        with _scrape_lock:
            _latest = {"ragpipe": pipe_samples, "ragstuffer": stuffer_samples}
            _all_upstream_up = all_up
        ragwatch_up.set(1 if all_up else 0)
        time.sleep(SCRAPE_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_scrape_loop, daemon=True)
    thread.start()
    log.info("ragwatch started — scraping ragpipe and ragstuffer every %ds", SCRAPE_INTERVAL)
    yield
    log.info("ragwatch shutting down")


app = FastAPI(title="ragwatch", lifespan=lifespan)


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(get_metrics(), media_type="text/plain; charset=utf-8")


@app.get("/metrics/summary")
async def metrics_summary():
    with _scrape_lock:
        pipe = dict(_latest["ragpipe"])
        stuffer = dict(_latest["ragstuffer"])
        all_up = _all_upstream_up

    summary: dict[str, object] = {
        "status": "up" if all_up else "degraded",
        "timestamp": time.time(),
        "sources": {
            "ragpipe": {"up": bool(pipe), "metric_count": len(pipe)},
            "ragstuffer": {"up": bool(stuffer), "metric_count": len(stuffer)},
        },
    }

    if pipe:
        qs = pipe.get("ragpipe_queries_total", 0.0)
        cache_hits = pipe.get("ragpipe_embed_cache_hits_total", 0.0)
        cache_misses = pipe.get("ragpipe_embed_cache_misses_total", 0.0)
        total = cache_hits + cache_misses
        summary["ragpipe"] = {
            "queries_total": qs,
            "embed_cache_hits": cache_hits,
            "embed_cache_misses": cache_misses,
            "embed_cache_hit_rate": (cache_hits / total) if total > 0 else 0.0,
            "invalid_citations_total": pipe.get("ragpipe_invalid_citations_total", 0.0),
            "chunks_retrieved_total": pipe.get("ragpipe_chunks_retrieved_total", 0.0),
        }

    if stuffer:
        summary["ragstuffer"] = {
            "documents_ingested_total": stuffer.get("ragstuffer_documents_ingested_total", 0.0),
            "chunks_created_total": stuffer.get("ragstuffer_chunks_created_total", 0.0),
            "embed_requests_total": stuffer.get("ragstuffer_embed_requests_total", 0.0),
            "embed_errors_total": stuffer.get("ragstuffer_embed_errors_total", 0.0),
        }

    return JSONResponse(summary)


@app.get("/health")
async def health():
    with _scrape_lock:
        up = _all_upstream_up
    return JSONResponse({"status": "ok" if up else "degraded"})
