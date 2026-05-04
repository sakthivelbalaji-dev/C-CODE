"""Shared rules for optional ``is_hidden`` on JSON-stored question test cases."""


def is_hidden_test_case(case: dict) -> bool:
    v = case.get("is_hidden")
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    if isinstance(v, (int, float)):
        return bool(v)
    return False
