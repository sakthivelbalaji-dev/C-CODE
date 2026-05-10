import os

os.environ.setdefault("DATABASE_URL", "postgresql://x:x@localhost:5432/x")
from app.topic_question_seeds import _SYLLABUS_ROWS, QUESTIONS_PER_TOPIC, _PEDAGOGICAL_REPEAT_ORDER

rq = list(_PEDAGOGICAL_REPEAT_ORDER) * 2
qi = 0
rpull = 0
order_slot_to_topic: dict[int, str] = {}

for m, t, single in _SYLLABUS_ROWS:
    take = QUESTIONS_PER_TOPIC - (1 if single else 0)
    for _ in range(take):
        k = rq[qi]
        order_slot = rpull
        order_slot_to_topic[order_slot] = t
        rpull += 1
        qi += 1

rq2 = list(_PEDAGOGICAL_REPEAT_ORDER)
qi = 0
slots: list[tuple[int, str, str]] = []
for m, t, single in _SYLLABUS_ROWS:
    take = QUESTIONS_PER_TOPIC - (1 if single else 0)
    for _ in range(take):
        k = rq2[qi]
        slots.append((qi, t, k))
        qi += 1
for qi, t, k in slots[35:]:
    print(f"ORDER[{qi}] -> {t}: {k}")
