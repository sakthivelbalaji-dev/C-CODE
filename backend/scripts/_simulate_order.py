import os

os.environ.setdefault("DATABASE_URL", "postgresql://x:x@localhost:5432/x")


def topic_for_key_first(order, key):
    from app.topic_question_seeds import _SYLLABUS_ROWS, QUESTIONS_PER_TOPIC

    rq = list(order) * 2
    qi = 0
    rpull = 0
    first = {}
    for m, t, single in _SYLLABUS_ROWS:
        tk = QUESTIONS_PER_TOPIC - (1 if single else 0)
        if single:
            for _ in range(tk):
                rpull += 1
                k = rq[qi]
                qi += 1
                first.setdefault(k, t)
        else:
            for _ in range(tk):
                rpull += 1
                k = rq[qi]
                qi += 1
                first.setdefault(k, t)
        if single:
            pass
        else:
            pass
    return first.get(key, "?"), first


from app.topic_question_seeds import _PEDAGOGICAL_REPEAT_ORDER as O

L = list(O)
i, j = L.index("pointer to pointer"), L.index("count vowels consonants spaces")
L[i], L[j] = L[j], L[i]
for k in (
    "pointer to pointer",
    "count vowels consonants spaces",
):
    print(k, topic_for_key_first(tuple(L), k)[0])
