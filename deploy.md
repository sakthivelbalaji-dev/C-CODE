# C Code Lab — PostgreSQL & Railway Deployment Analysis

Structured database analysis for the **FastAPI backend** under `backend/app/`. Generated for optimization and Railway (500 MB PostgreSQL) planning. **`attempts`-table anti-bloat behaviors are implemented** in `routers/attempts.py`, `models.py`, `schemas.py`, and **PostgreSQL bootstrapping for `is_best_attempt`** in `database.py` — see **§10**.

---

## 1. DATABASE CONFIGURATION

| Item | Detail |
|------|--------|
| **Database** | **PostgreSQL only** — `DATABASE_URL` is **required** (missing value raises at import). |
| **Production target** | **PostgreSQL** on Railway (attach Postgres; use injected `DATABASE_URL`). |
| **Config location** | `backend/app/database.py` — reads `DATABASE_URL`, builds engine, exposes `SessionLocal`, `Base`, `get_db`, `ensure_schema_updates`. |
| **Connection string** | `os.getenv("DATABASE_URL")`. After normalization: **`postgres://` → `postgresql://`** (Railway/Heroku-style URLs). |
| **`DATABASE_URL` supported** | **Yes.** This is the primary mechanism for Railway Postgres. |

**Operational note:** Startup in `main.py` calls `Base.metadata.create_all(bind=engine)` then `ensure_schema_updates()`. There is **no Alembic** (or other migration runner) in the tree.

---

## 2. SQLALCHEMY SETUP

| Area | Implementation |
|------|----------------|
| **Engine** | `create_engine(DATABASE_URL, pool_pre_ping=True)` — PostgreSQL only. |
| **Session** | `sessionmaker(autocommit=False, autoflush=False, bind=engine)` as `SessionLocal`; FastAPI dependency `get_db()` yields a session and closes it in `finally`. |
| **Base** | `declarative_base()` from `sqlalchemy.orm`, assigned to `Base` in `database.py`. Models import `Base` from there. |
| **PostgreSQL compatibility** | **Generally compatible:** standard types (`Integer`, `String`, `Text`, `Boolean`, `DateTime(timezone=True)`), FKs with `ondelete="CASCADE"`, no raw SQLite SQL in request paths. |

**PostgreSQL caveats (schema lifecycle, not query syntax):**

1. **`ensure_schema_updates()`**: Uses **`inspect()`** and conditional **`ALTER TABLE`** for legacy columns on **students**, **questions**, and **`attempts.is_best_attempt`** when missing (helps older DBs that predate those columns).

2. **Schema management** still relies heavily on **`create_all`**. That creates **missing tables** only; it does **not** evolve all column types reliably for existing databases. **`is_best_attempt`** on Postgres is patched as above; a **full Alembic** workflow is still recommended for complex changes.

3. **Driver:** `psycopg2-binary` is listed in `backend/requirements.txt` (see §7).

---

## 3. MODELS (FULL INVENTORY)

ORM definitions: **`backend/app/models.py`**. Three tables.

### Table: `students`

| Column | Type (SQLAlchemy → typical PostgreSQL) | Constraints / notes |
|--------|----------------------------------------|---------------------|
| `id` | `Integer` → `INTEGER` | **PK**, `index=True` |
| `name` | `String(120)` → `VARCHAR(120)` | `NOT NULL` |
| `email` | `String(255)` → `VARCHAR(255)` | `NOT NULL`, **UNIQUE**, `index=True` |
| `password` | `String(255)` → `VARCHAR(255)` | `NOT NULL` (plaintext in app flow — security concern, unrelated to Postgres) |
| `role` | `String(20)` → `VARCHAR(20)` | `NOT NULL`, default `"student"` |
| `created_at` | `DateTime(timezone=True)` → `TIMESTAMPTZ` | `server_default=func.now()` |

**Relationships:**

- `attempts` → one-to-many **`Attempt`**, `back_populates="student"`, `cascade="all, delete"`.

**Foreign keys:** none (root entity).

---

