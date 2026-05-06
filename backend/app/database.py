import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Load .env ONLY for local development
if os.getenv("ENV") != "production":
    _backend_dir = Path(__file__).resolve().parents[1]
    _repo_root = _backend_dir.parent
    load_dotenv(_repo_root / ".env")
    load_dotenv(_backend_dir / ".env")

# Get DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. On Railway, attach PostgreSQL and use the injected variable."
    )

# Fix Railway postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL.removeprefix("postgres://")

# Enforce PostgreSQL only
if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError(
        "DATABASE_URL must be PostgreSQL (postgresql://). SQLite is not supported."
    )

# Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()


def ensure_schema_updates():
    """Incremental ALTERs for existing DB schema."""
    inspector = inspect(engine)

    if not inspector.has_table("students"):
        return

    with engine.begin() as connection:
        # Students table update
        student_cols = {c["name"] for c in inspector.get_columns("students")}
        if "role" not in student_cols:
            connection.execute(
                text("ALTER TABLE students ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'student'")
            )

        # Questions table updates
        if inspector.has_table("questions"):
            question_cols = {c["name"] for c in inspector.get_columns("questions")}
            migrations = {
                "difficulty": "ALTER TABLE questions ADD COLUMN difficulty VARCHAR(20) NOT NULL DEFAULT 'medium'",
                "input_format": "ALTER TABLE questions ADD COLUMN input_format TEXT",
                "output_format": "ALTER TABLE questions ADD COLUMN output_format TEXT",
                "constraints": "ALTER TABLE questions ADD COLUMN constraints TEXT",
                "examples_json": "ALTER TABLE questions ADD COLUMN examples_json TEXT",
                "test_cases_json": "ALTER TABLE questions ADD COLUMN test_cases_json TEXT",
                "time_limit_minutes": "ALTER TABLE questions ADD COLUMN time_limit_minutes INTEGER NOT NULL DEFAULT 15",
                "algorithm_hint": "ALTER TABLE questions ADD COLUMN algorithm_hint TEXT",
                "functions_hint": "ALTER TABLE questions ADD COLUMN functions_hint TEXT",
                "efficient_solution": "ALTER TABLE questions ADD COLUMN efficient_solution TEXT",
            }
            for col, sql in migrations.items():
                if col not in question_cols:
                    connection.execute(text(sql))

        # Attempts table update
        if inspector.has_table("attempts"):
            attempt_cols = {c["name"] for c in inspector.get_columns("attempts")}
            if "is_best_attempt" not in attempt_cols:
                connection.execute(
                    text(
                        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS is_best_attempt "
                        "BOOLEAN NOT NULL DEFAULT false"
                    )
                )
            if "verdict" not in attempt_cols:
                connection.execute(
                    text(
                        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS verdict "
                        "VARCHAR(40) NOT NULL DEFAULT 'Wrong Answer'"
                    )
                )
            if "runtime_ms" not in attempt_cols:
                connection.execute(
                    text(
                        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS runtime_ms "
                        "INTEGER NOT NULL DEFAULT 0"
                    )
                )
            if "total_cases" not in attempt_cols:
                connection.execute(
                    text(
                        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS total_cases "
                        "INTEGER NOT NULL DEFAULT 0"
                    )
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()