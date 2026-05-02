"""Authorised staff accounts (restricted login / signup).

Set STAFF_EMAIL_ALLOWLIST in production to a comma-separated list of institutional emails.
Example (override defaults if needed):

    STAFF_EMAIL_ALLOWLIST=hod.aids@rajalakshmi.edu.in,staff.aids@rajalakshmi.edu.in
"""

from __future__ import annotations

import os

from .email_policy import normalize_institutional_email

_STAFF_FALLBACK_EMAILS = (
    "hod.aids@rajalakshmi.edu.in",
    "staff.aids@rajalakshmi.edu.in",
)


def staff_email_allowlist() -> frozenset[str]:
    """Normalised lowercase emails permitted for role=staff (exactly two)."""
    raw = os.getenv("STAFF_EMAIL_ALLOWLIST", "").strip()
    if raw:
        parts = (p.strip() for p in raw.split(","))
        allow = frozenset(normalize_institutional_email(p) for p in parts if p)
        if len(allow) != 2:
            raise ValueError(
                "STAFF_EMAIL_ALLOWLIST must contain exactly two comma-separated institutional emails."
            )
        return allow
    return frozenset(normalize_institutional_email(e) for e in _STAFF_FALLBACK_EMAILS)


def is_authorised_staff_email(email: str) -> bool:
    return normalize_institutional_email(email) in staff_email_allowlist()
