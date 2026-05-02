from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("Attempt", back_populates="student", cascade="all, delete")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    module = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False, default="medium")
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    constraints = Column(Text, nullable=True)
    sample_input = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    examples_json = Column(Text, nullable=True)
    test_cases_json = Column(Text, nullable=True)
    time_limit_minutes = Column(Integer, nullable=False, default=15)
    algorithm_hint = Column(Text, nullable=True)
    functions_hint = Column(Text, nullable=True)
    efficient_solution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("Attempt", back_populates="question", cascade="all, delete")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    submitted_code = Column(Text, nullable=False)
    score = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    is_correct = Column(Boolean, default=False)
    feedback = Column(Text, nullable=True)
    is_best_attempt = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")
