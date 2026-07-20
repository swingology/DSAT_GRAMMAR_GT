# DSAT Marker Worker

This uv project isolates Marker's PyTorch, Pillow, Anthropic, and OpenAI
constraints from the FastAPI backend environment.

Install/sync:

```bash
uv sync
```

Verify:

```bash
uv run marker_single --help
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Marker runs as an offline ingestion worker. It must not be imported by the
student-facing FastAPI process.
