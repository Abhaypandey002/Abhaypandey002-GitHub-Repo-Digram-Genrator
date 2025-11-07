# Backend Service

The backend exposes a FastAPI application with the following endpoints:

- `GET /api/health` – health check.
- `GET /api/cache/{sha}` – return cached analysis for a commit SHA when available.
- `POST /api/analyze` – trigger repository analysis. Body: `{ "repo_url": "https://github.com/owner/repo" }`.

## Setup (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Or using [uv](https://github.com/astral-sh/uv):

```powershell
pip install uv
cd backend
uv venv
uv pip install -r requirements.txt
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Tests

```powershell
cd backend
pytest -q
```

Logs are written under `.cache/logs/` and cached analyses under `.cache/<owner>_<repo>/<sha>/`.
