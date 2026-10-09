# DocPilot Backend

DocPilot's agentic FastAPI backend service, providing clinical LLM reasoning, decentralized memory on Walrus (MemWal), and relational state management in Supabase (PostgreSQL).

See the [Root README](../README.md) for full project documentation and architecture.

## Quick Start

### 1. Environment Configuration

```bash
cp .env.example .env
```

Fill in required credentials (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENROUTER_API_KEY`, `MEMWAL_PRIVATE_KEY`, `MEMWAL_ACCOUNT_ID`, `SECRET_KEY`).

### 2. Run with `uv` (Recommended)

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

### 3. Run with standard `venv`

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
uvicorn main:app --reload --port 8000
```

### 4. Run Test Suite

```bash
uv run pytest
```
