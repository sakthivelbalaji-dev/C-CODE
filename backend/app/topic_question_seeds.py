"""
Topic-based question seeds (5 per syllabus topic). Used by:
- `seed_topic_questions.py` CLI
- `app.main` auto-seed when the questions table is empty (Railway / fresh Postgres).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Attempt, Question
from .question_content import build_problem_content, problem_display_title

QUESTIONS_PER_TOPIC = 5

# --- Duplicate policy (110 questions = 22 topics × 5) ---
# • 18 “foundation” canonical problems appear exactly ONCE in the whole bank.
# • The other 46 templates each appear exactly TWICE (92 slots) — repeats are mid+ drills, not Hello World / Add Two Numbers.
# • Four topics use only “double pool” problems (compilation capstone + heavy practice).

_SINGLETON_KEYS: frozenset = frozenset(
    {
        "print hello world",
        "add two numbers",
        "swap two numbers",
        "read character ascii",
        "read float decimal places",
        "print name and city",
        "read name and age greeting",
        "check even/odd",
        "find largest of 3 numbers",
        "print multiplication table",
        "read until zero sum",
        "print data type sizes lab",
        "print simple box border",
        "student record variables",
        "pattern printing",
        "grade calculator",
        "day of week switch",
        "leap year",
    }
)

# Complement of singletons: each of these templates appears exactly twice (92 slots).
_REPEAT_KEYS: frozenset[str] = frozenset(
    {
        "access array using pointer",
        "armstrong number check",
        "array reverse print",
        "bubble sort array",
        "break on negative sum",
        "calculator switch menu",
        "check palindrome",
        "concatenate without strcat",
        "copy file",
        "count above average",
        "count vowels",
        "count vowels consonants spaces",
        "employee details",
        "equilateral star pattern",
        "factorial of number",
        "factorial using function",
        "fibonacci series",
        "find sum of array",
        "floyd triangle pattern",
        "gcd euclidean",
        "is even function loop",
        "largest element",
        "lcm using gcd",
        "linear search array",
        "matrix addition",
        "matrix print 3x3",
        "matrix row column sums",
        "matrix transpose",
        "max min average array",
        "palindrome number",
        "pascal triangle rows",
        "pointer to pointer",
        "prime check",
        "print primes in range",
        "product inventory record",
        "read file content",
        "reverse a string",
        "second largest array",
        "simple interest",
        "string length manual",
        "strong number check",
        "student record system",
        "sum using recursion",
        "swap using pointers",
        "symmetric matrix check",
        "write data to file",
    }
)

# Pedagogical stream order (two concatenated copies supply 92 repeat pulls).
# First-appearance topics are dictated by syllabus row order × this sequence; swaps below
# deliberately move a few drills out of mismatched headings (e.g. pointer-to-pointer away
# from Variables, bubble sort nearer array/logic phases, pointer traversal with Structure’s
# early array drills—not Introduction/Constants caps).
_PEDAGOGICAL_REPEAT_ORDER: tuple[str, ...] = (
    "simple interest",
    "is even function loop",
    "count vowels",
    "linear search array",
    "array reverse print",
    "access array using pointer",
    "largest element",
    "max min average array",
    "gcd euclidean",
    "lcm using gcd",
    "factorial of number",
    "factorial using function",
    "count vowels consonants spaces",
    "swap using pointers",
    "fibonacci series",
    "sum using recursion",
    "armstrong number check",
    "palindrome number",
    "floyd triangle pattern",
    "pascal triangle rows",
    "equilateral star pattern",
    "prime check",
    "second largest array",
    "find sum of array",
    "matrix print 3x3",
    "matrix addition",
    "matrix transpose",
    "matrix row column sums",
    "concatenate without strcat",
    "string length manual",
    "reverse a string",
    "check palindrome",
    "calculator switch menu",
    "break on negative sum",
    "employee details",
    "product inventory record",
    "read file content",
    "bubble sort array",
    "print primes in range",
    "student record system",
    "strong number check",
    "symmetric matrix check",
    "count above average",
    "pointer to pointer",
    "copy file",
    "write data to file",
)

assert len(_SINGLETON_KEYS) + len(_REPEAT_KEYS) == 64, "must match question_content template count"
assert len(_SINGLETON_KEYS) == 18 and len(_REPEAT_KEYS) == 46
assert len(_PEDAGOGICAL_REPEAT_ORDER) == 46 and set(_PEDAGOGICAL_REPEAT_ORDER) == _REPEAT_KEYS

# (module, topic, singleton key or None if all five come from the repeat pool)
_SYLLABUS_ROWS: tuple[tuple[str, str, str | None], ...] = (
    ("Phase 1 — Foundation", "Introduction to C", "print hello world"),
    ("Phase 1 — Foundation", "Structure of a C Program", "read float decimal places"),
    ("Phase 1 — Foundation", "Keywords and Identifiers", "check even/odd"),
    ("Phase 1 — Foundation", "Variables", "swap two numbers"),
    ("Phase 1 — Foundation", "Data Types", "read character ascii"),
    ("Phase 1 — Foundation", "Constants", "add two numbers"),
    ("Phase 1 — Foundation", "Header Files", "print data type sizes lab"),
    ("Phase 1 — Foundation", "Input and Output (printf, scanf)", "print name and city"),
    ("Phase 1 — Foundation", "Compilation process", None),
    ("Phase 2 — Logic Building & Flow Control", "Arithmetic, Relational, Logical, Assignment", "find largest of 3 numbers"),
    ("Phase 2 — Logic Building & Flow Control", "Increment and Decrement operators", "read until zero sum"),
    ("Phase 2 — Logic Building & Flow Control", "Conditional Statements (if, else, switch)", "grade calculator"),
    ("Phase 2 — Logic Building & Flow Control", "Loops (for, while, do-while)", "print multiplication table"),
    ("Phase 2 — Logic Building & Flow Control", "Jump statements (break, continue, goto)", "leap year"),
    ("Phase 3 — Functions", "Function declaration, definition, and call", "read name and age greeting"),
    ("Phase 3 — Functions", "Call by value and call by reference", "student record variables"),
    ("Phase 3 — Functions", "Using functions for primes, powers, factorial, gcd, lcm", "day of week switch"),
    ("Phase 4 — Data Collections", "One-dimensional arrays", "print simple box border"),
    ("Phase 4 — Data Collections", "Two-dimensional arrays (matrices)", None),
    ("Phase 4 — Data Collections", "Strings basics and manipulation", "pattern printing"),
    ("Phase 5 — Problem Practice", "Mixed array, matrix, string, and number-theory drills", None),
    ("Phase 5 — Problem Practice", "Patterns, sorts, palindromes, gcd/lcm bundles", None),
)


def _build_topic_seeds() -> list[tuple[str, str, list[str]]]:
    repeat_queue: list[str] = list(_PEDAGOGICAL_REPEAT_ORDER) + list(_PEDAGOGICAL_REPEAT_ORDER)
    qi = 0
    out: list[tuple[str, str, list[str]]] = []
    for module, topic, single in _SYLLABUS_ROWS:
        row: list[str] = []
        if single is not None:
            if single not in _SINGLETON_KEYS:
                raise ValueError(f"unknown singleton {single}")
            row.append(single)
            take = QUESTIONS_PER_TOPIC - 1
        else:
            take = QUESTIONS_PER_TOPIC
        for _ in range(take):
            row.append(repeat_queue[qi])
            qi += 1
        out.append((module, topic, row))
    assert qi == len(repeat_queue), "repeat queue mismatch"
    return out


_TOPIC_SEEDS: list[tuple[str, str, list[str]]] = _build_topic_seeds()


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


# Marked easy even when a later phase reuses a simple drill.
_EASY_PROBLEM_KEYS: frozenset = frozenset(
    {
        "print hello world",
        "add two numbers",
        "check even/odd",
        "print name and city",
        "read name and age greeting",
        "swap two numbers",
        "read character ascii",
        "read float decimal places",
        "reverse a string",
        "largest element",
        "find largest of 3 numbers",
        "string length manual",
        "find sum of array",
        "print multiplication table",
        "linear search array",
        "array reverse print",
        "count vowels consonants spaces",
        "grade calculator",
        "day of week switch",
        "print data type sizes lab",
    }
)

# Keep “medium” even in Phase 1–2 when the drill is heavier than basic I/O or conditions.
_MEDIUM_ALWAYS_KEYS: frozenset[str] = frozenset(
    {
        "bubble sort array",
        "armstrong number check",
        "floyd triangle pattern",
        "pascal triangle rows",
        "equilateral star pattern",
        "symmetric matrix check",
        "pointer to pointer",
        "matrix addition",
        "matrix transpose",
        "matrix row column sums",
        "second largest array",
        "strong number check",
    }
)


def _build_title(module: str, topic: str, display: str, *, catalog_q: int) -> str:
    """Catalog numbers Q1…Qn run in syllabus order across all topics (not per-topic Q1–Q5)."""
    return f"{module} — {topic} — Q{catalog_q}: {display}"


def _difficulty_for_problem(module: str, canonical_key: str) -> str:
    k = canonical_key.strip().lower()
    if k in _MEDIUM_ALWAYS_KEYS:
        return "medium"
    if k in _EASY_PROBLEM_KEYS:
        return "easy"
    if module.startswith("Phase 1") or module.startswith("Phase 2"):
        return "easy"
    return "medium"


def _payload(module: str, topic: str, q_index: int, canonical_key: str, *, catalog_q: int) -> dict:
    k = canonical_key.strip().lower()
    display = problem_display_title(k)
    content = build_problem_content(module, topic, k)
    return {
        "title": _build_title(module, topic, display, catalog_q=catalog_q),
        "description": content["description"],
        "module": module,
        "difficulty": _difficulty_for_problem(module, canonical_key),
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
    catalog_q = 1
    for module, topic, keys in _TOPIC_SEEDS:
        if len(keys) != QUESTIONS_PER_TOPIC:
            raise ValueError(f"{module} / {topic}: expected {QUESTIONS_PER_TOPIC} keys, got {len(keys)}")
        for i, key in enumerate(keys):
            payload = _payload(module, topic, i, key, catalog_q=catalog_q)
            catalog_q += 1
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
