"""
Seed 5 questions per syllabus topic (C Foundation phases 1–5).
Uses templates from app.question_content (same as dump.sql / PDF-aligned syllabus).

Usage (Railway / local Postgres; DATABASE_URL required):
  cd backend
  python seed_topic_questions.py              # add missing titles only
  python seed_topic_questions.py --reset      # delete all attempts + questions, then seed

Requires: pip install -r requirements.txt, DATABASE_URL set.
"""

from __future__ import annotations

import argparse

from app.database import SessionLocal
from app.models import Attempt, Question
from app.question_content import build_problem_content

QUESTIONS_PER_TOPIC = 5

# Template keys must match question_content.py `templates` dict (lowercase).
_TOPIC_SEEDS: list[tuple[str, str, list[str]]] = [
    # Phase 1 — Foundation (9 topics × 5)
    (
        "Phase 1 — Foundation",
        "Introduction to C",
        [
            "print hello world",
            "add two numbers",
            "print name and city",
            "read name and age greeting",
            "student record variables",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Structure of a C Program",
        [
            "print name and city",
            "student record variables",
            "read name and age greeting",
            "add two numbers",
            "swap two numbers",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Keywords and Identifiers",
        [
            "add two numbers",
            "swap two numbers",
            "check even/odd",
            "find largest of 3 numbers",
            "grade calculator",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Variables",
        [
            "swap two numbers",
            "student record variables",
            "read name and age greeting",
            "read float decimal places",
            "read character ascii",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Data Types",
        [
            "read character ascii",
            "read float decimal places",
            "print data type sizes lab",
            "add two numbers",
            "check even/odd",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Constants",
        [
            "print data type sizes lab",
            "read character ascii",
            "add two numbers",
            "print hello world",
            "read float decimal places",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Header Files",
        [
            "print data type sizes lab",
            "print hello world",
            "add two numbers",
            "read character ascii",
            "read float decimal places",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Input and Output (printf, scanf)",
        [
            "print name and city",
            "read float decimal places",
            "read name and age greeting",
            "student record variables",
            "read character ascii",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Compilation process",
        [
            "print simple box border",
            "print hello world",
            "print data type sizes lab",
            "pattern printing",
            "add two numbers",
        ],
    ),
    # Phase 2 — Logic Building & Flow Control (5 × 5)
    (
        "Phase 2 — Logic Building & Flow Control",
        "Arithmetic, Relational, Logical, Assignment",
        [
            "check even/odd",
            "find largest of 3 numbers",
            "simple interest",
            "calculator switch menu",
            "print multiplication table",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Increment and Decrement operators",
        [
            "print multiplication table",
            "read until zero sum",
            "find largest of 3 numbers",
            "break on negative sum",
            "check even/odd",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Conditional Statements (if, else, switch)",
        [
            "grade calculator",
            "day of week switch",
            "check even/odd",
            "prime check",
            "leap year",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Loops (for, while, do-while)",
        [
            "print multiplication table",
            "read until zero sum",
            "prime check",
            "fibonacci series",
            "factorial of number",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Jump statements (break, continue, goto)",
        [
            "break on negative sum",
            "read until zero sum",
            "calculator switch menu",
            "print multiplication table",
            "simple interest",
        ],
    ),
    # Phase 3 — Functions (3 × 5)
    (
        "Phase 3 — Functions",
        "Function declaration, definition, and call",
        [
            "print primes in range",
            "fibonacci series",
            "factorial using function",
            "gcd euclidean",
            "lcm using gcd",
        ],
    ),
    (
        "Phase 3 — Functions",
        "Call by value and call by reference",
        [
            "factorial using function",
            "sum using recursion",
            "swap using pointers",
            "gcd euclidean",
            "armstrong number check",
        ],
    ),
    (
        "Phase 3 — Functions",
        "Using functions for primes, powers, factorial, gcd, lcm",
        [
            "armstrong number check",
            "gcd euclidean",
            "lcm using gcd",
            "factorial of number",
            "floyd triangle pattern",
        ],
    ),
    # Phase 4 — Data Collections (3 × 5)
    (
        "Phase 4 — Data Collections",
        "One-dimensional arrays",
        [
            "array reverse print",
            "max min average array",
            "second largest array",
            "linear search array",
            "count above average",
        ],
    ),
    (
        "Phase 4 — Data Collections",
        "Two-dimensional arrays (matrices)",
        [
            "matrix print 3x3",
            "matrix row column sums",
            "matrix addition",
            "matrix transpose",
            "symmetric matrix check",
        ],
    ),
    (
        "Phase 4 — Data Collections",
        "Strings basics and manipulation",
        [
            "reverse a string",
            "check palindrome",
            "concatenate without strcat",
            "string length manual",
            "count vowels consonants spaces",
        ],
    ),
    # Phase 5 — Problem Practice (2 × 5)
    (
        "Phase 5 — Problem Practice",
        "Mixed array, matrix, string, and number-theory drills",
        [
            "pascal triangle rows",
            "bubble sort array",
            "strong number check",
            "palindrome number",
            "find sum of array",
        ],
    ),
    (
        "Phase 5 — Problem Practice",
        "Patterns, sorts, palindromes, gcd/lcm bundles",
        [
            "bubble sort array",
            "check palindrome",
            "pattern printing",
            "equilateral star pattern",
            "floyd triangle pattern",
        ],
    ),
]


def _display_name(canonical_key: str) -> str:
    return canonical_key.replace("_", " ").strip().title()


def _build_title(module: str, topic: str, q_index: int, display: str) -> str:
    return f"{module} — {topic} — Q{q_index + 1}: {display}"


def _payload(module: str, topic: str, q_index: int, canonical_key: str) -> dict:
    display = _display_name(canonical_key)
    content = build_problem_content(module, topic, display)
    return {
        "title": _build_title(module, topic, q_index, display),
        "description": content["description"],
        "module": module,
        "difficulty": "medium",
        "input_format": content["input_format"],
        "output_format": content["output_format"],
        "constraints": content["constraints"],
        "algorithm_hint": content.get("algorithm_hint"),
        "functions_hint": content.get("functions_hint"),
        "sample_input": content["sample_input"],
        "expected_output": content["expected_output"],
        "examples_json": content["examples_json"],
        "test_cases_json": content["test_cases_json"],
    }


def seed(*, reset: bool) -> None:
    db = SessionLocal()
    try:
        if reset:
            db.query(Attempt).delete()
            db.query(Question).delete()
            db.commit()
            print("Cleared attempts and questions.")

        existing = {q.title for q in db.query(Question).all()}
        added = 0
        for module, topic, keys in _TOPIC_SEEDS:
            if len(keys) != QUESTIONS_PER_TOPIC:
                raise ValueError(f"{module} / {topic}: expected {QUESTIONS_PER_TOPIC} keys, got {len(keys)}")
            for i, key in enumerate(keys):
                payload = _payload(module, topic, i, key)
                if payload["title"] in existing:
                    continue
                db.add(Question(**payload))
                existing.add(payload["title"])
                added += 1
        db.commit()
        print(f"Added {added} new question(s).")

        total = db.query(Question).count()
        print(f"Total questions in database: {total}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed 5 questions per syllabus topic.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all attempts and questions, then insert the full topic set.",
    )
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
