"""
Topic-based question seeds (5 per syllabus topic). Used by:
- `seed_topic_questions.py` CLI
- `app.main` auto-seed when the questions table is empty (Railway / fresh Postgres).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Attempt, Question
from .question_content import build_problem_content

QUESTIONS_PER_TOPIC = 5

_TOPIC_SEEDS: list[tuple[str, str, list[str]]] = [
    (
        "Phase 1 — Foundation",
        "Introduction to C",
        [
            "print hello world",
            "add two numbers",
            "print name and city",
            "read name and age greeting",
            "swap two numbers",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Structure of a C Program",
        [
            "print hello world",
            "print name and city",
            "add two numbers",
            "read name and age greeting",
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
            "print hello world",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Variables",
        [
            "swap two numbers",
            "add two numbers",
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
            "add two numbers",
            "check even/odd",
            "print hello world",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Constants",
        [
            "print hello world",
            "add two numbers",
            "read character ascii",
            "read float decimal places",
            "print name and city",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Header Files",
        [
            "print hello world",
            "add two numbers",
            "read character ascii",
            "read float decimal places",
            "print name and city",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Input and Output (printf, scanf)",
        [
            "print name and city",
            "read float decimal places",
            "read name and age greeting",
            "add two numbers",
            "read character ascii",
        ],
    ),
    (
        "Phase 1 — Foundation",
        "Compilation process",
        [
            "print hello world",
            "add two numbers",
            "print simple box border",
            "print data type sizes lab",
            "pattern printing",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Arithmetic, Relational, Logical, Assignment",
        [
            "check even/odd",
            "find largest of 3 numbers",
            "add two numbers",
            "simple interest",
            "print multiplication table",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Increment and Decrement operators",
        [
            "print multiplication table",
            "check even/odd",
            "find largest of 3 numbers",
            "read until zero sum",
            "add two numbers",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Conditional Statements (if, else, switch)",
        [
            "grade calculator",
            "check even/odd",
            "day of week switch",
            "find largest of 3 numbers",
            "leap year",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Loops (for, while, do-while)",
        [
            "print multiplication table",
            "read until zero sum",
            "factorial of number",
            "check even/odd",
            "find largest of 3 numbers",
        ],
    ),
    (
        "Phase 2 — Logic Building & Flow Control",
        "Jump statements (break, continue, goto)",
        [
            "break on negative sum",
            "read until zero sum",
            "print multiplication table",
            "check even/odd",
            "simple interest",
        ],
    ),
    (
        "Phase 3 — Functions",
        "Function declaration, definition, and call",
        [
            "factorial using function",
            "factorial of number",
            "iseven function loop",
            "fibonacci series",
            "print primes in range",
        ],
    ),
    (
        "Phase 3 — Functions",
        "Call by value and call by reference",
        [
            "factorial using function",
            "factorial of number",
            "gcd euclidean",
            "lcm using gcd",
            "swap using pointers",
        ],
    ),
    (
        "Phase 3 — Functions",
        "Using functions for primes, powers, factorial, gcd, lcm",
        [
            "gcd euclidean",
            "lcm using gcd",
            "factorial using function",
            "fibonacci series",
            "prime check",
        ],
    ),
    (
        "Phase 4 — Data Collections",
        "One-dimensional arrays",
        [
            "find sum of array",
            "largest element",
            "linear search array",
            "array reverse print",
            "max min average array",
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
            "string length manual",
            "reverse a string",
            "count vowels consonants spaces",
            "check palindrome",
            "concatenate without strcat",
        ],
    ),
    (
        "Phase 5 — Problem Practice",
        "Mixed array, matrix, string, and number-theory drills",
        [
            "find sum of array",
            "string length manual",
            "pattern printing",
            "linear search array",
            "check palindrome",
        ],
    ),
    (
        "Phase 5 — Problem Practice",
        "Patterns, sorts, palindromes, gcd/lcm bundles",
        [
            "pattern printing",
            "fibonacci series",
            "check palindrome",
            "reverse a string",
            "factorial of number",
        ],
    ),
]


def parse_topic_from_full_title(module: str, title: str) -> str | None:
    """
    Titles from _build_title look like:
    ``Phase 1 — Foundation — Introduction to C — Q1: Print Hello World``
    """
    sep = " — "
    prefix = module + sep
    if not title.startswith(prefix):
        return None
    rest = title[len(prefix) :]
    marker = " — Q"
    pos = rest.rfind(marker)
    if pos == -1:
        return None
    return rest[:pos].strip()


def topic_order_index(module: str, topic: str) -> int:
    """Row order in _TOPIC_SEEDS matches the C Foundation syllabus topic order within each phase."""
    for i, (m, t, _) in enumerate(_TOPIC_SEEDS):
        if m == module and t == topic:
            return i
    return 9999


def _display_name(canonical_key: str) -> str:
    return canonical_key.replace("_", " ").strip().title()


def _build_title(module: str, topic: str, q_index: int, display: str) -> str:
    return f"{module} — {topic} — Q{q_index + 1}: {display}"


def _difficulty_for_module(module: str) -> str:
    if module.startswith("Phase 1") or module.startswith("Phase 2"):
        return "easy"
    return "medium"


def _payload(module: str, topic: str, q_index: int, canonical_key: str) -> dict:
    display = _display_name(canonical_key)
    content = build_problem_content(module, topic, display)
    return {
        "title": _build_title(module, topic, q_index, display),
        "description": content["description"],
        "module": module,
        "difficulty": _difficulty_for_module(module),
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


def seed_topic_questions_into_db(db: Session, *, reset: bool) -> int:
    """
    Insert topic-seeded questions. Commits on success.
    Returns number of new Question rows inserted.
    """
    if reset:
        db.query(Attempt).delete()
        db.query(Question).delete()
        db.commit()

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
    return added


def maybe_seed_topic_questions_if_empty(db: Session) -> int:
    """
    If there are zero questions, run the full topic seed (no reset, no wipe).
    Returns number inserted (0 if skipped).
    """
    if db.query(Question).count() > 0:
        return 0
    return seed_topic_questions_into_db(db, reset=False)
