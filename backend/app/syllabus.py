import re

from sqlalchemy import case

# Order matches "C Foundation -- Updated.pdf" (Phases 1–5).
# Legacy module names are kept at the end so older seeded DB rows still sort predictably.
SYLLABUS_MODULE_ORDER = [
    "Phase 1 — Foundation",
    "Phase 2 — Logic Building & Flow Control",
    "Phase 3 — Functions",
    "Phase 4 — Data Collections",
    "Phase 5 — Problem Practice",
    "Basics (Foundation)",
    "Control Statements",
    "Loops",
    "Arrays",
    "Strings",
    "Functions",
    "Pointers (Important)",
    "Structures & Unions",
    "File Handling",
]
_SYLLABUS_ORDER_MAP = {name: index for index, name in enumerate(SYLLABUS_MODULE_ORDER, start=1)}


def module_order_case(module_column):
    return case(_SYLLABUS_ORDER_MAP, value=module_column, else_=9999)


def module_sort_rank(module_name: str | None) -> int:
    return _SYLLABUS_ORDER_MAP.get(module_name or "", 9999)


def title_question_rank(title: str | None) -> int:
    """
    Extract `Q<number>` rank from titles like:
    - "Phase 1 — ... — Q1: Print Name And City"
    - "Q5: Student Record Variables"
    Falls back to a large value when no Q-number exists.
    """
    if not title:
        return 9999
    match = re.search(r"\bQ\s*([0-9]+)\b", title, re.IGNORECASE)
    if not match:
        return 9999
    try:
        return int(match.group(1))
    except ValueError:
        return 9999
