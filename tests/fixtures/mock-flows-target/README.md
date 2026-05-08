# mock-flows-target

Fixture SUT (System Under Test) for forge-codex `forge:test` skill mock-flows regression tests.

## Purpose

This is a minimal FastAPI application with role-based access control, designed to be scaffolded and tested by downstream mock-flow regression tests in the forge workflow system. It provides:

- **POST /upload** — Create records (requires `X-Role: admin` or `X-Role: member`)
- **GET /reports** — List records filtered by role permissions
- **In-memory SQLite storage** — No external dependencies

## Quick Start

```bash
pip install -e .
python -c "from app.main import app; print(app.title)"
```

### Run Smoke Tests

```bash
pytest tests/test_smoke.py -v
```

## Role Permissions

| Role | Permissions |
|------|-------------|
| `admin` | Upload, list all records |
| `member` | Upload, list own records |
| `viewer` | List public records only |
| (none/anonymous) | 401 Unauthorized |

## Data Model

Records stored in SQLite with fields:
- `id` (PK, auto-increment)
- `name` (string)
- `data` (string)
- `role` (creator role: admin, member, or public)
- `is_public` (boolean flag for public visibility)

## Design Notes

- Uses `TestClient`-friendly pattern (no startup events requiring real DB)
- In-memory SQLite connection created on first request
- Stdlib `sqlite3` only; no SQLAlchemy
- Roles defined in `app/roles.yaml` (currently unused but available for extension)
- Test fixtures in `tests/conftest.py` provide `app_client` and `seeded_db`
