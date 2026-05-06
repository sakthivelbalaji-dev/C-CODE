import json
from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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


@router.get("/questions/export/pdf")
def export_questions_pdf(
    admin_id: int | None = Query(None),
    x_admin_id: str | None = Header(None),
    db: Session = Depends(get_db),
):
    _require_admin(db, admin_id=admin_id, x_admin_id=x_admin_id)
    questions = sorted(
        db.query(Question).all(),
        key=lambda row: (module_sort_rank(row.module), title_question_rank(row.title), row.id),
    )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left_margin = 40
    top_margin = 40
    y = height - top_margin
    line_height = 14

    def new_page() -> None:
        nonlocal y
        pdf.showPage()
        pdf.setFont("Helvetica", 11)
        y = height - top_margin

    def draw_line(text: str = "", *, bold: bool = False) -> None:
        nonlocal y
        if y <= top_margin:
            new_page()
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
        safe = (text or "").replace("\t", "    ")
        max_chars = 110
        while len(safe) > max_chars:
            pdf.drawString(left_margin, y, safe[:max_chars])
            safe = safe[max_chars:]
            y -= line_height
            if y <= top_margin:
                new_page()
        pdf.drawString(left_margin, y, safe)
        y -= line_height

    draw_line("C Code Lab - Published Questions", bold=True)
    draw_line(f"Total Questions: {len(questions)}")
    draw_line()

    for idx, row in enumerate(questions, start=1):
        item = _serialize_question_for_admin(row)
        draw_line(f"{idx}. {item['title']}", bold=True)
        draw_line(f"Module: {item.get('module') or '-'}")
        draw_line(f"Difficulty: {item.get('difficulty') or '-'}")
        draw_line(f"Description: {item.get('description') or '-'}")
        draw_line(f"Input Format: {item.get('input_format') or '-'}")
        draw_line(f"Output Format: {item.get('output_format') or '-'}")
        draw_line(f"Constraints: {item.get('constraints') or '-'}")
        draw_line(f"Sample Input: {item.get('sample_input') or '-'}")
        draw_line(f"Expected Output: {item.get('expected_output') or '-'}")
        draw_line(f"Test Case Count: {item.get('test_case_count') or 0}")
        draw_line()

    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="published-questions.pdf"'},
    )
