from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

REGISTRY = CollectorRegistry()

ragwatch_scrape_duration_seconds = Histogram(
    "ragwatch_scrape_duration_seconds",
    "Duration of scraping upstream metrics endpoints in seconds",
    ["source"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=REGISTRY,
)

ragwatch_scrape_errors_total = Counter(
    "ragwatch_scrape_errors_total",
    "Total scrape errors from upstream endpoints",
    ["source"],
    registry=REGISTRY,
)

ragwatch_up = Gauge(
    "ragwatch_up",
    "Whether ragwatch is able to scrape all upstream endpoints (1=up, 0=down)",
    registry=REGISTRY,
)

ragwatch_last_scrape_timestamp = Gauge(
    "ragwatch_last_scrape_timestamp_seconds",
    "Unix timestamp of last successful scrape of each upstream",
    ["source"],
    registry=REGISTRY,
)


def get_metrics() -> bytes:
    return generate_latest(REGISTRY)
