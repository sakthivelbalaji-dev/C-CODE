import os

os.environ.setdefault("DATABASE_URL", "postgresql://x:x@localhost:5432/x")

from app.topic_question_seeds import _SYLLABUS_ROWS, QUESTIONS_PER_TOPIC, _PEDAGOGICAL_REPEAT_ORDER

rq = list(_PEDAGOGICAL_REPEAT_ORDER) * 2
qi = 0
rpull = 0
pull_topic: dict[int, tuple[str, str]] = {}

for m, t, single in _SYLLABUS_ROWS:
    if single is not None:
        take = QUESTIONS_PER_TOPIC - 1
    else:
        take = QUESTIONS_PER_TOPIC

    keys_in_row = []
    if single:
        keys_in_row.append((m, t, single, "sing"))
    for _ in range(take):
        k = rq[qi]
        qi += 1
        rpull += 1
        keys_in_row.append((m, t, k, "rep"))
        pull_topic[rpull] = (m, t, k)

for p in sorted(pull_topic):
    _, t, k = pull_topic[p]
    if k in (
        "access array using pointer",
        "bubble sort array",
        "pointer to pointer",
        "fibonacci series",
        "symmetric matrix check",
        "write data to file",
    ):
        print(f"repeat pull#{p}: {t}: {k}")
