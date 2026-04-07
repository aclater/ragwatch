# Architecture

Observability aggregation service for the rag-suite stack. Scrapes metrics from ragpipe, ragstuffer, and ragorchestrator, stores parsed samples in memory, and exposes them via Prometheus-compatible `/metrics` endpoint and JSON `/metrics/summary` endpoint for Grafana dashboards.

## How it fits into rag-suite

```
ragpipe ──→ :8090/metrics ──┐
                           │
ragstuffer ──→ :8091/metrics ├──→ ragwatch (:9090) ──→ Prometheus server
                           │
ragorchestrator ──→ :8095/metrics ┤
                           │
                           └──→ /metrics/summary JSON → Grafana dashboards
```

Background thread scrapes all three services every 30 seconds (configurable via `RAGWATCH_SCRAPE_INTERVAL_SECS`).

## Scraped services

| Service | Metrics URL | Default scrape interval |
|---------|-------------|------------------------|
| ragpipe | `http://localhost:8090/metrics` | 30s |
| ragstuffer | `http://localhost:8091/metrics` | 30s |
| ragorchestrator | `http://localhost:8095/metrics` | 30s |

## Key design decisions

- **Prometheus for metrics collection** (pull-based, standard in cloud-native)
- **JSON `/metrics/summary`** for direct Grafana consumption without Prometheus
- **Thread-based background scraping** — does not block FastAPI event loop
- **Thread-safe sample storage** with lock-protected global dict
- **Ragwatch's own metrics** track scrape health, not just forward upstream metrics
- **No GPU required** — pure metrics aggregation

## Project structure

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
