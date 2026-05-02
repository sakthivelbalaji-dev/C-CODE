from app.database import SessionLocal
from app.models import Question

DIFFICULTY_CYCLE = ["easy", "medium", "tough"]


def backfill_difficulty() -> None:
    db = SessionLocal()
    try:
        modules = db.query(Question.module).distinct().all()
        for (module_name,) in modules:
            questions = (
                db.query(Question)
                .filter(Question.module == module_name)
                .order_by(Question.id.asc())
                .all()
            )
            for index, question in enumerate(questions):
                # Stagger each 3-question block so repeated templates are spread
                # across easy/medium/tough instead of always landing in one bucket.
                block_offset = index // len(DIFFICULTY_CYCLE)
                question.difficulty = DIFFICULTY_CYCLE[(index + block_offset) % len(DIFFICULTY_CYCLE)]
            print(f"{module_name}: updated {len(questions)} questions")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    backfill_difficulty()
