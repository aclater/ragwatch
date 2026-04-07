# ragwatch

Observability aggregation service for the rag-suite stack. Scrapes metrics from ragpipe, ragstuffer, and ragorchestrator, stores parsed samples in memory, and exposes them via Prometheus-compatible `/metrics` endpoint and JSON `/metrics/summary` endpoint for Grafana dashboards.

## Table of contents

- [Architecture](docs/architecture.md) — data flow, scraped services, key design decisions
- [API reference](docs/api.md) — endpoints, response formats, adding new scrape targets
- [Configuration](docs/configuration.md) — environment variables

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

## Running tests

```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```

## Status

**Implemented.** ragwatch is production-ready and actively scraping ragpipe, ragstuffer, and ragorchestrator metrics in the running stack.

## License

AGPL-3.0-or-later
