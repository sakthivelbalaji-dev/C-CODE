from app.database import SessionLocal
from app.models import Question
from app.question_content import build_problem_content


def _extract_example_from_title(title: str) -> str:
    if ":" in title:
        return title.split(":", 1)[1].strip()
    return title.strip()


def backfill_question_content() -> None:
    db = SessionLocal()
    try:
        questions = db.query(Question).order_by(Question.id.asc()).all()
        updated = 0
        for question in questions:
            example = _extract_example_from_title(question.title)
            content = build_problem_content(question.module, "syllabus topic", example)

            question.description = content["description"]
            question.input_format = content["input_format"]
            question.output_format = content["output_format"]
            question.constraints = content["constraints"]
            question.algorithm_hint = content.get("algorithm_hint")
            question.functions_hint = content.get("functions_hint")
            question.sample_input = content["sample_input"]
            question.expected_output = content["expected_output"]
            question.examples_json = content["examples_json"]
            question.test_cases_json = content["test_cases_json"]
            updated += 1

        db.commit()
        print(f"Updated {updated} question(s) with corrected constraints/examples/test cases.")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_question_content()
