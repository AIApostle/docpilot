# DocPilot Backend Agent Guidelines

## 1. Domain Boundary
- You are working in the **Backend** environment (`/backend`).
- **Do NOT touch, edit, or modify any files in `../frontend`**. Keep backend changes completely isolated.

## 2. Instruction Precedence
1. Read and adhere to the root project instructions in [../AGENTS.md](file:///home/ai-apostle/Projects/docpilot/AGENTS.md).
2. Adhere to all rules in this backend-specific guide.

## 3. Technology & Dependency Standards
- **Runtime & Manager**: Python 3.14 / uv (`uv add`, `uv run`).
- **Framework**: FastAPI with Uvicorn.
- **Data Modeling & Settings**: Pydantic v2 and `pydantic-settings`.
- **Application Mode**: Keep `[tool.uv] package = false` in `pyproject.toml` since the backend is an application service, not a distributable wheel package.

## 4. Security-First Architecture
- **Input Validation**: Validate every request body, query parameter, and header using strict Pydantic schemas.
- **Authentication & Authorization**: Verify auth tokens and enforce role-based / user-scoped permissions on all sensitive endpoints.
- **Configuration & Secrets**: Load all sensitive keys and environment variables via `pydantic-settings` from `.env`. Never commit secrets, service keys, or sensitive configs to version control.
- **Network & API Security**:
  - Restrict CORS origins strictly to permitted frontend domains.
  - Implement rate limiting, timeout policies, and sanitized error responses (avoid leaking internal stack traces or database errors to clients).
  - Use parameterized queries or ORM/client abstractions to prevent injection attacks.

## 5. Engineering Quality: No Shortcuts
- No dummy/placeholder fallback code that masks underlying failures.
- Implement robust, typed error handling and raise standard FastAPI `HTTPException` with meaningful error models.
- Ensure all modules, models, and routes are modular and cleanly organized (e.g. `src/agent/`, `src/auth/`, `src/client/`, `src/db/`, `src/pages/`, `src/schemas/`).

## 6. Documentation-First Integration
- Always read and verify the official documentation for any library, SDK, or framework (e.g., FastAPI, Pydantic, HTTPX, Supabase, LLM SDKs) before writing or updating integration code.
- Ensure correct usage of async/await, connection pooling, and client session lifecycles as recommended by library authors.

## 7. Database & SQL Query Isolation
- **Dedicated File Per Table**: Every database table must have its own separate, dedicated SQL queries file (under `src/db/`).
- **Never Mix Table Queries**: Do not mix queries across multiple tables in a single file. Keep each table's queries strictly isolated to its respective query file.

## 8. External Services & Client Architecture (`src/client/`)
- **Centralized Service Clients**: Any code that interacts with external services (e.g., Supabase, third-party APIs, or external SDKs) must be written inside the `src/client/` directory.
- **Encapsulated Invocations & Exports**: Client initializations, connections, and external API invocations must be defined and managed within `src/client/`, then imported wherever needed across the backend.
- **Modular Programming**:
  - Adhere to strict separation of concerns: split logic into dedicated files and functions with single responsibilities to ensure the codebase remains maintainable, testable, and clean.
  - Do not create monolithic client files or mix multiple external service providers into the same module.

