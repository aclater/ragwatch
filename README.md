# ragwatch

Observability aggregation service for the rag-suite stack. Scrapes metrics from ragpipe and ragstuffer, stores parsed samples in memory, and exposes them via Prometheus-compatible `/metrics` endpoint and JSON `/metrics/summary` endpoint for Grafana dashboards.

## What it does

ragwatch is the monitoring and observability layer for rag-suite. It:

- Scrapes the `/metrics` endpoint from ragpipe every 30 seconds (configurable)
- Scrapes the `/metrics` endpoint from ragstuffer every 30 seconds (configurable)
- Parses Prometheus-formatted metrics and stores aggregated samples in memory
- Exposes a Prometheus-compatible `/metrics` endpoint for Prometheus server scraping
- Exposes a `/metrics/summary` JSON endpoint with parsed, aggregated metrics for direct Grafana consumption
- Tracks upstream service health and exposes a `/health` endpoint reflecting aggregate status

## How it fits into rag-suite

```
ragpipe ──→ :8090/metrics ──┐
                           ├──→ ragwatch (:9090) ──→ Prometheus server
ragstuffer ──→ :8091/metrics ┤
                           │
                           └──→ /metrics/summary JSON → Grafana dashboards
```

## Quick start

```bash
# Clone and install
git clone https://github.com/aclater/ragwatch
cd ragwatch
pip install -r requirements.txt

# Run
python -m ragwatch

# Or via container
podman build -t ragwatch .
podman run --rm -p 9090:9090 ragwatch
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{"status": "ok"}` if both ragpipe and ragstuffer are up, `{"status": "degraded"}` otherwise |
| `GET` | `/metrics` | Prometheus-compatible metrics output (ragwatch's own instrumentation) |
| `GET` | `/metrics/summary` | JSON summary of scraped metrics from ragpipe and ragstuffer |

### /metrics/summary response format

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

## Prometheus metrics exposed by ragwatch

ragwatch instruments its own scraping activity:

```
# HELP ragwatch_scrape_duration_seconds Duration of scraping upstream metrics endpoints in seconds
# TYPE ragwatch_scrape_duration_seconds histogram
ragwatch_scrape_duration_seconds_bucket{source="ragpipe",le="0.01"} 100
ragwatch_scrape_duration_seconds_bucket{source="ragpipe",le="0.05"} 500
...

# HELP ragwatch_scrape_errors_total Total scrape errors from upstream endpoints
# TYPE ragwatch_scrape_errors_total counter
ragwatch_scrape_errors_total{source="ragpipe"} 2
ragwatch_scrape_errors_total{source="ragstuffer"} 0

# HELP ragwatch_up Whether ragwatch is able to scrape all upstream endpoints (1=up, 0=down)
# TYPE ragwatch_up gauge
ragwatch_up 1

# HELP ragwatch_last_scrape_timestamp_seconds Unix timestamp of last successful scrape of each upstream
# TYPE ragwatch_last_scrape_timestamp_seconds gauge
ragwatch_last_scrape_timestamp_seconds{source="ragpipe"} 1712345678.901
ragwatch_last_scrape_timestamp_seconds{source="ragstuffer"} 1712345678.895
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RAGWATCH_SCRAPE_INTERVAL_SECS` | `30` | Interval between scrapes of upstream endpoints |

## Project structure

```
ragwatch/
  __init__.py      — package marker + app factory
  __main__.py      — uvicorn entry point (python -m ragwatch)
  metrics.py       — Prometheus metric definitions (CollectorRegistry, Counters, Gauges, Histograms)
ragwatch:app       — FastAPI app with lifespan (starts background scrape thread)
tests/
  test_ragwatch.py — integration tests for scrape loop and endpoints
quadlets/
  ragwatch.container — Podman quadlet for systemd integration
```

## Running tests

```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```

## Status

**Implemented.** ragwatch is production-ready and actively scraping ragpipe and ragstuffer metrics in the running stack.

## License

AGPL-3.0-or-later
