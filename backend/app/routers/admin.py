import json
import re
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


def _pdf_question_line_title(full_title: str, catalog_index: int) -> str:
    """
    Replace the Q number in stored titles so the PDF lists Q1…Qn in export order
    (after syllabus sort), independent of database row IDs.
    """
    m = re.match(
        r"^(?P<prefix>.+ — )Q\s*\d+\s*:\s*(?P<rest>.+)$",
        (full_title or "").strip(),
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        return f"{m.group('prefix')}Q{catalog_index}: {m.group('rest')}"
    return full_title or ""


def _canonical_problem_stem(title: str | None) -> str:
    """
    Titles look like ``Phase 1 — … — Introduction to C — Q2: Add Two Numbers``.
    The stem after ``Qn:`` identifies the same drill across syllabus topics.
    """
    if not title:
        return ""
    t = title.strip()
    m = re.search(r"Q\s*\d+\s*:\s*(.+)$", t, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip().casefold()
    return re.sub(r"\s+", " ", t).strip().casefold()


def _dedupe_questions_unique_problem(
    questions: list,
) -> tuple[list, int]:
    """Keep first row per canonical stem (syllabus order). Returns (filtered, removed_count)."""
    seen: set[str] = set()
    out: list = []
    removed = 0
    for q in questions:
        stem = _problem_stem_dedupe_key(q.title, q.id)
        if stem in seen:
            removed += 1
            continue
        seen.add(stem)
        out.append(q)
    return out, removed


def _problem_stem_dedupe_key(title: str | None, question_id: int) -> str:
    """Same canonical stem for duplicate detection; bare/invalid titles never merge."""
    stem = _canonical_problem_stem(title)
    return stem if stem else f"__no_stem_{question_id}"


def _plan_question_dedupe_by_stem(
    questions: list,
) -> tuple[list[int], list[int]]:
    """Return (keep_ids, delete_ids) in syllabus order: first occurrence wins."""
    seen: set[str] = set()
    keep_ids: list[int] = []
    delete_ids: list[int] = []
    for q in questions:
        key = _problem_stem_dedupe_key(q.title, q.id)
        if key in seen:
            delete_ids.append(q.id)
            continue
        seen.add(key)
        keep_ids.append(q.id)
    return keep_ids, delete_ids


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


@router.post("/questions/deduplicate-by-problem-stem")
def deduplicate_questions_by_problem_stem(
    admin_id: int | None = Query(None),
    x_admin_id: str | None = Header(None),
    confirm: bool = Query(
        False,
        description="If true, delete duplicate rows (keeps first in syllabus order per problem name).",
    ),
    db: Session = Depends(get_db),
):
    """
    Removes duplicate question rows that share the same drill name (text after ``Qn:`` in the title),
    matching the PDF duplicate report. The first row in syllabus order is kept; later copies are deleted.
    Student attempts on deleted rows are removed (CASCADE).
    """
    _require_admin(db, admin_id=admin_id, x_admin_id=x_admin_id)

    ordered = sorted(
        db.query(Question).all(),
        key=question_syllabus_sort_key,
    )
    keep_ids, delete_ids = _plan_question_dedupe_by_stem(ordered)

    if not confirm:
        return {
            "dry_run": True,
            "would_delete_count": len(delete_ids),
            "would_delete_ids": delete_ids,
            "would_keep_count": len(keep_ids),
        }

    deleted = 0
    for qid in delete_ids:
        row = db.query(Question).filter(Question.id == qid).first()
        if row:
            db.delete(row)
            deleted += 1
    db.commit()
    return {
        "dry_run": False,
        "deleted_count": deleted,
        "kept_count": len(keep_ids),
        "deleted_ids": delete_ids,
    }


@router.get("/questions/export/pdf")
def export_questions_pdf(
    admin_id: int | None = Query(None),
    x_admin_id: str | None = Header(None),
    unique_problems: bool = Query(
        False,
        description="If true, include each problem type only once (first in syllabus order).",
    ),
    db: Session = Depends(get_db),
):
    _require_admin(db, admin_id=admin_id, x_admin_id=x_admin_id)
    questions = sorted(
        db.query(Question).all(),
        key=question_syllabus_sort_key,
    )
    removed_dupes = 0
    if unique_problems:
        questions, removed_dupes = _dedupe_questions_unique_problem(questions)

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
    draw_line(
        "Catalog numbers Q1, Q2, … in this PDF follow syllabus order in this export. "
        "They are not database row IDs. Use the title’s Q number for LMS imports and references."
    )
    if unique_problems and removed_dupes:
        draw_line(
            f"(Unique problem types — omitted {removed_dupes} duplicate row(s) with same drill as an earlier question.)"
        )
    draw_line()

    for idx, row in enumerate(questions, start=1):
        item = _serialize_question_for_admin(row)
        pdf_title = _pdf_question_line_title(item["title"] or "", idx)
        draw_line(f"{idx}. {pdf_title}", bold=True)
        draw_line(f"Module: {item.get('module') or '-'}")
        draw_line(f"Difficulty: {item.get('difficulty') or '-'}")
        draw_line(f"Description: {item.get('description') or '-'}")
        draw_line(f"Input Format: {item.get('input_format') or '-'}")
        draw_line(f"Output Format: {item.get('output_format') or '-'}")
        draw_line(f"Constraints: {item.get('constraints') or '-'}")
        _si = item.get("sample_input")
        _eo = item.get("expected_output")
        _si_s = str(_si) if _si is not None else ""
        if _si is not None and ("\n" in _si_s or _si_s.startswith(" ")):
            draw_line("Sample Input:", bold=True)
            draw_line(_si_s, monospace=True)
        else:
            draw_line(f"Sample Input: {_si if _si is not None else '-'}")
        _eo_s = str(_eo) if _eo is not None else ""
        if _eo is not None and ("\n" in _eo_s or _eo_s.startswith(" ")):
            draw_line("Expected Output (sample):", bold=True)
            draw_line(_eo_s, monospace=True)
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
        headers={
            "Content-Disposition": 'attachment; filename="published-questions-unique.pdf"'
            if unique_problems
            else 'attachment; filename="published-questions.pdf"'
        },
    )
