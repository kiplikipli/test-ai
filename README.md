# Enterprise Meeting Booking AI

Production-oriented hybrid architecture:
- **Frontend widget**: stateless HTML/JS chat client (`frontend/index.html`)
- **AI Brain**: FastAPI + LangChain + Redis (`ai-brain/`)
- **n8n Tools**: deterministic workflow endpoints (`n8n/workflows/`)

## Run

```bash
docker compose up --build
```

## Core contracts

- Chat payload:
  - `sessionId`
  - `message`
  - `userEmail`
  - `legalEntityId`
- AI endpoint: `POST /ai/process`
- Redis key: `meeting_session:{session_id}` with 4h TTL

## n8n workflow endpoints

- `POST /webhook/chat`
- `POST /webhook/tool/find_employees` (supports dynamic SQL generation when `ddl` + `request` are provided; otherwise uses safe fallback query)
- `POST /webhook/tool/validate_employees`
- `POST /webhook/tool/find_optimal_availability`
- `POST /webhook/tool/create_meeting`
