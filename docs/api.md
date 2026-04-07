# ragwatch API

ragwatch is an observability aggregation service that scrapes metrics from ragpipe, ragstuffer, and ragorchestrator, then exposes them via Prometheus-compatible `/metrics` and JSON `/metrics/summary`.

## Scraped Services

| Service | Metrics URL | Scrape Interval |
|---------|-------------|-----------------|
| ragpipe | `http://localhost:8090/metrics` | Every 30s |
| ragstuffer | `http://localhost:8091/metrics` | Every 30s |
| ragorchestrator | `http://localhost:8095/metrics` | Every 30s |

Scrape interval is configurable via `RAGWATCH_SCRAPE_INTERVAL_SECS` (default: 30 seconds).

## Endpoints

### `GET /health`

Health check. Returns `ok` when all upstream services are reachable, `degraded` when any upstream is down.

**Response:** `application/json`

```json
{"status": "ok"}
```

```bash
curl http://localhost:9090/health
```

### `GET /metrics`

ragwatch's own Prometheus metrics (scrape duration, errors, and health gauges). Does not forward upstream metrics — only ragwatch's instrumentation.

**Response:** `text/plain; charset=utf-8` (Prometheus text format)

```
# HELP ragwatch_up Whether ragwatch is able to scrape all upstream endpoints (1=up, 0=down)
# TYPE ragwatch_up gauge
ragwatch_up 1.0
# HELP ragwatch_scrape_duration_seconds Duration of scraping upstream metrics endpoints in seconds
# TYPE ragwatch_scrape_duration_seconds histogram
ragwatch_scrape_duration_seconds_bucket{source="ragpipe",le="0.01"} 10.0
...
# HELP ragwatch_scrape_errors_total Total scrape errors from upstream endpoints
# TYPE ragwatch_scrape_errors_total counter
ragwatch_scrape_errors_total{source="ragpipe"} 0.0
# HELP ragwatch_last_scrape_timestamp_seconds Unix timestamp of last successful scrape of each upstream
# TYPE ragwatch_last_scrape_timestamp_seconds gauge
ragwatch_last_scrape_timestamp_seconds{source="ragorchestrator"} 1.775521e+09
```

```bash
curl http://localhost:9090/metrics
```

### `GET /metrics/summary`

JSON summary of all scraped upstream metrics, suitable for Grafana dashboard consumption without a Prometheus scrape.

**Response:** `application/json`

```json
{
    "status": "up",
    "timestamp": 1775521034.2388134,
    "sources": {
        "ragpipe": {"up": true, "metric_count": 80},
        "ragstuffer": {"up": true, "metric_count": 4},
        "ragorchestrator": {"up": true, "metric_count": 34}
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
    },
    "ragorchestrator": {
        "queries_total": 42.0,
        "query_latency_seconds": 0.0,
        "tool_calls_total": 0.0,
        "complexity_classified_total": 0.0
    }
}
```

```bash
curl http://localhost:9090/metrics/summary | python3 -m json.tool
```

**Fields in `/metrics/summary`:**

| Field | Source | Description |
|-------|--------|-------------|
| `status` | — | `"up"` if all sources up, `"degraded"` otherwise |
| `timestamp` | — | Unix timestamp of the summary |
| `sources.<name>.up` | — | Boolean, whether this source responded to last scrape |
| `sources.<name>.metric_count` | — | Number of metrics parsed from this source |
| `ragpipe.queries_total` | `ragpipe_queries_total` | Total RAG queries processed |
| `ragpipe.embed_cache_hits` | `ragpipe_embed_cache_hits_total` | Embedding cache hits |
| `ragpipe.embed_cache_misses` | `ragpipe_embed_cache_misses_total` | Embedding cache misses |
| `ragpipe.embed_cache_hit_rate` | computed | Hit rate as a fraction (0–1) |
| `ragpipe.invalid_citations_total` | `ragpipe_invalid_citations_total` | Citations that failed validation |
| `ragpipe.chunks_retrieved_total` | `ragpipe_chunks_retrieved_total` | Total chunks retrieved from docstore |
| `ragstuffer.documents_ingested_total` | `ragstuffer_documents_ingested_total` | Documents ingested |
| `ragstuffer.chunks_created_total` | `ragstuffer_chunks_created_total` | Chunks created |
| `ragstuffer.embed_requests_total` | `ragstuffer_embed_requests_total` | Embedding requests made |
| `ragstuffer.embed_errors_total` | `ragstuffer_embed_errors_total` | Embedding errors |
| `ragorchestrator.queries_total` | `ragorchestrator_queries_total` | Queries processed |
| `ragorchestrator.query_latency_seconds` | `ragorchestrator_query_latency_seconds` | Query latency histogram sum |
| `ragorchestrator.tool_calls_total` | `ragorchestrator_tool_calls_total` | Supervisor tool calls |
| `ragorchestrator.complexity_classified_total` | `ragorchestrator_complexity_classified_total` | Complexity classifications |

## Adding a New Scrape Target

To add a new service to ragwatch's scrape loop:

1. Add the metrics URL constant in `ragwatch/__init__.py`:
   ```python
   NEW_SERVICE_METRICS_URL = "http://localhost:<port>/metrics"
   ```

2. Add the service name to `_latest` and the scrape sources in `__init__.py`:
   ```python
   _latest: dict[str, dict[str, float]] = {
       "ragpipe": {},
       "ragstuffer": {},
       "ragorchestrator": {},
       "new_service": {},   # add here
   }
   ```

3. Add the scrape call in `_scrape_loop`:
   ```python
   new_samples = _scrape_source("new_service", NEW_SERVICE_METRICS_URL)
   ```

4. Update the `all_up` check:
   ```python
   all_up = bool(pipe_samples) and bool(stuffer_samples) and bool(orch_samples) and bool(new_samples)
   ```

5. Add parsed metrics to the `/metrics/summary` response in `metrics_summary()`:
   ```python
   if new_samples:
       summary["new_service"] = {
           "my_metric_total": new_samples.get("new_service_my_metric_total", 0.0),
       }
   ```

6. Add `"new_service"` to the `sources` dict in the summary response.
