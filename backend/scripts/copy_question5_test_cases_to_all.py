"""
Copy test_cases_json from one source question (default: id=5) to all questions.

Usage:
  cd backend
  python scripts/copy_question5_test_cases_to_all.py
  python scripts/copy_question5_test_cases_to_all.py --source-id 5 --only-empty
"""

from __future__ import annotations

import argparse
import json

from app.database import SessionLocal
from app.models import Question


def copy_test_cases(source_id: int, *, only_empty: bool) -> None:
    db = SessionLocal()
    try:
        source = db.query(Question).filter(Question.id == source_id).first()
        if not source:
            raise SystemExit(f"Source question id={source_id} not found.")
        if not (source.test_cases_json or "").strip():
            raise SystemExit(f"Source question id={source_id} has empty test_cases_json.")

        # Validate source payload once before applying.
        try:
            parsed = json.loads(source.test_cases_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Source question test_cases_json is invalid JSON: {exc}") from exc
        if not isinstance(parsed, list):
            raise SystemExit("Source question test_cases_json must be a JSON array.")

        query = db.query(Question)
        if only_empty:
            rows = query.all()
            targets = [q for q in rows if not (q.test_cases_json or "").strip()]
        else:
            targets = query.all()

        updated = 0
        for question in targets:
            if question.id == source_id:
                continue
            question.test_cases_json = source.test_cases_json
            updated += 1

        db.commit()
        mode = "empty-only" if only_empty else "all"
        print(
            f"Copied test_cases_json from question {source_id} to {updated} question(s) [{mode}] successfully."
        )
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy source question test cases to all questions.")
    parser.add_argument("--source-id", type=int, default=5, help="Source question id (default: 5)")
    parser.add_argument(
        "--only-empty",
        action="store_true",
        help="Only fill questions that currently have empty test_cases_json.",
    )
    args = parser.parse_args()
    copy_test_cases(args.source_id, only_empty=args.only_empty)


if __name__ == "__main__":
    main()
