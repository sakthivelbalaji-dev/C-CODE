from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..email_policy import (
    EMAIL_DOMAIN_REJECT_DETAIL,
    is_allowed_institutional_email,
    normalize_institutional_email,
)
from ..models import Student
from ..schemas import ALLOWED_ROLES, StudentCreate, StudentLogin, StudentOut
from ..staff_policy import is_authorised_staff_email, staff_email_allowlist

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def signup(payload: StudentCreate, db: Session = Depends(get_db)):
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role must be 'student', 'staff', or 'admin'")

    email_norm = normalize_institutional_email(str(payload.email))

    if payload.role in {"staff", "admin"} and not is_authorised_staff_email(email_norm):
        raise HTTPException(
            status_code=403,
            detail="Staff/admin signup is only allowed for the two authorised staff emails "
            "(hod.aids / staff.aids @rajalakshmi.edu.in by default — set STAFF_EMAIL_ALLOWLIST to override).",
        )

    if not is_allowed_institutional_email(email_norm):
        raise HTTPException(status_code=400, detail=EMAIL_DOMAIN_REJECT_DETAIL)

    existing_student = db.query(Student).filter(Student.email == email_norm).first()
    if existing_student:
        raise HTTPException(status_code=400, detail="Email already exists")

    student = Student(
        name=payload.name,
        email=email_norm,
        password=payload.password,
        role=payload.role,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.post("/login", response_model=StudentOut)
def login(payload: StudentLogin, db: Session = Depends(get_db)):
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role must be 'student', 'staff', or 'admin'")

    email_norm = normalize_institutional_email(str(payload.email))
    if payload.role in {"staff", "admin"} and not is_authorised_staff_email(email_norm):
        try:
            allowed = ", ".join(sorted(staff_email_allowlist()))
        except ValueError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Misconfigured STAFF_EMAIL_ALLOWLIST: {exc}",
            ) from exc
        raise HTTPException(
            status_code=403,
            detail=(
                "Staff login is only for emails on this server allowlist. "
                f"Allowed right now: {allowed}. "
                "Use hod.aids@rajalakshmi.edu.in and staff.aids@rajalakshmi.edu.in, "
                "or unset STAFF_EMAIL_ALLOWLIST so the app defaults apply. Students use the Student tab."
            ),
        )

    if not is_allowed_institutional_email(email_norm):
        raise HTTPException(status_code=400, detail=EMAIL_DOMAIN_REJECT_DETAIL)

    student = (
        db.query(Student)
        .filter(
            Student.email == email_norm,
            Student.password == payload.password,
            Student.role == payload.role,
        )
        .first()
    )
    if not student:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return student


@router.get("/students", response_model=List[StudentOut])
def list_students(role: str | None = "student", db: Session = Depends(get_db)):
    query = db.query(Student)
    if role:
        query = query.filter(Student.role == role)
    return query.order_by(Student.created_at.asc()).all()
