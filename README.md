# Repo Diagrammer

Repo Diagrammer analyses public GitHub repositories, extracts structural metadata with Tree-sitter, builds network diagrams, and optionally summarises the codebase with a local LLM.

## Features

- FastAPI backend with endpoints for analysis and cache retrieval.
- Shallow git clone into a deterministic `.cache/<owner>_<repo>/<sha>/` workspace.
- Static analysis using Tree-sitter for Python and JavaScript to discover imports, functions, classes, routes, and ORM models.
- NetworkX powered dependency graphs and C4-style module maps rendered as Mermaid diagrams.
- Optional summaries via a local Ollama instance (Llama 3.1 8B by default).
- Vanilla HTML/CSS/JS frontend that renders diagrams and summaries.

## Prerequisites (Windows 10/11 + VS Code)

1. Install [Git](https://git-scm.com/download/win).
2. Install [Python 3.11](https://www.python.org/downloads/windows/).
3. Install [VS Code](https://code.visualstudio.com/Download).
4. (Optional for summaries) Install [Ollama](https://ollama.com/download) and pull `llama3.1:8b`.

## Clone This Project

```powershell
git clone <this_project_url>
cd repo-diagrammer
```

## Backend Setup

### Using uv (recommended)

```powershell
pip install uv
cd backend
uv venv
uv pip install -r requirements.txt
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Using venv + pip

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Optional: Start Ollama

```powershell
ollama serve
ollama pull llama3.1:8b
```

The backend writes logs to `.cache/logs/<sha>.log` and caches analysis results under `.cache/<owner>_<repo>/<sha>/result.json`.

## Frontend Setup

Use VS Code Live Server or any static file server to open `frontend/index.html`. The page communicates with the backend at `http://127.0.0.1:8000`.

## Usage

1. Start the backend as shown above.
2. Open the frontend.
3. Paste a public GitHub repository URL (e.g. `https://github.com/pallets/flask`).
4. Click **Analyze** and wait for diagrams and summaries.
5. Use the **Zoom in** dropdown to focus on a specific module when diagrams are large.

## Testing

```powershell
cd backend
pytest -q
```

## Troubleshooting

- **Git not installed**: Ensure `git` is available in PowerShell (`git --version`).
- **Private repositories**: Only public repositories are supported.
- **Large repositories**: Analysis caps graphs at 40 nodes for readability; consider narrowing scope via the "Zoom in" dropdown (planned extension).
- **Mermaid errors**: Refresh the tab; ensure diagrams do not exceed Mermaid limits.
- **Ollama unavailable**: Summaries will show a notice but diagrams still render.

## License

MIT License. See [LICENSE](LICENSE).
