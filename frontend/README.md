# DocPilot frontend

React and TypeScript web client for the DocPilot doctor-facing conversation experience.

## Run locally

```sh
npm install
npm run dev
```

The development-only chat preview is available at `/chat/demo`. It displays synthetic content, is read-only, and does not call the API. The normal `/login`, `/register`, `/new`, and `/chat/{id}` routes use the backend API and require a valid backend session for protected routes.

## Configure the backend

Copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL` to the backend origin, for example:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Leave it empty to send relative API requests to the current origin. Restart Vite after changing environment variables.

All endpoint paths are centralized in [`src/api/endpoints.ts`](./src/api/endpoints.ts), so they can be updated together when the backend contract is finalized. The current proposed contract is:

| Method | Path | Expected request/response |
| --- | --- | --- |
| `POST` | `/auth/register` | `{ name?, email, password }`; establishes the session |
| `POST` | `/auth/login` | `{ email, password }`; establishes the session |
| `POST` | `/auth/logout` | Ends the current session |
| `GET` | `/chats` | Array of chat summaries, or `{ chats: [...] }` / `{ items: [...] }` |
| `GET` | `/chats/{id}` | Chat summary with a `messages` array |
| `POST` | `/chat` | `{ message, conversation_id? }`; returns a conversation id and assistant reply |

The response parsers accept common field aliases such as `conversation_id`/`chat_id`/`id`, `reply`/`response`, and snake_case or camelCase timestamps. Update the endpoint map and parsers in `src/api/` to match the backend's final contract.

Requests include cookies (`credentials: 'include'`) for an HttpOnly session. For a separate frontend/backend origin, configure the backend's CORS policy to allow the frontend origin and credentials. The frontend does not use Supabase, store auth tokens, or persist conversation content in browser storage.

## Checks

```sh
npm run build
npm run lint
```
