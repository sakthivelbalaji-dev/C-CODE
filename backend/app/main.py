import logging
import os
import re
import json
import shutil
import subprocess
import sys
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401 — register ORM models before create_all
from .database import Base, engine, ensure_schema_updates, get_db
from .routers import admin, attempts, auth, judge, questions
from .schemas import JudgeRequest, JudgeResponse

logger = logging.getLogger(__name__)
DEFAULT_TEST_CASES_JSON = json.dumps(
    [
        {"input": "Mia\n19\n", "output": "Mia 19", "is_hidden": False},
        {"input": "Alex\n21\n", "output": "Alex 21", "is_hidden": False},
        {"input": "Zoe\n20\n", "output": "Zoe 20", "is_hidden": True},
    ]
)

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent
_FRONTEND_DIR = _REPO_ROOT / "frontend"

DIST_DIR = _BACKEND_DIR / "dist"
ASSETS_DIR = DIST_DIR / "assets"
INDEX_FILE = DIST_DIR / "index.html"
ADMIN_FILE = DIST_DIR / "admin.html"


def _skip_frontend_prepare() -> bool:
    return os.getenv("SKIP_FRONTEND_BUILD", "").strip().lower() in ("1", "true", "yes")


def _resolve_npm_executable() -> str | None:
    """Windows: npm is usually npm.cmd; list-form subprocess needs a real executable path."""
    if sys.platform == "win32":
        for name in ("npm.cmd", "npm"):
            path = shutil.which(name)
            if path:
                return path
        return None
    path = shutil.which("npm")
    return path


def prepare_frontend_dist() -> None:
    """Run `npm run build` in frontend/; Vite writes directly to backend/dist."""
    if _skip_frontend_prepare():
        logger.info("SKIP_FRONTEND_BUILD is set; using existing backend/dist.")
        return

    pkg = _FRONTEND_DIR / "package.json"
    if not pkg.exists():
        logger.warning("frontend/package.json not found; skipping frontend prepare.")
        return

    npm_exe = _resolve_npm_executable()
    env = os.environ.copy()
    logger.info("Building frontend into backend/dist (npm run build)…")
    if npm_exe:
        subprocess.run(
            [npm_exe, "run", "build"],
            cwd=str(_FRONTEND_DIR),
            check=True,
            env=env,
        )
    elif sys.platform == "win32":
        # Last resort: cmd.exe runs npm.cmd from PATH
        completed = subprocess.run(
            "npm run build",
            cwd=str(_FRONTEND_DIR),
            shell=True,
            check=False,
            env=env,
        )
        if completed.returncode != 0:
            raise subprocess.CalledProcessError(completed.returncode, "npm run build")
    else:
        raise RuntimeError(
            "npm not found on PATH. Install Node.js, or set SKIP_FRONTEND_BUILD=1 "
            "if backend/dist is already built."
        )

    if not INDEX_FILE.is_file():
        raise RuntimeError(f"Frontend build failed: missing {INDEX_FILE}")
    logger.info("Frontend static files ready at %s", DIST_DIR)


prepare_frontend_dist()

Base.metadata.create_all(bind=engine)
ensure_schema_updates()


def _auto_seed_questions_if_empty() -> None:
    """Fresh Postgres / Railway: populate questions like we auto-build frontend dist."""
    if os.getenv("AUTO_SEED_QUESTIONS", "1").strip().lower() in ("0", "false", "no"):
        logger.info("AUTO_SEED_QUESTIONS is off; skip empty-table question seed.")
        return
    from .database import SessionLocal
    from .topic_question_seeds import maybe_seed_topic_questions_if_empty

    db = SessionLocal()
    try:
        added = maybe_seed_topic_questions_if_empty(db)
        if added:
            logger.info("Questions table was empty: auto-seeded %d row(s).", added)
    except Exception:
        logger.exception("Auto-seed questions failed; continuing startup.")
        db.rollback()
    finally:
        db.close()


_auto_seed_questions_if_empty()


