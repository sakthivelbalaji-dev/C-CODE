"""Probe repeat-queue pulls ↔ syllabus topics."""
from app.topic_question_seeds import _SYLLABUS_ROWS, QUESTIONS_PER_TOPIC, _PEDAGOGICAL_REPEAT_ORDER

rq = list(_PEDAGOGICAL_REPEAT_ORDER) * 2
qi = 0
rpull = 0

for m, t, single in _SYLLABUS_ROWS:
    if single is not None:
        take = QUESTIONS_PER_TOPIC - 1
        row_header = f"{m} / {t}"
        if "One-dimensional" in t or "Variables" in t or "Structure" in t or "Loops" in t:
            print(row_header, "-- singleton:", single)
        for _ in range(take):
            rpull += 1
            k = rq[qi]
            qi += 1
            if (
                "One-dimensional" in t
                or ("Loops" in t)
                or ("Structure" in t)
                or ("Call by value" in t)
            ):
                print("  repeat pull#", rpull, "order_idx", rpull - 1 if rpull <= 92 else "?", "key", k)
        continue
    take = QUESTIONS_PER_TOPIC
    row_header = f"{m} / {t}"
    if "One-dimensional" in t:
        print(row_header, "-- all repeat")
    for _ in range(take):
        rpull += 1
        k = rq[qi]
        qi += 1
        if "One-dimensional" in t:
            print("  repeat pull#", rpull, "ORDER slot", (rpull - 1) % 46 if rpull <= 92 else "?", k)
