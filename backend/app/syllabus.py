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


def module_order_case(module_column):
    order_map = {name: index for index, name in enumerate(SYLLABUS_MODULE_ORDER, start=1)}
    return case(order_map, value=module_column, else_=9999)
