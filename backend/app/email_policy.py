"""Institutional email policy for student/staff accounts."""

ALLOWED_EMAIL_DOMAIN = "rajalakshmi.edu.in"

# API error text (signup + login)
EMAIL_DOMAIN_REJECT_DETAIL = (
    "Only rajalakshmi.edu.in is allowed. Use an address ending with @rajalakshmi.edu.in."
)


def normalize_institutional_email(email: str) -> str:
    return str(email).strip().lower()


def is_allowed_institutional_email(email: str) -> bool:
    normalized = normalize_institutional_email(email)
    local, sep, domain = normalized.rpartition("@")
    return bool(sep and local and domain == ALLOWED_EMAIL_DOMAIN)
