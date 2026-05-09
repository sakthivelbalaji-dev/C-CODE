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


def question_syllabus_sort_key(row: object) -> tuple:
    """
    Phase order → topic order (C Foundation PDF / _TOPIC_SEEDS) → Q number in title → id.
    Without topic order, every ``Q1`` collides across topics and listing order became arbitrary.
    """
    from .topic_question_seeds import parse_topic_from_full_title, topic_order_index

    module = getattr(row, "module", None) or ""
    title = getattr(row, "title", None) or ""
    qid = getattr(row, "id", 0) or 0
    topic = parse_topic_from_full_title(module, title)
    topic_rank = topic_order_index(module, topic) if topic is not None else 9999
    return (module_sort_rank(module), topic_rank, title_question_rank(title), qid)


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
