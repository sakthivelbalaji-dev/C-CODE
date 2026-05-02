# C Code Lab Backend (FastAPI + PostgreSQL)

## Setup

```bash
cd backend
python -m pip install -r requirements.txt
```

## Run API

```bash
uvicorn app.main:app --reload
```

API runs at: `http://127.0.0.1:8000`
Swagger docs: `http://127.0.0.1:8000/docs`

## Implemented Endpoints

- `POST /auth/signup`
- `POST /auth/login`
- `POST /questions/`
- `GET /questions/`
- `GET /questions/{question_id}`
- `POST /attempts/`
- `GET /attempts/`
- `POST /judge/c` (real C compile + run)

## Database

- Set **`DATABASE_URL`** to a `postgresql://…` connection string (required). Railway sets this when Postgres is attached.
- Tables auto-create on app startup (`create_all` + `ensure_schema_updates`).

## C Compiler Requirement

Install a C compiler and ensure it is available in PATH:

- Windows: `gcc` from MinGW-w64 (or `clang`)
- Linux/macOS: `gcc` or `clang`
