import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401 — register ORM models before create_all
from .database import Base, engine, ensure_schema_updates
from .routers import attempts, auth, judge, questions

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent
_FRONTEND_DIR = _REPO_ROOT / "frontend"

DIST_DIR = _BACKEND_DIR / "dist"
ASSETS_DIR = DIST_DIR / "assets"
INDEX_FILE = DIST_DIR / "index.html"


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

app = FastAPI(title="C Code Lab API", version="1.0.0")


@app.middleware("http")
async def normalize_legacy_judge_paths(request: Request, call_next):
    """Handle frontend relative URL bugs by rewriting nested judge paths."""
    path = request.scope.get("path", "")
    if path != "/api/judge/c" and path.endswith("/api/judge/c"):
        request.scope["path"] = "/api/judge/c"
    elif path != "/judge/c" and path.endswith("/judge/c"):
        request.scope["path"] = "/judge/c"
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
# Backward-compatible judge path for older built frontend bundles.
app.include_router(judge.router)

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/")
def health_check():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"status": "ok", "message": "C Code Lab backend is running"}


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
