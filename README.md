# DocPilot

> **Agentic, Decentralized Medical Memory for Physicians.**

DocPilot is a clinical AI assistant built specifically for doctors to **store, retrieve, and update patient information and physician profiles through natural language** across the Web and Telegram.

DocPilot pairs multimodal clinical document perception (PDFs, lab reports, clinical images, CSVs) with persistent, decentralized patient memory on **Walrus Memory (MemWal)** and relational application state in **Supabase (PostgreSQL)**.

> ⚠️ **Medical Disclaimer:** DocPilot is an experimental clinical workflow assistant designed for demonstration and developer testing. Always use synthetic patient data. DocPilot is **not** an electronic health record (EHR) system, medical device, or autonomous diagnostic/prescribing agent.

---

## Key Features

- **Persistent Decentralized Memory**: Walrus Memory (MemWal on Sui) preserves patient vitals, medications, diagnoses, and allergies across sessions, web, and Telegram with cryptographic doctor-level isolation.
- **Message Intent Understanding & Perspective**: Accurately classifies clinical intents:
  - **Physician Identity Queries** (*"Who am I?"*): Identifies the attending doctor using logged-in profile data and recalled memories (e.g. *"You are Dr. Saviour"*), never confusing the doctor with the assistant.
  - **Physician Introductions & Profiles** (*"I am Dr. Saviour"*): Automatically greets the doctor, updates the physician profile, and persists the identity to Walrus memory.
  - **Assistant Identity Queries** (*"Who are you?"*): Clarifies DocPilot's role as a clinical assistant.
  - **Patient Consultations**: Extracts discrete clinical facts (vitals, labs, medications, allergies, diagnoses, plans) into persistent memory.
- **Multimodal Document Perception & Indexing**: Ingests and reviews medical records (PDFs via `pdftotext` with pure-Python fallback, CSVs, JSON, clinical images via data URLs), synthesizes findings, and indexes them into decentralized memory.
- **Doctor Memory Toggle (MemWal On/Off)**: Complete autonomy for physicians to toggle persistent clinical memory on or off at any time.
- **Omnichannel Access**: Access consultations either on the modern React web interface or on Telegram (@docpilot_AIbot) with Telegram Login Widget synchronization.
- **Zero-Downtime Keep-Alive**: Background keep-alive engine pings the backend (14-minute interval) to prevent idle spin-downs on cloud platforms like Render.

---

## Architecture

```text
       +-----------------------+       +------------------------+
       |   React Web Client    |       |      Telegram Bot      |
       |  (React 19 + Vite)    |       |   (@docpilot_AIbot)    |
       +-----------+-----------+       +------------+-----------+
                   |                                |
                   +---------------+  +-------------+
                                   |  |
                                   v  v
                         +----------------------+
                         |     FastAPI API      |
                         |   (Python / Uvicorn) |
                         +----------+-----------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+-------------------+                               +--------------------+
|     Supabase      |                               |   DocPilot Agent   |
| (PostgreSQL &     |                               |    Coordinator     |
|  Supabase Auth)   |                               +---------+----------+
+-------------------+                                         |
                                         +--------------------+--------------------+
                                         |                                         |
                                         v                                         v
                              +--------------------+                    +--------------------+
                              |     OpenRouter     |                    |   Walrus Memory    |
                              |  (GPT-4o-mini /    |                    |  (MemWal on Sui /  |
                              |   Clinical LLM)    |                    |   Decentralized)   |
                              +--------------------+                    +--------------------+
```

### Data Storage Boundaries

- **Supabase (PostgreSQL & Supabase Auth)**: The sole relational database engine for application data. Manages doctor authentication accounts, consultation sessions, message transcripts, and MemWal memory preference toggles. *(SQLite is not used)*.
- **Walrus Memory (MemWal)**: The decentralized, cryptographically isolated memory layer for clinical facts, indexed document chunks, patient longitudinal history, and physician profile notes.

---

## Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, React Hot Toast
- **Backend API**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, `uv` package manager
- **Relational Database & Auth**: Supabase (PostgreSQL, Supabase Auth, Async PostgREST Client)
- **Decentralized Clinical Memory**: Walrus Memory (`memwal[openai]`, Sui mainnet/testnet relayer)
- **LLM Reasoning**: OpenRouter (`openai/gpt-4o-mini`, AsyncOpenAI client)
- **Document Processing**: `pdftotext` (poppler-utils) with pure-Python stream fallback, CSV, JSON, base64 clinical imaging
- **Omnichannel Messaging**: Telegram Bot API (Webhooks + Telegram Login Widget)
- **Deployment & Reliability**: Render deployment with automated 14-minute keep-alive ping engine

