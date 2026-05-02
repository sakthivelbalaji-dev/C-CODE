# C Code Lab

C Code Lab is a full-stack coding practice platform for C programming with:
- timed questions,
- test-case based judging,
- student/staff roles,
- leaderboard and performance tracking.

## Tech Stack

- Frontend: React 19, Vite 8, Tailwind CSS, React Router, Monaco Editor
- Backend: FastAPI, SQLAlchemy ORM, Pydantic
- Database: PostgreSQL only (`DATABASE_URL` required)
- Dev tooling: ESLint, PostCSS, concurrently

## Browser support

- **Deployed HTML** (`backend/dist/index.html`): viewport/referrer/X-UA-Compatible meta, `<noscript>` fallback, and `nomodule` messaging for browsers without ES module support.
- **HTTP responses** (`app/main.py`): `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and `Cache-Control: no-cache` for HTML (reduces stale-shell issues after deploy).
- **Rebuild the SPA** for maximum reach: `frontend/vite.config.js` enables **`@vitejs/plugin-legacy`** (polyfills + legacy bundles). After pulling, run in `frontend/`:

  ```bash
  npm i -D @vitejs/plugin-legacy terser
  ```

  Then `npm run build` from the repo root (or `frontend`). If you already maintain your own `vite.config`, merge the `legacy` plugin and `build.outDir` → `../backend/dist` as before.

  Very old browsers (for example IE11) are **not** supported by React 19; legacy output covers widely used evergreen and mobile Safari-class engines.

## Compiler and Judge

C code is compiled and executed by the backend judge (`backend/app/routers/judge.py`).

- Primary compiler: `gcc`
- Compile flags: `-O2 -std=c11 -Wall -Wformat=2`
- Fallback compilers (if gcc missing): `clang`, `cc` (and Windows fallback paths)
- Runtime: compiled binary is executed in a temporary folder
- Timeout controls:
  - compile timeout: 8 seconds
  - run timeout: 2 seconds
- Error handling: graceful failure if compiler is unavailable

## Project Structure

```text
c-code-lab/
├─ backend/
│  ├─ app/
│  │  ├─ routers/
│  │  │  ├─ auth.py
│  │  │  ├─ attempts.py
│  │  │  ├─ judge.py
│  │  │  └─ questions.py
│  │  ├─ database.py
│  │  ├─ main.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  ├─ email_policy.py
│  │  ├─ question_content.py
│  │  ├─ student_hints.py
│  │  └─ syllabus.py
│  │
│  ├─ dist/                   # auto-generated (React build comes here)
│  │  ├─ index.html
│  │  └─ assets/
│  │
│  ├─ requirements.txt
│
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ hooks/
│  │  ├─ lib/
│  │  ├─ pages/
│  │  ├─ App.jsx
│  │  └─ main.jsx
│  │
│  ├─ public/
│  ├─ package.json
│  └─ vite.config.js          # build output → ../backend/dist
│
├─ node_modules/              # auto (root-level optional)
├─ package.json
├─ package-lock.json
├─ Dockerfile                 # for Railway (optional for now)
├─ Procfile                   # for Railway (optional for now)
└─ README.md
```

## Run Locally

### 1) Install frontend dependencies

```bash
npm install
```

### 2) Install backend dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

### 3) Start FastAPI (single service: API + frontend)

From the **`backend/`** directory (needs **Node/npm** on your PATH):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On import, **`app/main.py` runs `npm run build` in `frontend/`**. **Vite writes straight into `backend/dist/`** (no separate `frontend/dist` folder).

- App: `http://127.0.0.1:8000`
- API base: `http://127.0.0.1:8000/api`
- API docs: `http://127.0.0.1:8000/docs`

**(Optional)** Build only the SPA without starting the server:

```bash
npm run build
```

(from repo root; writes `backend/dist/` via `frontend/vite.config.js`)

## Environment Variables

- `DATABASE_URL` (**required** — local and Railway)
  - Example: `postgresql://USER:PASSWORD@HOST:5432/DBNAME`
  - Railway: attach the Postgres service; `DATABASE_URL` is set automatically (`postgres://` is normalized to `postgresql://`).
- `PORT`
  - Used in production by Railway (`uvicorn` reads this value).
- `SKIP_FRONTEND_BUILD`
  - If set to `1`/`true`/`yes`, skips `npm run build` and the copy step (use Docker images that already populate `backend/dist`, or backend-only workflows).
  - With `uvicorn --reload`, set this after your first successful build if you want faster restarts during API-only edits (avoids rebuilding into `backend/dist` on each reload).
- `STAFF_EMAIL_ALLOWLIST`
  - Must list **exactly two** comma-separated institutional emails. Only those addresses may use **Staff signup** or **Staff login**. Students use **Student** tab only; any other staff email gets `403`.
  - Defaults in code: `hod.aids@rajalakshmi.edu.in`, `staff.aids@rajalakshmi.edu.in`. Override on Railway by setting this variable if you ever change addresses.
  - Example: `STAFF_EMAIL_ALLOWLIST=hod.aids@rajalakshmi.edu.in,staff.aids@rajalakshmi.edu.in`
- `AUTO_SEED_QUESTIONS` (default **on**)
  - On app startup, if the **`questions`** table has **zero** rows, the server inserts the full **110** topic-based syllabus set (same as `python seed_topic_questions.py` without `--reset`).
  - Set to `0` / `false` / `no` if you want an empty bank and will load questions yourself (SQL or CLI).

Optional: **`backend/scripts/provision_staff.py`** can create the two rows with a preset password instead of staff using Sign up:

```bash
cd backend && python scripts/provision_staff.py --password "YOUR_STRONG_INITIAL_PASSWORD"
```

**Syllabus questions (5 per topic, 110 total):** on a **fresh** empty database, the app **auto-seeds** these on first startup (see `AUTO_SEED_QUESTIONS`). To re-run or wipe manually with `DATABASE_URL` set, from `backend/`:

```bash
python seed_topic_questions.py --reset
```

`--reset` deletes all attempts and questions, then inserts the full set. Omit `--reset` to only append titles that are not already present.

## API and Frontend Integration

- All backend routes are prefixed with `/api`.
- Frontend uses `/api` as base URL (`frontend/src/lib/api.js`).
- **Vite** writes the production bundle directly to **`backend/dist/`**.
- **`backend/app/main.py`** runs the build at startup unless `SKIP_FRONTEND_BUILD` is set.
- FastAPI serves:
  - `/assets/*` from `backend/dist/assets`
  - `/` and other SPA routes from `backend/dist/index.html`

## Deploy on Railway (Single Service)

### Option A: Docker deploy (recommended)

1. Ensure Railway has a PostgreSQL plugin/service attached.
2. Set environment variable:
   - `DATABASE_URL` to Railway PostgreSQL URL
3. Deploy using the project `Dockerfile`.
4. Service runs with:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8080`

### Option B: Procfile deploy

- Root **`Procfile`**: starts uvicorn with `--app-dir backend`.
- Prefer **Docker** for production: the Python runtime image does not include Node, so **`SKIP_FRONTEND_BUILD=1`** is set in `Dockerfile` and the frontend is built in a Node stage then copied into `backend/dist`.

## Main Scripts

- `npm run dev` -> start Vite frontend
- `npm run dev:api` -> start FastAPI backend
- `npm run dev:full` -> run frontend + backend together
- `npm run build` -> production build to `frontend/dist/` (uvicorn startup also runs this unless skipped)
- `npm run lint` -> lint frontend code
