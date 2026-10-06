# DocPilot authentication and conversational memory

## Scope and mode

The doctor-facing web authentication and chat experience: `/login`, `/register`, `/new`, and `/chat/{id}`. Mode: Operate.

## Audience, task, content, and constraints

An individual doctor signs in, records or retrieves patient context through natural language, and reopens prior conversations. The first authenticated destination is `/new`; sending a first message creates a conversation and navigates to `/chat/{id}`. History is listed and loaded from `GET /chats` and `GET /chats/{id}`. Keep documented memories distinct from clinical advice, never invent patient facts, and do not persist medical conversation content in browser storage. Use a restrained, legible interface and synthetic examples only.

## Chosen direction and memorable moment

The physician’s pocket casebook, selected from Impeccable direction seed `5fcf08b8` as Impeccable’s pick. A contemporary, open workspace puts the message field in the role of a writing surface, with a nearby index of backend-saved conversations. The memorable moment is a new conversation becoming an indexed, reopenable entry only after the backend creates it.

## Unresolved decisions

The backend’s exact JSON field names and cookie/session behavior are not specified in the PRD. The frontend uses the documented auth/chat routes, the approved `GET /chats` and `GET /chats/{id}` history proposal, and an HttpOnly cookie session assumption; align field names with the backend when its contract is available.

## Direction contract

### THESIS

Make the doctor's memory feel like a well-kept working casebook, not a generic AI chat. Refuse the category-default centered chat with an interchangeable history rail.

### OWN-WORLD

Warm, clean paper; deep green ink and rules; compact index tabs; quiet graphite details. Controls and history rows behave like entries in the same contemporary notebook, never like decorative paper props.

### STORY

The doctor arrives at a fresh page, asks or records something in natural language, then finds that conversation again in the backend-backed index. Replies distinguish what is documented from what is not and never present the interface as a diagnostic authority.

### FIRST VIEWPORT

On desktop, a narrow notebook index sits at the left; the rest of the page is a broad writing area with a concise welcome, a primary message composer, and a small set of grounded example prompts. On `/chat/{id}`, the thread occupies that area and the composer remains reachable below it. Auth screens use the same paper-and-green vocabulary with an uncluttered form. On mobile, the index becomes an explicit drawer and the composer remains full-width and reachable.

### FORM

Build the selected grounded physician’s pocket casebook direction across auth, `/new`, history, and chat. This is Impeccable’s pick from seed `5fcf08b8`; the catalog assignment was a Japanese high-density web mosaic. Keep the casebook's contemporary clarity and green-primary commitment rather than imitating paper texture or historic clinical forms.

### FINISH

unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