### Table: `questions`

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | `Integer` | **PK**, `index=True` |
| `title` | `String(200)` | `NOT NULL` |
| `description` | `Text` | `NOT NULL` |
| `module` | `String(100)` | `NOT NULL` |
| `difficulty` | `String(20)` | `NOT NULL`, default `"medium"` |
| `input_format` | `Text` | nullable |
| `output_format` | `Text` | nullable |
| `constraints` | `Text` | nullable |
| `sample_input` | `Text` | nullable |
| `expected_output` | `Text` | nullable |
| `examples_json` | `Text` | nullable (JSON string) |
| `test_cases_json` | `Text` | nullable (JSON string) |
| `time_limit_minutes` | `Integer` | `NOT NULL`, default `15` |
| `algorithm_hint` | `Text` | nullable |
| `functions_hint` | `Text` | nullable |
| `efficient_solution` | `Text` | nullable (reference solution / teaching content) |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` |

**Relationships:**

- `attempts` → one-to-many **`Attempt`**, `back_populates="question"`, `cascade="all, delete"`.

**Foreign keys:** none.

---

### Table: `attempts`

| Column | Type | Constraints / notes |
|--------|------|---------------------|
| `id` | `Integer` | **PK**, `index=True` |
| `student_id` | `Integer` | `NOT NULL`, **FK** `students.id` **`ON DELETE CASCADE`** |
| `question_id` | `Integer` | `NOT NULL`, **FK** `questions.id` **`ON DELETE CASCADE`** |
| `submitted_code` | `Text` | `NOT NULL` — stores **full C source only when `is_correct` is true**; for incorrect submissions the row stores a **short fixed placeholder** (`[incorrect submission — code not stored]`) so PostgreSQL/`NOT NULL` compatibility is preserved without retaining large wrong-answer payloads. **`POST /api/attempts/`** still echoes the client’s submitted code **in that response body** immediately after submit. |
| `score` | `Integer` | default `0` |
| `passed_cases` | `Integer` | default `0` |
| `failed_cases` | `Integer` | default `0` |
| `is_correct` | `Boolean` | default `False` |
| `feedback` | `Text` | nullable; **truncated to 500 characters** at insert time (`create_attempt`). |
| `is_best_attempt` | `Boolean` | `NOT NULL`, default **`false`** — **exactly one** row per **`(student_id, question_id)`** is flagged **`true`** (highest `score`; tie-break **newest** by `created_at`, then **`id`**). Maintained whenever a row is inserted and after retention pruning for that pair. |
| `created_at` | `DateTime(timezone=True)` | `server_default=func.now()` |

**Relationships:**

- `student` → many-to-one **`Student`**, `back_populates="attempts"`.
- `question` → many-to-one **`Question`**, `back_populates="attempts"`.

---

## 4. DATA SIZE ANALYSIS

| Table | Growth rate | Estimated row size (order of magnitude) | Notes |
|-------|-------------|----------------------------------------|--------|
| **`attempts`** | **Highest** — one row **per HTTP submit** until **retention** applies | **`submitted_code`:** incorrect rows retain only a **~40-byte placeholder** (not full sources). **`correct` successes** still retain full sources (typically **~1–20+ KB**). **`feedback`:** capped **500 chars** server-side. **Hard cap:** at most **20 rows per `(student_id, question_id)`** (older rows deleted after each insert via ordered query + bulk delete). **Observed footprint is far lower than “every failure stores full source” workloads.** |
| **`questions`** | Low after initial seed / staff authoring | **Moderate:** multiple `TEXT` fields + JSON blobs (`examples_json`, `test_cases_json`, hints, `efficient_solution`). Often **few KB to tens of KB** per question. Bounded by syllabus size. | Static compared to attempts. |
| **`students`** | Low (user signups) | **Small:** sub‑KB per row | Negligible vs attempts at scale. |

**500 MB risk:**

- **Bounded question bank + moderate attempts:** Usually **safe**.
- **High volume of *correct* solutions** retained (bounded to **≤20 tries per pair**, but successes still store **full sources**): still the main residual growth vector; magnitude depends on correctness rate and submission size — **incorrect spam is no longer a large `TEXT` consumer.**

**Large / bloat-prone fields:**

- **`attempts.submitted_code`** — significant **only for `is_correct` rows.** Failures persist a negligible placeholder text.
- **`attempts.feedback`** — capped at **500 characters** when saving (see §10).
- **`questions`:** `test_cases_json`, `examples_json`, `description`, hints, **`efficient_solution`** — sizable but **not** per-submit; total size scales with **number of questions**, not submissions.

---

## 5. JUDGE DATA USAGE (WHAT HITS THE DATABASE)

| Concern | Finding |
|---------|---------|
| **User code in DB** | **Only for submissions saved as correct (`is_correct == true`).** Incorrect attempts persist a constant **placeholder string** instead of student source; **`POST /api/attempts/` keeps returning full source in JSON** immediately after submission for UI parity. Judge paths still do not persist stderr/stdout. |
| **Execution logs / stdout / stderr per test case** | **Not persisted** in the reviewed models. **`POST /api/judge/c`** compiles/runs in a temp directory and returns **`JudgeResponse`** (compile output + per-case results) **without writing runs to the database** — it only **reads** `Question` / `test_cases_json` when `question_id` is set. |
| **Compile output / “got” vs “expected”** | **Response-only** for judge; **not** stored as separate log rows unless the **client** sends them into `feedback` on `Attempt` (possible bloat if abused or very verbose). |

**Conclusion:** Most remaining `attempts` footprint comes from persisted **correct** submissions (`submitted_code`) plus **capped** `feedback`; **incorrect** attempts stay small on disk. Judge execution logs are not stored server-side as row data.

---

## 6. API → DB FLOW

Prefix: **`/api`** (routers registered in `main.py`).

### Writes (`commit` / `add`)

| Endpoint | Method | DB effect |
|----------|--------|-----------|
| `/api/auth/signup` | POST | **INSERT** `students` |
| `/api/questions/` | POST | **INSERT** `questions` (JSON fields serialized to `examples_json` / `test_cases_json`) |
| `/api/attempts/` | POST | **INSERT** `attempts` (+ optional **DELETE older rows** beyond **20/latest per `(student_id,question_id)`**); **truncate `feedback`**; **placeholder `submitted_code` if incorrect**; **refresh `is_best_attempt`** flags for that pair |

### Implemented write-side transaction semantics (`attempts`)

- Single **`flush` → prune → recomputation → commit`** on **`POST /api/attempts/`**.
- Deletes use **`bulk delete`** by primary key **`IN (…)`** from an **ordered-offset** query (**SQLAlchemy ORM**, no handwritten raw SQL strings in router).

