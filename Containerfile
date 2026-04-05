# ragwatch — observability service for rag-suite
# Base: UBI10 minimal, pinned to digest for reproducibility
FROM registry.access.redhat.com/ubi10@sha256:1b616c4a90d6444b394d5c8f4bd9e15a394d95dd628925d0ec80c257fdc5099c

# hadolint ignore=DL3041
RUN dnf install -y -q python3 python3-pip curl && \
    dnf clean all && \
    rm -rf /var/cache/dnf

WORKDIR /app

COPY pyproject.toml ./
COPY ragwatch/ ragwatch/
RUN pip install --quiet --no-cache-dir .

USER 1001

CMD ["python3", "-m", "ragwatch"]