---

## Environment Variables & Credentials (`.env`)

### 1. Backend (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` and provide your credentials:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Description | Example / Default |
|---|---|---|---|
| `SUPABASE_URL` | **Yes** | Supabase project URL | `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | **Yes** | Supabase public anonymous key | `eyJhbGci...` |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | Supabase privileged service role key | `eyJhbGci...` |
| `OPENROUTER_API_KEY` | **Yes** | OpenRouter API Key for clinical reasoning | `sk-or-v1-...` |
| `OPENROUTER_BASE_URL` | No | OpenRouter API Base URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | No | Clinical LLM model identifier | `openai/gpt-4o-mini` |
| `WALRUS_ENABLED` | No | Toggle Walrus persistent memory globally | `true` |
| `WALRUS_ENV` | No | Walrus network environment (`prod` or `dev`) | `prod` |
| `MEMWAL_PRIVATE_KEY` | **Yes** | Registered MemWal delegate private key | `0x...` |
| `MEMWAL_ACCOUNT_ID` | **Yes** | Registered MemWal account object ID on Sui | `0x...` |
| `MEMWAL_SERVER_URL` | No | MemWal relayer server URL | `https://relayer.memory.walrus.xyz` |
| `MEMWAL_VERIFY` | No | Whether to verify memory proofs | `false` |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram Bot API token from @BotFather | `123456789:ABCdef...` |
| `TELEGRAM_BOT_USERNAME` | Optional | Telegram Bot handle without `@` | `docpilot_AIbot` |
| `TELEGRAM_SECRET_TOKEN` | Optional | Random string to verify Telegram webhooks | `generate-random-token` |
| `TELEGRAM_WEBHOOK_URL` | Optional | HTTPS endpoint for Telegram webhooks | `https://your-domain.com/telegram/webhook` |
| `SECRET_KEY` | **Yes** | JWT signing secret (min 32 random chars) | `your-secure-random-jwt-secret-key` |
| `ENVIRONMENT` | No | Application environment (`development` or `production`) | `development` |
| `RENDER_KEEP_ALIVE_ENABLED` | No | Enables the background keep-alive ping loop | `true` |
| `RENDER_EXTERNAL_URL` | Optional | Public URL of the backend service on Render | `https://your-service.onrender.com` |

> 🔒 **Security Notice:** Never commit `.env` files to git. `backend/.env` is ignored in `.gitignore`.

### 2. Frontend (`frontend/.env.local`)

Copy `frontend/.env.example` to `frontend/.env.local`:

```bash
cp frontend/.env.example frontend/.env.local
```

| Variable | Required | Description | Example / Default |
|---|---|---|---|
| `VITE_API_BASE_URL` | **Yes** | Backend API origin | `http://localhost:8000` (local) or production backend URL |

---

## Database Setup (Supabase)

DocPilot exclusively uses **Supabase (PostgreSQL)**. Ensure the following tables exist in your Supabase project (you can execute this in the Supabase SQL Editor):

