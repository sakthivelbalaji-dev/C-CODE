"""
CLI for topic-based question seeds (5 per syllabus topic).

Logic lives in app.topic_question_seeds (also used by app.main on empty DB).

  cd backend
  python seed_topic_questions.py              # add missing titles only
  python seed_topic_questions.py --reset      # delete attempts + questions, then seed
"""

from __future__ import annotations

import argparse

from app.database import SessionLocal
from app.models import Question
from app.topic_question_seeds import seed_topic_questions_into_db


def seed(*, reset: bool) -> None:
    db = SessionLocal()
    try:
        added = seed_topic_questions_into_db(db, reset=reset)
        if reset:
            print("Cleared attempts and questions (reset).")
        print(f"Added {added} new question(s).")
        total = db.query(Question).count()
        print(f"Total questions in database: {total}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed 5 questions per syllabus topic.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all attempts and questions, then insert the full topic set.",
    )
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
