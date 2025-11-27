# Repository Guidelines

## Project Structure & Modules
- `backend/app`: FastAPI application with routers (`api/`), services, models, AI helpers, and config. `main.py` wires CORS and routes. Keep new modules typed and split by layer (api → services → models/ai).
- `backend/tests`: Pytest suite using `httpx.ASGITransport` + `pytest-asyncio`. Mirror app package structure (`tests/api`, `tests/services`, etc.) and name files `test_*.py`.
- `frontend/`: Reserved for the React/WebRTC client. Keep build tooling and components here when added.
- `content/`: Marketing/blog content (Markdown).
- `docs/`: Living docs (briefs, ADRs, progress). Update `docs/progress.md` whenever you add features or docs.

## Setup, Build, and Run
- Prereqs: Python 3.12+, uv, Node 20+ (frontend), local Postgres & Redis for full runs.
- Install backend deps: `cd backend && uv sync --all-extras --dev`.
- Run API (dev): `uv run uvicorn app.main:app --reload`.
- Lint: `uv run ruff check app tests`.
- Type check: `uv run mypy app`.
- Tests + coverage: `uv run pytest` (config adds `-v --cov=app --cov-report=term-missing`).
- Format imports (optional): `uv run ruff check --select I --fix`.
- Env: copy `.env` at repo root for app settings (`database_url`, `redis_url`, `secret_key`, API keys). Never commit secrets.

## Coding Style & Naming
- Python: type hints everywhere, 100-char lines, prefer async endpoints/services, pydantic/SQLModel models for schemas. Use snake_case for functions/vars, PascalCase for classes, and keep route modules grouped by resource.
- Tests: fixture functions in `conftest.py` when shared; assert JSON shapes explicitly; mark async tests with `@pytest.mark.asyncio`.
- Docs: prefer relative links; keep diagrams/text in ASCII; update ADRs when making architecture decisions.

## Testing Guidelines
- Add unit tests alongside code; integration tests should exercise FastAPI routes via `AsyncClient`.
- Cover happy path + key failure modes (validation errors, auth once added).
- Maintain or improve coverage thresholds from pytest config; include representative sample payloads.

## Commit & PR Guidelines
- Commits: use conventional prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `test:`). Keep scope focused.
- PRs: include a clear summary, testing notes (`uv run pytest` results), and relevant screenshots for UI work. Link issues/tasks and mention any config changes (.env keys, migrations).
- Documentation: when behavior or endpoints change, update `docs/progress.md` and any impacted living docs before merge.

## Security & Configuration Tips
- Use strong `secret_key` and rotate API keys; keep `debug` false outside local dev.
- Restrict CORS origins in `settings.cors_origins` to known frontends.
- Secure storage endpoints (audio/media) and avoid logging sensitive user content.