```sql
-- 1. Doctors table
CREATE TABLE IF NOT EXISTS public.doctors (
    id text PRIMARY KEY,
    email text UNIQUE NOT NULL,
    hashed_password text NOT NULL,
    full_name text,
    created_at timestamptz DEFAULT timezone('utc'::text, now())
);

-- 2. Doctor memory preferences (MemWal On/Off setting)
CREATE TABLE IF NOT EXISTS public.doctor_memory_preferences (
    doctor_id text PRIMARY KEY REFERENCES public.doctors(id) ON DELETE CASCADE,
    walrus_memory_enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz DEFAULT timezone('utc'::text, now()),
    updated_at timestamptz DEFAULT timezone('utc'::text, now())
);

-- 3. Telegram connections
CREATE TABLE IF NOT EXISTS public.telegram_connections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id text NOT NULL REFERENCES public.doctors(id) ON DELETE CASCADE,
    telegram_user_id bigint UNIQUE NOT NULL,
    telegram_chat_id bigint NOT NULL,
    telegram_username text,
    created_at timestamptz DEFAULT timezone('utc'::text, now())
);

-- 4. Consultation sessions
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id text PRIMARY KEY,
    doctor_id text NOT NULL REFERENCES public.doctors(id) ON DELETE CASCADE,
    title text NOT NULL,
    message_count int DEFAULT 0,
    created_at timestamptz DEFAULT timezone('utc'::text, now()),
    updated_at timestamptz DEFAULT timezone('utc'::text, now())
);

-- 5. Chat messages
CREATE TABLE IF NOT EXISTS public.docpilot_chat_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id text NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    doctor_id text NOT NULL REFERENCES public.doctors(id) ON DELETE CASCADE,
    role text NOT NULL,
    content text NOT NULL,
    attachments jsonb DEFAULT '[]'::jsonb,
    action_taken text,
    entities_extracted jsonb DEFAULT '[]'::jsonb,
    created_at timestamptz DEFAULT timezone('utc'::text, now())
);
```

---

## How to Run

### 1. Prerequisites

- **Python 3.11+** (Fastest setup: install [`uv`](https://docs.astral.sh/uv/))
- **Node.js 18+** & `npm`
- A configured **Supabase** project
- A **Walrus Memory** account & delegate key

---

### 2. Run the Backend

Navigate to the `backend/` directory:

```bash
cd backend
```

#### Option A: Using `uv` (Recommended)

```bash
# Sync dependencies
uv sync

# Start the FastAPI server with auto-reload
uv run uvicorn main:app --reload --port 8000
```

#### Option B: Using standard Python `venv` + `pip`

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate       # On Linux/macOS
# .venv\Scripts\activate       # On Windows

# Install backend dependencies
pip install -e .

# Start the server
uvicorn main:app --reload --port 8000
```

The backend will be live at:
- **API Root**: `http://localhost:8000/`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Keep-Alive Ping**: `http://localhost:8000/ping`

#### Running Backend Tests

```bash
cd backend
uv run pytest
```

---

### 3. Run the Frontend

In a separate terminal, navigate to the `frontend/` directory:

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend will run at `http://localhost:5173`.

#### Frontend Quality Checks

```bash
# Build production bundle
npm run build

# Run linter
npm run lint
```

---

## Core API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Register a new physician account |
| `POST` | `/auth/login` | Authenticate physician and issue access token |
| `GET` | `/auth/session` | Get current doctor profile from token |
| `POST` | `/auth/logout` | Clear physician session |
| `GET` | `/chat` or `/chats` | List previous consultation sessions |
| `POST` | `/chat` | Send a clinical note/query with optional documents |
| `GET` | `/chat/{id}` | Retrieve full message transcript for a consultation |
| `GET` | `/memory/preference` | Check doctor's MemWal persistent memory status |
| `PUT` | `/memory/preference` | Toggle MemWal persistent memory on or off |
| `POST` | `/telegram/connect` | Connect a Telegram account |
| `POST` | `/telegram/webhook` | Process incoming Telegram messages |
| `GET` | `/health` | Application health probe for Render / Docker |
| `GET` | `/ping` | Keep-alive ping endpoint (anti-spin-down) |

---

## Clinical Interaction Example

```text
Doctor:
"I am Doctor Saviour. Patient Maria Santos visited today with BP 150/95 mmHg.
Prescribed Amlodipine 10mg daily."

DocPilot:
"Welcome, Dr. Saviour. I have documented Maria Santos's clinical encounter:
- Vital Sign: BP 150/95 mmHg
- Medication: Amlodipine 10mg daily
This has been committed to your decentralized clinical memory."

--- Next Session ---

Doctor:
"Who am I?"

DocPilot:
"You are Dr. Saviour. How can I assist you with your consultations today?"

Doctor:
"What was Maria Santos's documented blood pressure?"

DocPilot:
"Based on your previous consultation notes, Maria Santos had a documented BP of 150/95 mmHg."
```

---

## Contributing

1. Create a feature branch (`git checkout -b feature/my-feature`).
2. Implement your changes following project guidelines.
3. Verify that all tests pass (`uv run pytest` and `npm run build`).
4. Commit your changes with clear messages.
5. Never commit real patient information or production credentials.

---

## License

See [LICENSE](LICENSE) for details.
