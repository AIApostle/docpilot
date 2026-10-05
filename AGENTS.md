# DocPilot Project Guidelines & Agent Instructions

## 1. Scope & Isolation
- **Strict Boundary Separation**: Backend (`/backend`) and frontend (`/frontend`) are strictly separated domains.
- **Do Not Cross Boundaries**: While working on the backend, **do not touch, edit, or modify any files in the frontend** (and vice versa), unless explicitly requested by the user.

## 2. Agent Instruction Hierarchy
Whenever an agent operates on this repository:
1. **Root Instructions**: Always read and follow the instructions in this root `AGENTS.md`.
2. **Context-Specific Instructions**: Read and follow the `AGENTS.md` located inside the specific subsystem or directory you are working in (e.g., [backend/AGENTS.md](file:///home/ai-apostle/Projects/docpilot/backend/AGENTS.md)).

## 3. Core Development Principles

### Security First
- Every architectural decision, endpoint, and component must be designed with security as the top priority.
- Enforce strict input validation, data sanitization, authentication, and authorization.
- Never hardcode secrets, API keys, or credentials. Store and load configuration securely via environment variables.
- Protect against common vulnerabilities (OWASP Top 10, injection, CSRF, insecure direct object references).

### No Shortcuts
- Write complete, robust, production-grade code.
- Avoid placeholder implementations, stubbed mocks that bypass real logic, or quick hacks that compromise reliability.
- Handle error boundaries, edge cases, and unexpected states explicitly.

### Documentation-First Development
- Always consult and read official documentation on how things are intended to be done before using, configuring, or integrating any framework, tool, SDK, or external library.
- Verify API contracts, deprecation statuses, and version compatibility before implementing integrations.

### Mandatory Skill Utilization for Best Practices
- Always check and use your specialized skills (e.g., Supabase, Render, Python dependencies, database management, security) whenever performing relevant tasks to ensure established best practices and project conventions are strictly followed.

### Database & SQL File Isolation
- Each database table must have its own separate, dedicated SQL queries file.
- Never mix or combine queries from different tables into a single file. Keep query definitions strictly separated and scoped per table.

