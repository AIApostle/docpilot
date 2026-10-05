# DocPilot Backend Agent Guidelines

## 1. Domain Boundary
- You are working in the **Backend** environment (`/backend`).
- **Do NOT touch, edit, or modify any files in `../frontend`**. Keep backend changes completely isolated unless explicitly commanded.

## 2. Instruction Precedence
1. Read and adhere to the root project instructions in [../AGENTS.md](file:///home/ai-apostle/Projects/docpilot/AGENTS.md).
2. Adhere to all rules in this backend-specific guide.

## 3. Python Source Root & Import Convention
- The `src/` directory is the root directory for Python source code.
- **Never use `from src.` imports**. Always import modules relative to `src/` (e.g. `from client.config import settings`, `from schemas.login import ...`) or use explicit package-relative imports (e.g. `from .jwt import ...`).

## 4. Mandatory Git Commit & Push Workflow
- **Always Commit and Push**: Whenever you complete a feature, bugfix, schema, client, or user-requested task, you must:
  1. Verify the code compiles/tests cleanly.
  2. Stage the modified files (`git add`).
  3. Commit with a concise, descriptive commit message.
  4. Push the commit to the remote repository (`origin/main`).

## 5. Technology & Dependency Standards
- **Runtime & Manager**: Python 3.14 / uv (`uv add`, `uv run`).
- **Framework**: FastAPI with Uvicorn.
- **Data Modeling & Settings**: Pydantic v2 and `pydantic-settings`.
- **Application Mode**: Keep `[tool.uv] package = false` in `pyproject.toml` since the backend is an application service, not a distributable wheel package.

## 6. Security-First Architecture
- **Input Validation**: Validate every request body, query parameter, and header using strict Pydantic schemas.
- **Authentication & Authorization**: Verify auth tokens (JWT and Supabase Auth tokens) and enforce role-based / physician-scoped permissions on all sensitive endpoints.
- **Configuration & Secrets**: Load all sensitive keys and environment variables via `client.config.settings` from `.env`. Never commit secrets or service keys to version control.
- **Network & API Security**:
  - Restrict CORS origins strictly to permitted frontend domains.
  - Implement rate limiting, timeout policies, and sanitized error responses.
  - Use parameterized queries or Supabase client abstractions to prevent injection attacks.

## 7. Database & SQL Query Isolation
- **Dedicated File Per Table**: Every database table must have its own separate, dedicated SQL queries file under `src/db/`.
- **Never Mix Table Queries**: Do not mix queries across multiple tables in a single file. Keep each table's queries strictly isolated to its respective query file.

## 8. External Services & Client Architecture (`src/client/`)
- **Centralized Service Clients**: Any code that interacts with external services (e.g., Supabase, OpenRouter LLM, Telegram, Walrus Memory) must be written inside the `src/client/` directory.
- **Encapsulated Invocations & Exports**: Client initializations, connections, and external API invocations must be defined and managed within `src/client/`, then imported wherever needed across the backend.
- **Modular Programming**:
  - Split logic into dedicated files and functions with single responsibilities.
  - Do not create monolithic client files or mix multiple external service providers into the same module.
