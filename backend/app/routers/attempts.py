from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Integer, desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Attempt, Question, Student
from ..schemas import AttemptCreate, AttemptDetailOut, AttemptOut, LeaderboardEntry
from ..syllabus import question_syllabus_sort_key

router = APIRouter(prefix="/attempts", tags=["attempts"])

MAX_ATTEMPTS_PER_QUESTION = 20
MAX_FEEDBACK_CHARS = 500
INCORRECT_CODE_PLACEHOLDER = "[incorrect submission — code not stored]"


def _truncate_feedback(value: str | None, max_len: int = MAX_FEEDBACK_CHARS) -> str | None:
    if value is None:
        return None
    if len(value) <= max_len:
        return value
    return value[:max_len]


def _prune_excess_attempts(db: Session, student_id: int, question_id: int, *, keep: int) -> None:
    """Keep the newest `keep` rows per (student_id, question_id); delete the rest."""
    surplus_ids = [
        row[0]
        for row in (
            db.query(Attempt.id)
            .filter(Attempt.student_id == student_id, Attempt.question_id == question_id)
            .order_by(desc(Attempt.created_at), desc(Attempt.id))
            .offset(keep)
            .all()
        )
    ]
    if surplus_ids:
        db.query(Attempt).filter(Attempt.id.in_(surplus_ids)).delete(synchronize_session=False)


def _recompute_best_attempt_for_question(db: Session, student_id: int, question_id: int) -> None:
    """Exactly one attempt per (student_id, question_id) has is_best_attempt True: highest score, then newest."""
    rows = (
        db.query(Attempt)
        .filter(Attempt.student_id == student_id, Attempt.question_id == question_id)
        .order_by(desc(Attempt.score), desc(Attempt.created_at), desc(Attempt.id))
        .all()
    )
    if not rows:
        return
    best_id = rows[0].id
    for row in rows:
        row.is_best_attempt = row.id == best_id


@router.post("/", response_model=AttemptOut, status_code=status.HTTP_201_CREATED)
def create_attempt(payload: AttemptCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    verdict_norm = (payload.verdict or "").strip().lower()
    derived_is_correct = bool(
        verdict_norm == "accepted"
        or (payload.total_cases > 0 and payload.passed_cases >= payload.total_cases)
        or payload.is_correct
    )

    attempt = Attempt(
        student_id=payload.student_id,
        question_id=payload.question_id,
        submitted_code=(
            payload.submitted_code if derived_is_correct else INCORRECT_CODE_PLACEHOLDER
        ),
        score=payload.score,
        passed_cases=payload.passed_cases,
        failed_cases=payload.failed_cases,
        is_correct=derived_is_correct,
        feedback=_truncate_feedback(payload.feedback),
        is_best_attempt=False,
        verdict=payload.verdict or ("Accepted" if derived_is_correct else "Wrong Answer"),
        runtime_ms=max(0, payload.runtime_ms),
        total_cases=max(0, payload.total_cases),
    )
    db.add(attempt)
    db.flush()
    _prune_excess_attempts(db, payload.student_id, payload.question_id, keep=MAX_ATTEMPTS_PER_QUESTION)
    _recompute_best_attempt_for_question(db, payload.student_id, payload.question_id)
    db.commit()
    db.refresh(attempt)

    next_question_id = None
    should_move_next = False
    if attempt.is_correct:
        solved_question_ids = {
            question_id
            for (question_id,) in (
                db.query(Attempt.question_id)
                .filter(
                    Attempt.student_id == attempt.student_id,
                    Attempt.is_correct.is_(True),
                )
                .distinct()
                .all()
            )
        }
        ordered_questions = sorted(
            db.query(Question).all(),
            key=question_syllabus_sort_key,
        )
        ordered_question_ids = [row.id for row in ordered_questions]
        if ordered_question_ids:
            try:
                current_index = ordered_question_ids.index(attempt.question_id)
            except ValueError:
                current_index = -1

            total_questions = len(ordered_question_ids)
            for step in range(1, total_questions + 1):
                candidate_id = ordered_question_ids[(current_index + step) % total_questions]
                if candidate_id not in solved_question_ids:
                    next_question_id = candidate_id
                    should_move_next = True
                    break

    return AttemptOut(
        id=attempt.id,
        student_id=attempt.student_id,
        question_id=attempt.question_id,
        submitted_code=payload.submitted_code,
        score=attempt.score,
        passed_cases=attempt.passed_cases,
        failed_cases=attempt.failed_cases,
        is_correct=attempt.is_correct,
        feedback=attempt.feedback,
        is_best_attempt=attempt.is_best_attempt,
        verdict=attempt.verdict,
        runtime_ms=attempt.runtime_ms,
        total_cases=attempt.total_cases,
        created_at=attempt.created_at,
        should_move_next=should_move_next,
        next_question_id=next_question_id,
    )


@router.get("/", response_model=List[AttemptDetailOut])
def list_attempts(student_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Attempt)
    if student_id is not None:
        query = query.filter(Attempt.student_id == student_id)
    attempts = query.order_by(Attempt.created_at.desc()).all()

    question_ids = {attempt.question_id for attempt in attempts}
    student_ids = {attempt.student_id for attempt in attempts}

    question_map = {
        question.id: question.title
        for question in db.query(Question).filter(Question.id.in_(question_ids)).all()
    }
    student_map = {
        student.id: {"name": student.name, "email": student.email}
        for student in db.query(Student).filter(Student.id.in_(student_ids)).all()
    }

    result: list[AttemptDetailOut] = []
    for attempt in attempts:
        student_info = student_map.get(attempt.student_id, {})
        result.append(
            AttemptDetailOut(
                id=attempt.id,
                student_id=attempt.student_id,
                question_id=attempt.question_id,
                submitted_code=attempt.submitted_code,
                score=attempt.score,
                passed_cases=attempt.passed_cases,
                failed_cases=attempt.failed_cases,
                is_correct=attempt.is_correct,
                feedback=attempt.feedback,
                is_best_attempt=attempt.is_best_attempt,
                verdict=attempt.verdict,
                runtime_ms=attempt.runtime_ms,
                total_cases=attempt.total_cases,
                created_at=attempt.created_at,
                question_title=question_map.get(attempt.question_id),
                student_name=student_info.get("name"),
                student_email=student_info.get("email"),
            )
        )
    return result


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    safe_limit = max(1, min(limit, 100))
    rows = (
        db.query(
            Student.id.label("student_id"),
            Student.name.label("student_name"),
            Student.email.label("student_email"),
            func.coalesce(func.sum(Attempt.score), 0).label("total_score"),
            func.coalesce(func.sum(func.cast(Attempt.is_correct, Integer)), 0).label("total_correct"),
            func.count(Attempt.id).label("total_attempts"),
            func.coalesce(func.avg(Attempt.score), 0.0).label("average_score"),
        )
        .join(Attempt, Attempt.student_id == Student.id)
        .group_by(Student.id, Student.name, Student.email)
        .order_by(func.sum(Attempt.score).desc(), func.sum(func.cast(Attempt.is_correct, Integer)).desc())
        .limit(safe_limit)
        .all()
    )

    return [
        LeaderboardEntry(
            student_id=row.student_id,
            student_name=row.student_name,
            student_email=row.student_email,
            total_score=int(row.total_score or 0),
            total_correct=int(row.total_correct or 0),
            total_attempts=int(row.total_attempts or 0),
            average_score=float(row.average_score or 0.0),
        )
        for row in rows
    ]
