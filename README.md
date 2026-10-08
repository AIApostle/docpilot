# DocPilot

> Conversational medical memory for doctors.

DocPilot is a doctor-facing AI assistant that lets doctors **store, retrieve, and update patient information through natural language** across web and Telegram.

Walrus Memory provides persistent patient memory, while the OpenAI Agents SDK handles agent orchestration.

> **Note:** DocPilot is an experimental MVP. Use synthetic patient data only. It is not an EHR or autonomous clinical decision-maker.

## What It Does

- Conversational patient memory
- Cross-session memory
- Patient information updates
- Natural-language retrieval
- Doctor-specific memory isolation
- Telegram integration
- Clarification for ambiguous patient references
- Grounded responses based on stored information

## Architecture

```text
Web / Telegram
      |
      v
   FastAPI
      |
      v
 DocPilot Agent
   /       \
  v         v
OpenAI   Walrus Memory
             |
       Patient Memory
```

SQLite stores application metadata such as doctor accounts and Telegram mappings.

## Tech Stack

- React / Next.js + TypeScript
- Python + FastAPI
- Walrus Memory
- OpenAI Agents SDK
- OpenAI Models
- SQLite
- Telegram Bot API

## Setup

### 1. Clone

```bash
git clone <repository-url>
cd docpilot
```

### 2. Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Environment Variables

Create your `.env` files using the project's environment example.

```env
OPENAI_API_KEY=
WALRUS_API_KEY=
TELEGRAM_BOT_TOKEN=
JWT_SECRET=
```

Never commit real secrets.

## Running Locally

Backend:

```bash
uvicorn app.main:app --reload
```

Frontend:

```bash
npm run dev
```

## Core API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create doctor account |
| POST | `/auth/login` | Authenticate doctor |
| POST | `/chat` | Conversational memory |
| POST | `/telegram/connect` | Connect Telegram |
| POST | `/telegram/webhook` | Receive Telegram events |
| DELETE | `/telegram/disconnect` | Disconnect Telegram |

## Memory Model

Walrus Memory stores:

- Patient history
- Diagnoses and conditions
- Allergies
- Medications
- Visits and clinical notes
- Measurements and observations

Each doctor has an isolated memory namespace. The backend resolves the namespace from the authenticated doctor; clients cannot select one.

DocPilot should never invent undocumented patient information. If a patient reference is ambiguous, it should ask for clarification.

## Example

```text
Doctor:
I saw John Doe today. He's 42, has hypertension,
and is allergic to penicillin.

DocPilot:
I've recorded the documented information about John Doe.
```

Later, in a new session:

```text
Doctor:
What do you remember about John Doe?

DocPilot:
John Doe is 42 and has documented hypertension.
His documented allergy is penicillin.
```

## Contributing

1. Create a feature branch.
2. Make your changes.
3. Add tests where appropriate.
4. Do not commit secrets or real patient data.
5. Open a pull request describing your changes.

For major changes, open an issue first.

## Safety

DocPilot does **not**:

- Diagnose patients
- Prescribe medication
- Make autonomous treatment decisions
- Replace doctors or clinical systems

Development and demos must use synthetic patient data.

## Roadmap

- Improved memory retrieval
- Structured patient timelines
- Better longitudinal context
- Additional communication interfaces
- Healthcare system integrations
- Advanced audit and access controls

## License

See [LICENSE](LICENSE).