**Non-HTTP writers (operators):**

- `backend/scripts/provision_staff.py` — inserts/updates staff users.
- `seed_syllabus_questions.py`, `backfill_question_content.py`, `backfill_question_difficulty.py` — bulk question maintenance.

### Reads

| Endpoint | Method | Primary reads |
|----------|--------|----------------|
| `/api/auth/login` | POST | `students` filter by email/password/role |
| `/api/auth/students` | GET | `students` |
| `/api/questions/` | GET | `questions` (+ ordering) |
| `/api/questions/resume/next` | GET | `students`, `attempts` (distinct solved), **`questions` full list ordered** |
| `/api/questions/{id}/syllabus-next` | GET | **`questions` — loads full ordered list in Python** |
| `/api/questions/{question_id}` | GET | `questions` |
| `/api/questions/{question_id}/efficient-solution` | GET | `questions`, `attempts` existence check |
| `/api/attempts/` | GET | **`attempts` (optional filter)** + batch `questions`/`students` for titles/names |
| `/api/attempts/leaderboard` | GET | **JOIN** `students` + aggregates on `attempts` |
| `/api/judge/c` | POST | `questions` (if `question_id` present) |

### Redundant / heavy patterns

- **`POST /api/attempts/`** after insert runs **additional reads** for “next question” computation (distinct solved attempts + ordered question IDs) — **extra read load**, not duplicate writes.
- **`GET /api/attempts/`** **without `student_id`** loads **all attempts** — **risk for large databases** (memory/payload size), not extra disk writes.
- **`resume/next`** and **`syllabus-next`** load **all questions** ordered — acceptable for **small/medium banks**, weaker if question count scales very large.

---

## 7. POSTGRESQL MIGRATION CHECK

| Question | Answer |
|----------|--------|
| **Is code ready for PostgreSQL?** | **YES**, for connecting and running CRUD against models with `DATABASE_URL` pointing at Postgres, **provided** schema is created consistently with `models.py` (typically fresh `create_all` on Railway). |

| Requirement | Status |
|-------------|--------|
| **`psycopg2-binary` needed?** | **Already in** `backend/requirements.txt`. |
| **`postgres://` → `postgresql://` fix?** | **Implemented** in `database.py` (`removeprefix("postgres://")` → `postgresql://`). |
| **SQLite-specific code?** | **None** — PostgreSQL only; **`ensure_schema_updates()`** uses **`inspect()`** + **`ALTER TABLE`** for missing legacy columns (see §2). |
| **Gaps** | **No Alembic** full history; **existing rows created before these features** retain **full-source `submitted_code` for failures** until replaced by new submits; **`is_best_attempt` on legacy multi-row pairs** stays **`false`** on all rows until touched by inserts or a manual backfill. Password storage is plaintext (deployment/security topic). |

