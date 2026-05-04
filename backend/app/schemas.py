from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ALLOWED_ROLES = {"student", "staff"}


class StudentBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "student"


class StudentCreate(StudentBase):
    password: str


class StudentLogin(BaseModel):
    email: EmailStr
    password: str
    role: str = "student"


class StudentOut(StudentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    title: str
    description: str
    module: str
    difficulty: str = "medium"
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    sample_input: Optional[str] = None
    expected_output: Optional[str] = None
    examples: list[dict[str, str]] = Field(default_factory=list)
    test_cases: list[dict[str, str]] = Field(default_factory=list)
    time_limit_minutes: int = 15
    algorithm_hint: Optional[str] = None
    functions_hint: Optional[str] = None
    efficient_solution: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionOut(QuestionBase):
    id: int
    created_at: datetime
    test_case_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CatalogUpdatesOut(BaseModel):
    """New questions added after optional client watermark (staff additions)."""

    new_count: int
    newest_catalog_at: datetime | None = None
    new_titles: list[str] = Field(default_factory=list)


class AttemptCreate(BaseModel):
    """Client always sends full submission text; persistence rules are applied in the router."""

    student_id: int
    question_id: int
    submitted_code: str
    score: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    is_correct: bool = False
    feedback: Optional[str] = None


class AttemptOut(BaseModel):
    id: int
    student_id: int
    question_id: int
    submitted_code: Optional[str] = None
    score: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    is_correct: bool = False
    feedback: Optional[str] = None
    is_best_attempt: bool = False
    created_at: datetime
    should_move_next: bool = False
    next_question_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class AttemptDetailOut(AttemptOut):
    question_title: str | None = None
    student_name: str | None = None
    student_email: str | None = None


class JudgeCaseResult(BaseModel):
    index: int
    input: str
    expected: str
    got: str
    status: str
    passed: bool
    hidden: bool = False


class JudgeRequest(BaseModel):
    code: str
    question_id: int | None = None
    custom_input: str | None = None
    mode: str = "run"
    test_cases: list[dict[str, str]] = Field(default_factory=list)


class JudgeResponse(BaseModel):
    compile_ok: bool
    compile_output: str
    custom_output: str | None = None
    results: list[JudgeCaseResult] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    student_id: int
    student_name: str
    student_email: EmailStr
    total_score: int
    total_correct: int
    total_attempts: int
    average_score: float


class EfficientSolutionOut(BaseModel):
    question_id: int
    efficient_solution: str


class ResumeProgressOut(BaseModel):
    next_question: QuestionOut | None = None
    all_complete: bool = False
    message: Optional[str] = None
