import json
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, Student
from ..schemas import QuestionCreate, QuestionOut
from ..syllabus import module_sort_rank, title_question_rank

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(
    db: Session,
    admin_id: int | None = None,
    x_admin_id: str | None = None,
) -> Student:
    raw_id = admin_id if admin_id is not None else (int(x_admin_id) if x_admin_id and x_admin_id.isdigit() else None)
    if raw_id is None:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    user = db.query(Student).filter(Student.id == raw_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if user.role not in {"staff", "admin"}:
        raise HTTPException(status_code=403, detail="Only admin/staff can access admin panel")
    return user


def _serialize_question_for_admin(question: Question) -> dict:
    examples = json.loads(question.examples_json or "[]")
    test_cases = json.loads(question.test_cases_json or "[]")
    if not isinstance(examples, list):
        examples = []
    if not isinstance(test_cases, list):
        test_cases = []
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
        "examples": examples,
        "test_cases": test_cases,
        "test_case_count": len([row for row in test_cases if isinstance(row, dict)]),
        "time_limit_minutes": question.time_limit_minutes,
        "algorithm_hint": question.algorithm_hint,
        "functions_hint": question.functions_hint,
        "efficient_solution": question.efficient_solution,
        "created_at": question.created_at,
    }


@router.get("/questions", response_model=List[QuestionOut])
def list_all_questions_for_admin(
    admin_id: int | None = Query(None),
    x_admin_id: str | None = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(db, admin_id=admin_id, x_admin_id=x_admin_id)
    questions = sorted(
        db.query(Question).all(),
        key=lambda row: (module_sort_rank(row.module), title_question_rank(row.title), row.id),
    )
    return [_serialize_question_for_admin(question) for question in questions]


@router.post("/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question_as_admin(
    payload: QuestionCreate,
    admin_id: int | None = Query(None),
    x_admin_id: str | None = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(db, admin_id=admin_id, x_admin_id=x_admin_id)
    payload_dict = payload.model_dump()
    payload_dict["examples_json"] = json.dumps(payload_dict.pop("examples"))
    payload_dict["test_cases_json"] = json.dumps(payload_dict.pop("test_cases"))
    question = Question(**payload_dict)
    db.add(question)
    db.commit()
    db.refresh(question)
    return _serialize_question_for_admin(question)