---

## 8. OPTIMIZATION SUGGESTIONS

**Already implemented**

- **`attempts` retention**: **20-row cap** per **`(student_id, question_id)`** on each insert (**§10**).
- **Failures:** **no persisted full-source** on incorrect attempts (placeholder **`Text`** stored).
- **`feedback` truncation:** **500 characters** (**§10**).

**Further optional optimizations**

- **Correct-only blobs:** offload **successful** **`submitted_code`** to external object storage **if sources grow large**.
- **`is_best_attempt` consumers:** dashboards can prefer best rows-only reads (not yet wired in leaderboard; leaderboard still sums/scores/all attempts per design).

**Retention / archiving**

- **Rolling cap** replaces need for nightly purge except for **historic correct sources** archived elsewhere if required.

**Indexing (PostgreSQL)**

- Composite indexes now align well with pruning/sorting hot paths (`student_id`,`question_id`,`created_at`): consider explicit definitions if EXPLAIN shows seq scans under load — same list as previously:
  - **`attempts(student_id, question_id, created_at DESC)`** complements retention lookups.
  - **`attempts(question_id)`**, **`attempts(student_id, question_id, is_correct)`** for syllabus/progress probes.
- **`students(email)`** already indexed (unique).
- **Leaderboard query** aggregates by `student_id` — supporting indexes on **`attempts(student_id)`** help.

**Application behavior**

- **Paginate** `GET /api/attempts/` and default `student_id` for non-admin clients.
- Avoid loading **entire** `questions` table for every resume/syllabus-next if the bank grows large (cursor / SQL window — future design).

---

## 9. FINAL VERDICT — Railway 500 MB PostgreSQL

**Trending YES with post-mitigations.**

- **`attempts`** are **automatically capped** per question per student; **`feedback`** capped; **`submitted_code` bloat primarily tracks successful submissions** (`is_correct`).
- **`NO`** only remains plausible if instructors expect **dense long correct solutions retained across tens of thousands of rows** alongside very large authored **`questions`** content — tune **attempt cap downward** further or archive **successful** submits externally if instrumentation shows TOAST-heavy growth.

---

## 10. IMPLEMENTED ATTEMPT RETENTION & STORAGE POLICY

| Behavior | Detail |
|---------|--------|
| **Row cap per pair** | After each **`POST /api/attempts/`**, keep only the newest **20** attempts for that **`student_id`** + **`question_id`** (**`created_at` DESC**, **`id` DESC** as tie-break); delete surplus via ORM **`delete()`**. |
| **Incorrect code storage** | **`submitted_code = "[incorrect submission — code not stored]"`** (compact placeholder). |
| **`POST` response fidelity** | HTTP **201 payload** **`submitted_code`** field **still mirrors the freshly submitted student source**, even though the DB persisted the placeholder for failures — existing clients (**e.g. `localStorage` patterns**) keep working without UI regressions from missing response text. **`GET /list`** returns DB-stored value (placeholder for failures). |
| **`feedback`** | **≤ 500 Unicode code points sliced** Python-side **`[:500]`**. |
| **`is_best_attempt`** | Recomputed row flags per **`(student_id, question_id)`** after prune: **max `score`** first, then **`created_at`**, then **`id`**. Responses include this boolean (**`AttemptOut` / `AttemptDetailOut`**). **Leaderboard** logic unchanged (**still aggregates all attempts**, so scoring semantics stay identical). |

**Constants (`routers/attempts.py`):** `MAX_ATTEMPTS_PER_QUESTION = 20`, `MAX_FEEDBACK_CHARS = 500`, **`INCORRECT_CODE_PLACEHOLDER`**.

---

## Appendix: File references

| Concern | Path |
|---------|------|
| Engine, URL, sessions, schema patches | `backend/app/database.py` |
| Models | `backend/app/models.py` |
| `create_all` + router mount | `backend/app/main.py` |
| HTTP DB usage | `backend/app/routers/auth.py`, `questions.py`, `attempts.py`, `judge.py` |
| Pydantic payloads | `backend/app/schemas.py` |
| Python deps | `backend/requirements.txt` |
| Container image | `Dockerfile` (root) |
