# Repository Guidelines

## Project Structure & Module Organization
- Source lives under `namespace/`, split by responsibility: `controller/` (FastAPI routers), `service/` (business logic), `client/` (external integrations), `model/` (Pydantic schemas), `container/` (dependency injection wiring), `command/` (Click CLI commands).
- Entry points: `namespace/api.py` (FastAPI app) and `namespace/cli.py` (CLI root). Extend new features by adding modules to the closest layer and binding them in the container.

## Development Setup & Commands
- Install deps with your preferred manager (e.g., `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`). Add a `requirements.txt` if you introduce dependencies.
- Run API locally: `uvicorn namespace.api:app --reload --port 8459`.
- Call the CLI example: `python -m namespace.cli example`.
- Format/import-sort before pushing; if you add tools like `ruff` or `black`, document and pin versions in the repo.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; keep line length reasonable (≤100 chars).
- Use type hints throughout; prefer explicit dataclasses/Pydantic models for payloads.
- Module/file names are `snake_case`; classes are `CapWords`; functions and variables are `snake_case`.
- Keep FastAPI routes thin: delegate to services; wire dependencies via the injector container.

## Testing Guidelines
- Use `pytest` (suggested). Place tests in `tests/` mirroring package structure (`tests/service/test_example_service.py`).
- Name tests with `test_` prefix; favor small, deterministic cases. Aim for meaningful coverage on services and controllers.
- Run tests: `pytest -q`. If you add coverage, target ≥80% and fail builds when coverage drops.

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise subject (`Add example controller route`), include focused changes only.
- PRs: describe behavior changes, add reproduction/testing notes (`uvicorn...`, `pytest -q`), link issues, and include screenshots for API docs/CLI output when visual/log changes occur.

## Security & Configuration Tips
- Keep secrets out of the repo; load via environment variables. Never commit `.env`.
- When adding clients, isolate external calls in `client/` and mock them in tests.
