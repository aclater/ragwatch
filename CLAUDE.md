# ragwatch

Observability aggregation service for rag-suite. Scrapes metrics from ragpipe and ragstuffer, stores parsed samples in memory, and exposes them via Prometheus-compatible `/metrics` endpoint and JSON `/metrics/summary` endpoint for Grafana dashboards.

## Architecture
```
ragpipe :8090/metrics ──┐
                       ├──→ ragwatch :9090 ──→ /metrics (Prometheus format)
ragstuffer :8091/metrics ┤              └──→ /metrics/summary (JSON for Grafana)
```

Background thread scrapes both endpoints every 30 seconds (configurable via `RAGWATCH_SCRAPE_INTERVAL_SECS`).

## Package structure
```
ragwatch/
  __init__.py      — package marker + FastAPI app factory with lifespan
  __main__.py      — uvicorn entry point (python -m ragwatch)
  metrics.py       — Prometheus metric definitions (CollectorRegistry, Counters, Gauges, Histograms)
tests/
  test_ragwatch.py — integration tests for scrape loop and endpoints
quadlets/
  ragwatch.container — Podman quadlet for systemd integration
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{"status": "ok"}` if both upstream services are up, `{"status": "degraded"}` otherwise |
| `GET` | `/metrics` | Prometheus-compatible metrics (ragwatch's own instrumentation) |
| `GET` | `/metrics/summary` | JSON summary of scraped metrics from ragpipe and ragstuffer |

## /metrics/summary response

```json
{
  "status": "up",
  "timestamp": 1712345678.901,
  "sources": {
    "ragpipe": {"up": true, "metric_count": 24},
    "ragstuffer": {"up": true, "metric_count": 8}
  },
  "ragpipe": {
    "queries_total": 1234.0,
    "embed_cache_hits": 890.0,
    "embed_cache_misses": 344.0,
    "embed_cache_hit_rate": 0.721,
    "invalid_citations_total": 12.0,
    "chunks_retrieved_total": 5678.0
  },
  "ragstuffer": {
    "documents_ingested_total": 200.0,
    "chunks_created_total": 3420.0,
    "embed_requests_total": 200.0,
    "embed_errors_total": 3.0
  }
}
```

## Prometheus metrics exposed

```
ragwatch_scrape_duration_seconds{source="ragpipe|ragstuffer"}
ragwatch_scrape_errors_total{source="ragpipe|ragstuffer"}
ragwatch_up (1=up, 0=down)
ragwatch_last_scrape_timestamp_seconds{source="ragpipe|ragstuffer"}
```

## Key design decisions
- Prometheus for metrics collection (pull-based, standard in cloud-native)
- JSON `/metrics/summary` for direct Grafana consumption without Prometheus
- Thread-based background scraping — does not block FastAPI event loop
- Thread-safe sample storage with lock保护的 global dict
- Ragwatch's own metrics track scrape health, not just forward upstream metrics
- No GPU required — pure metrics aggregation

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RAGWATCH_SCRAPE_INTERVAL_SECS` | `30` | Interval between scrapes |

Scraped URLs are hardcoded to localhost:
- `RAGPIPE_METRICS_URL = "http://localhost:8090/metrics"`
- `RAGSTUFFER_METRICS_URL = "http://localhost:8091/metrics"`

## Running tests
```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```
