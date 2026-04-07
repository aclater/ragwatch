# Configuration

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RAGWATCH_SCRAPE_INTERVAL_SECS` | `30` | Interval between scrapes of upstream endpoints |

Scraped URLs are hardcoded to localhost:
- `RAGPIPE_METRICS_URL = "http://localhost:8090/metrics"`
- `RAGSTUFFER_METRICS_URL = "http://localhost:8091/metrics"`
- `RAGORCHESTRATOR_METRICS_URL = "http://localhost:8095/metrics"`
