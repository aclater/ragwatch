# ragwatch

Observability service for the rag-suite stack. Collects metrics from ragpipe, ragstuffer, and ragprobe and surfaces them via Prometheus + Grafana.

## Architecture
```
ragpipe ──→ metrics ──┐
                      ├──→ ragwatch (Prometheus) ──→ Grafana dashboards
ragstuffer ─→ metrics ─┤
                      │
ragprobe ──→ results ─┘
```

## Package structure
```
ragwatch/
  __init__.py      — empty (package marker)
tests/
  __init__.py      — empty (package marker)
quadlets/
  ragwatch.container         — Prometheus service quadlet (stub)
  ragwatch-grafana.container — Grafana dashboard quadlet (stub)
```

## Key design decisions
- Prometheus for metrics collection (pull-based, standard in cloud-native)
- Grafana for dashboards (rich visualization, alerting)
- Metrics scraped from ragpipe, ragstuffer, ragprobe endpoints
- No GPU required — pure metrics aggregation and visualization

## Running tests
```bash
pip install '.[dev]'
python -m pytest tests/ -v
ruff check && ruff format --check
```

## GPU acceleration

- This system may have an AMD, NVIDIA, or Intel GPU. All services and scripts must detect the available GPU at runtime and select the appropriate acceleration stack — do not hardcode a vendor.
- Detection priority: NVIDIA CUDA > AMD ROCm > Intel XPU/OpenVINO > CPU. Fall back to CPU only when no GPU is available, and log a clear warning when doing so.
- Never default to CPU for any workload that can run on GPU. CPU fallback is acceptable only when a specific library or operation has no GPU support, and must be explicitly noted in a comment explaining why.
- For Python workloads: use torch.cuda.is_available(), torch.version.hip (ROCm), or torch.xpu.is_available() (Intel) to detect and select the correct device at runtime. Do not hardcode "cuda", "rocm", or "cpu".
- For ONNX Runtime: select ExecutionProvider based on runtime detection — CUDAExecutionProvider, ROCMExecutionProvider, OpenVINOExecutionProvider, or CPUExecutionProvider — in that priority order.
- For container workloads:
  - NVIDIA: pass --device /dev/nvidia0 (or --gpus all with nvidia-container-toolkit)
  - AMD ROCm: pass --device /dev/kfd --device /dev/dri
  - Intel: pass --device /dev/dri
  - Document any container that cannot use GPU and why.
- AMD ROCm on gfx1151: HSA_OVERRIDE_GFX_VERSION=11.5.1 is required. Set this env var in any quadlet, container, or script that uses ROCm on this hardware.
- Do not recommend or implement CPU-only solutions without first investigating whether a GPU-accelerated alternative exists for all three vendors.
- When benchmarking or profiling, always compare GPU vs CPU and report both. Never present CPU-only results as the baseline.
- When writing GPU detection code, always write it once as a shared utility function — do not duplicate vendor detection logic across files.
