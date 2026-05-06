from datetime import datetime
from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Attempt, Question, Student
from ..schemas import (
    CatalogUpdatesOut,
    EfficientSolutionOut,
    QuestionCreate,
    QuestionOut,
    QuestionPublicOut,
    ResumeProgressOut,
)
from ..syllabus import module_order_case

router = APIRouter(prefix="/questions", tags=["questions"])


def _next_unsolved_question(db: Session, student_id: int) -> tuple[Question | None, bool]:
    solved_ids = {
        question_id
        for (question_id,) in db.query(Attempt.question_id)
        .filter(Attempt.student_id == student_id, Attempt.is_correct.is_(True))
        .distinct()
        .all()
    }
    ordered = (
        db.query(Question)
        .order_by(module_order_case(Question.module), Question.id.asc())
        .all()
    )
    for row in ordered:
        if row.id not in solved_ids:
            return row, False
    return None, True


@router.post("/", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    payload_dict = payload.model_dump()
    payload_dict["examples_json"] = json.dumps(payload_dict.pop("examples"))
    payload_dict["test_cases_json"] = json.dumps(payload_dict.pop("test_cases"))

    question = Question(**payload_dict)
    db.add(question)
    db.commit()
    db.refresh(question)
    return _serialize_question(question)


@router.get("/", response_model=List[QuestionOut])
def list_questions(module: str | None = None, difficulty: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Question)
    if module:
        query = query.filter(Question.module == module)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty.lower())
    questions = query.order_by(module_order_case(Question.module), Question.id.asc()).all()
    return [_serialize_question(question) for question in questions]


@router.get("/catalog-updates", response_model=CatalogUpdatesOut)
def catalog_updates(since: datetime | None = Query(None), db: Session = Depends(get_db)):
    """Watermark new rows by ``Question.created_at`` so students see a dashboard notice after staff POST /questions."""
    newest = db.query(func.max(Question.created_at)).scalar()
    if newest is None:
        return CatalogUpdatesOut(new_count=0, newest_catalog_at=None, new_titles=[])

    if since is None:
        return CatalogUpdatesOut(new_count=0, newest_catalog_at=newest, new_titles=[])

    newer_count = int(
        db.query(func.count(Question.id)).filter(Question.created_at > since).scalar() or 0
    )
    sample = (
        db.query(Question)
        .filter(Question.created_at > since)
        .order_by(Question.created_at.desc())
        .limit(10)
        .all()
    )

    return CatalogUpdatesOut(
        new_count=newer_count,
        newest_catalog_at=newest,
        new_titles=[question.title for question in sample],
    )


@router.get("/resume/next", response_model=ResumeProgressOut)
def resume_next_question(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    next_row, all_complete = _next_unsolved_question(db, student_id)
    if next_row:
        return ResumeProgressOut(next_question=_serialize_question(next_row), all_complete=False)
    return ResumeProgressOut(
        next_question=None,
        all_complete=True,
        message="You have completed all questions in order. Great job.",
    )


@router.get("/{question_id}/syllabus-next", response_model=QuestionOut)
def get_following_question_in_syllabus(question_id: int, db: Session = Depends(get_db)):
    """Immediate next Question by module syllabus order (for timed auto-advance)."""
    ordered = (
        db.query(Question)
        .order_by(module_order_case(Question.module), Question.id.asc())
        .all()
    )
    for index, row in enumerate(ordered):
        if row.id == question_id:
            if index + 1 >= len(ordered):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No next question in syllabus order.",
                )
            return _serialize_question(ordered[index + 1])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")


@router.get("/{question_id}", response_model=QuestionPublicOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    serialized = _serialize_question(question)
    return {
        "id": serialized["id"],
        "title": serialized["title"],
        "description": serialized["description"],
        "constraints": serialized["constraints"],
        "sample_input": serialized["sample_input"],
        "expected_output": serialized["expected_output"],
        "examples": serialized["examples"],
    }


@router.get("/{question_id}/efficient-solution", response_model=EfficientSolutionOut)
def get_efficient_solution(question_id: int, student_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if not question.efficient_solution:
        raise HTTPException(status_code=404, detail="Efficient solution not available")

    solved = (
        db.query(Attempt.id)
        .filter(
            Attempt.question_id == question_id,
            Attempt.student_id == student_id,
            Attempt.is_correct.is_(True),
        )
        .first()
    )
    if not solved:
        raise HTTPException(status_code=403, detail="Complete the question first to view efficient solution")

    return EfficientSolutionOut(question_id=question.id, efficient_solution=question.efficient_solution)


def _serialize_question(question: Question) -> dict:
    stored_tests = json.loads(question.test_cases_json or "[]")
    normalized_tests = [c for c in stored_tests if isinstance(c, dict)]
    if not normalized_tests:
        sample_in = (question.sample_input or "").strip()
        sample_out = (question.expected_output or "").strip()
        if sample_in or sample_out:
            normalized_tests.append({"input": sample_in, "output": sample_out, "is_hidden": False})
        else:
            examples = json.loads(question.examples_json or "[]")
            if isinstance(examples, list):
                for row in examples:
                    if not isinstance(row, dict):
                        continue
                    ex_in = str(row.get("input", "")).strip()
                    ex_out = str(row.get("output", "")).strip()
                    if ex_in or ex_out:
                        normalized_tests.append({"input": ex_in, "output": ex_out, "is_hidden": False})

    case_count = len(normalized_tests)
    masked_cases = [{"input": "", "output": ""} for _ in range(case_count)]
    return {
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "module": question.module,
        "difficulty": question.difficulty,
        "input_format": question.input_format,
        "output_format": question.output_format,
        "constraints": question.constraints,
        "sample_input": question.sample_input,
        "expected_output": question.expected_output,
        "examples": json.loads(question.examples_json or "[]"),
        # Frontend compatibility: keep case list shape but never expose real case data.
        "test_cases": masked_cases,
        "test_case_count": case_count,
        "time_limit_minutes": question.time_limit_minutes,
        "algorithm_hint": question.algorithm_hint,
        "functions_hint": question.functions_hint,
        "efficient_solution": question.efficient_solution,
        "created_at": question.created_at,
    }