def _dedupe_and_fill_syllabus_questions() -> None:
    """
    Keep one row per title (merge attempts into keeper), then add missing syllabus rows.
    Prevents repeated questions and ensures full syllabus coverage.
    """
    from .database import SessionLocal
    from .models import Attempt, Question
    from .question_content import build_problem_content, resolve_template_key
    from .topic_question_seeds import (
        _difficulty_for_problem,
        parse_topic_from_full_title,
        seed_topic_questions_into_db,
        syllabus_row_semantic_key,
    )

    db = SessionLocal()
    try:
        if os.getenv("AUTO_FILL_SYLLABUS_GAPS", "1").strip().lower() in ("0", "false", "no"):
            logger.info("AUTO_FILL_SYLLABUS_GAPS is off; skip inserting missing seed rows on startup.")
        else:
            added = seed_topic_questions_into_db(db, reset=False)
            if added:
                logger.info("Added %d missing syllabus question(s).", added)

        rows = db.query(Question).order_by(Question.id.asc()).all()
        if not rows:
            return

        def _example_from_title(title: str) -> str:
            # "<module> — <topic> — Qx: Example" -> "Example"
            if ":" in title:
                return title.split(":", 1)[1].strip()
            return title.strip()

        # Normalize syllabus question content so test cases are canonical/correct.
        corrected = 0
        for question in rows:
            if not (question.module or "").startswith("Phase "):
                continue
            title_raw = question.title or ""
            if "Iseven" in title_raw:
                question.title = title_raw.replace("Iseven Function Loop", "Is Even Function Loop")
                corrected += 1
            example = _example_from_title(question.title or "")
            if not example:
                continue
            try:
                topic = parse_topic_from_full_title(question.module or "", question.title or "") or "General"
                content = build_problem_content(
                    question.module or "Phase 1 — Foundation",
                    topic,
                    example,
                )
                question.description = content.get("description", question.description)
                question.input_format = content.get("input_format", question.input_format)
                question.output_format = content.get("output_format", question.output_format)
                question.constraints = content.get("constraints", question.constraints)
                question.sample_input = content.get("sample_input", question.sample_input)
                question.expected_output = content.get("expected_output", question.expected_output)
                question.examples_json = content.get("examples_json", question.examples_json)
                question.test_cases_json = content.get("test_cases_json", question.test_cases_json)
                question.algorithm_hint = content.get("algorithm_hint", question.algorithm_hint)
                question.functions_hint = content.get("functions_hint", question.functions_hint)
                key = resolve_template_key(example)
                question.difficulty = _difficulty_for_problem(question.module or "", key)
                corrected += 1
            except Exception:
                continue

        # Remove repeats only when same module + topic + problem example (keeps one row per syllabus cell).
        by_semantic_key: dict[str, list[Question]] = {}
        for row in rows:
            semantic = syllabus_row_semantic_key(row.module or "", row.title or "")
            by_semantic_key.setdefault(semantic, []).append(row)

        deduped = 0
        for _, group in by_semantic_key.items():
            if len(group) <= 1:
                continue
            keeper = group[0]
            for duplicate in group[1:]:
                db.query(Attempt).filter(Attempt.question_id == duplicate.id).update(
                    {Attempt.question_id: keeper.id},
                    synchronize_session=False,
                )
                db.delete(duplicate)
                deduped += 1

        if corrected or deduped:
            db.commit()
        if corrected:
            logger.info("Corrected canonical content/test cases for %d syllabus question(s).", corrected)
        if deduped:
            logger.info("Removed %d duplicate question row(s) by semantic key.", deduped)
    except Exception:
        logger.exception("Failed to dedupe/fill syllabus questions.")
        db.rollback()
    finally:
        db.close()


_dedupe_and_fill_syllabus_questions()


def _ensure_test_cases_for_all_questions() -> None:
    """
    Ensure every question has non-empty test_cases_json.
    Fills missing entries by copying from the first available question
    that already has test cases, else uses built-in defaults.
    """
    from .database import SessionLocal
    from .models import Question
    from .question_content import build_problem_content

    db = SessionLocal()
    try:
        rows = db.query(Question).all()
        if not rows:
            return

        def has_cases(q: Question) -> bool:
            raw = (q.test_cases_json or "").strip()
            if not raw:
                return False
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return False
            if not isinstance(parsed, list) or not parsed:
                return False
            for row in parsed:
                if not isinstance(row, dict):
                    return False
                if "input" not in row or "output" not in row:
                    return False
            return True

        def example_from_title(title: str) -> str:
            # "<module> — <topic> — Qx: Example" => "Example"
            if ":" in title:
                return title.split(":", 1)[1].strip()
            return title.strip()

        source = next((q for q in sorted(rows, key=lambda q: q.id) if has_cases(q)), None)
        source_payload = source.test_cases_json if source else DEFAULT_TEST_CASES_JSON

        updated = 0
        for question in rows:
            if not has_cases(question):
                try:
                    content = build_problem_content(
                        question.module or "Phase 1 — Foundation",
                        question.module or "General",
                        example_from_title(question.title or ""),
                    )
                    payload = content.get("test_cases_json", "")
                    if isinstance(payload, str) and payload.strip():
                        question.test_cases_json = payload
                    else:
                        question.test_cases_json = source_payload
                except Exception:
                    question.test_cases_json = source_payload
                updated += 1

        if updated:
            db.commit()
            logger.info("Backfilled test_cases_json for %d question(s).", updated)
    except Exception:
        logger.exception("Failed to backfill missing test cases.")
        db.rollback()
    finally:
        db.close()


