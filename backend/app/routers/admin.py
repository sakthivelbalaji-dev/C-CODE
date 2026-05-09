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
from ..syllabus import question_syllabus_sort_key

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
        key=question_syllabus_sort_key,
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
        key=question_syllabus_sort_key,
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

    def draw_line(
        text: str = "",
        *,
        bold: bool = False,
        indent: int = 0,
        monospace: bool = False,
    ) -> None:
        nonlocal y
        safe_full = (text or "").replace("\t", "    ")
        # PDF viewers often collapse regular U+0020 spaces; NBSP keeps pattern columns aligned.
        if monospace:
            safe_full = "\n".join(
                line.replace(" ", "\u00a0") for line in safe_full.split("\n")
            )
        for segment in safe_full.split("\n"):
            _draw_wrapped_segment(segment, bold=bold, indent=indent, monospace=monospace)

    def _draw_wrapped_segment(
        safe: str, *, bold: bool, indent: int, monospace: bool = False
    ) -> None:
        nonlocal y
        margin = left_margin + indent
        font_size = 10 if monospace else 11
        max_chars = max(36, (88 if monospace else 110) - indent // 5)
        body_font = "Courier" if monospace else "Helvetica"
        head_font = "Courier-Bold" if monospace else "Helvetica-Bold"
        while len(safe) > max_chars:
            if y <= top_margin:
                new_page()
            pdf.setFont(head_font if bold else body_font, font_size)
            pdf.drawString(margin, y, safe[:max_chars])
            safe = safe[max_chars:]
            y -= line_height
        if y <= top_margin:
            new_page()
        pdf.setFont(head_font if bold else body_font, font_size)
        pdf.drawString(margin, y, safe)
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
        _si = item.get("sample_input")
        _eo = item.get("expected_output")
        if _si is not None and "\n" in str(_si):
            draw_line("Sample Input:", bold=True)
            draw_line(_si, monospace=True)
        else:
            draw_line(f"Sample Input: {_si if _si is not None else '-'}")
        if _eo is not None and "\n" in str(_eo):
            draw_line("Expected Output (sample):", bold=True)
            draw_line(_eo, monospace=True)
        else:
            draw_line(f"Expected Output: {_eo if _eo is not None else '-'}")
        tc_list = item.get("test_cases") or []
        draw_line(f"Judge test case count: {item.get('test_case_count') or len(tc_list)}")
        if isinstance(tc_list, list) and tc_list:
            draw_line("All test cases (for evaluation / marking):", bold=True)
            for ci, case in enumerate(tc_list, start=1):
                if not isinstance(case, dict):
                    continue
                hidden = bool(case.get("is_hidden"))
                vis = "hidden" if hidden else "public"
                draw_line(f"Case {ci} ({vis})", bold=True, indent=12)
                tin = str(case.get("input", "") or "")
                tout = str(case.get("output", "") or "")
                draw_line("Input:", bold=True, indent=20)
                # Do not .strip() multiline I/O — leading spaces matter for patterns; monospace preserves alignment.
                draw_line("(empty)" if tin == "" else tin, indent=24, monospace=True)
                draw_line("Expected output:", bold=True, indent=20)
                draw_line("(empty)" if tout == "" else tout, indent=24, monospace=True)
        draw_line()

    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="published-questions.pdf"'},
    )
