# ragwatch

Observability service for the rag-suite stack. Collects metrics from ragpipe, ragstuffer, and ragprobe and surfaces them via Prometheus + Grafana.

## What it does

ragwatch is the monitoring and observability layer for the rag-suite. It:

- Scrapes metrics from ragpipe (query latency, grounding classification, citation validation, cache hit rates)
- Collects ingestion metrics from ragstuffer (documents processed, chunk counts, embedding throughput)
- Gathers test results from ragprobe (pass/fail rates, grounding quality scores, regression detection)
- Exposes a Prometheus-compatible metrics endpoint
- Provides Grafana dashboards for real-time and historical observability

## How it fits into rag-suite

```
ragpipe ──→ metrics ──┐
                      ├──→ ragwatch (Prometheus) ──→ Grafana dashboards
ragstuffer ─→ metrics ─┤
                      │
ragprobe ──→ results ─┘
```

## Quick start

```bash
git clone https://github.com/aclater/ragwatch
cd ragwatch
pip install '.[dev]'
python -m pytest tests/ -v
```

## Running tests

```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```

## Status

Under active development. No metrics collection or dashboards are implemented yet — this is a scaffold.

## License

AGPL-3.0-or-later