_ensure_test_cases_for_all_questions()


def _renumber_phase_question_titles() -> None:
    """Ensure each Phase module uses serial Q numbers (Q1, Q2, Q3...)."""
    from .database import SessionLocal
    from .models import Question
    from .syllabus import question_syllabus_sort_key

    db = SessionLocal()
    try:
        rows = db.query(Question).all()
        if not rows:
            return

        phase_rows = [q for q in rows if (q.module or "").startswith("Phase ")]
        if not phase_rows:
            return

        grouped: dict[str, list[Question]] = {}
        for question in phase_rows:
            grouped.setdefault(question.module, []).append(question)

        changed = 0
        for module_name, items in grouped.items():
            ordered = sorted(
                items,
                key=question_syllabus_sort_key,
            )
            for idx, question in enumerate(ordered, start=1):
                old_title = question.title or ""
                if re.search(r"\bQ\s*\d+\b", old_title, flags=re.IGNORECASE):
                    new_title = re.sub(
                        r"\bQ\s*\d+\b",
                        f"Q{idx}",
                        old_title,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                else:
                    new_title = f"{old_title} — Q{idx}"
                if new_title != old_title:
                    question.title = new_title
                    changed += 1

        if changed:
            db.commit()
            logger.info("Renumbered %d phase question title(s) to serial Q order.", changed)
    except Exception:
        logger.exception("Failed to renumber phase question titles.")
        db.rollback()
    finally:
        db.close()


_renumber_phase_question_titles()

app = FastAPI(title="C Code Lab API", version="1.0.0")


@app.middleware("http")
async def normalize_legacy_judge_paths(request: Request, call_next):
    """Handle frontend relative URL bugs by rewriting nested API paths."""
    path = request.scope.get("path", "")
    compact_path = re.sub(r"/+", "/", path)
    compact_no_slash = compact_path.rstrip("/") or "/"

    rewritten_path = None

    # If frontend calls nested routes like /question/api/judge/c, strip prefix.
    api_idx = compact_no_slash.find("/api/")
    if api_idx > 0:
        rewritten_path = compact_no_slash[api_idx:]

    # Dedicated compatibility for judge endpoints with/without /api.
    if compact_no_slash.endswith("/api/judge/c"):
        rewritten_path = "/api/judge/c"
    elif compact_no_slash.endswith("/judge/c"):
        rewritten_path = "/judge/c"

    if rewritten_path and rewritten_path != path:
        request.scope["path"] = rewritten_path
        request.scope["raw_path"] = rewritten_path.encode("utf-8")
    return await call_next(request)


@app.middleware("http")
async def browser_compat_headers(request: Request, call_next):
    """Consistent MIME/referrer behaviour across Chromium, Safari, Firefox, Edge."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    ctype = response.headers.get("content-type", "")
    if "text/html" in ctype.lower():
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


# CORS: `allow_credentials=True` is invalid with allow_origins=["*"] — browsers enforce that.
# Default: wildcard, no credentials. Set CORS_ALLOWED_ORIGINS=comma,separated URLs to allow credentialed cross-origin.
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
if _cors_origins_env:
    _cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    _cors_credentials = True
else:
    _cors_origins = ["*"]
    _cors_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")
app.include_router(judge.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
# Backward-compatible judge path for older built frontend bundles.
app.include_router(judge.router)


@app.post("/{_prefix:path}/api/judge/c", response_model=JudgeResponse)
def nested_api_judge_proxy(_prefix: str, payload: JudgeRequest, db: Session = Depends(get_db)):
    """Fallback for buggy relative frontend calls from nested SPA routes."""
    return judge.judge_c_code(payload, db)


@app.post("/{_prefix:path}/judge/c", response_model=JudgeResponse)
def nested_judge_proxy(_prefix: str, payload: JudgeRequest, db: Session = Depends(get_db)):
    """Fallback for legacy nested /judge/c calls."""
    return judge.judge_c_code(payload, db)

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/")
def health_check():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"status": "ok", "message": "C Code Lab backend is running"}


@app.get("/admin")
def serve_admin_panel():
    """Prefer legacy admin.html if present; otherwise SPA index (staff /admin route)."""
    if ADMIN_FILE.exists():
        return FileResponse(str(ADMIN_FILE))
    if INDEX_FILE.is_file():
        return FileResponse(str(INDEX_FILE))
    raise HTTPException(status_code=404, detail="Admin not available")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """SPA deep links (/login etc.); `/api/*` stays on API router (avoid catching unknown API paths here)."""
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
    if INDEX_FILE.is_file():
        return FileResponse(str(INDEX_FILE))
    return {"status": "ok", "message": "C Code Lab backend is running"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
