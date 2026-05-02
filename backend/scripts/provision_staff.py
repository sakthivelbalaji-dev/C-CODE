#!/usr/bin/env python3
"""
Create the two authorised staff Student rows if they are missing.

Run from the backend folder so `app` is importable:

    cd backend
    python scripts/provision_staff.py --password "YOUR_STRONG_PASSWORD"

Requires STAFF_EMAIL_ALLOWLIST (exactly two emails) or the defaults in app/staff_policy.py.

Optional: rotate passwords for existing staff rows:

    python scripts/provision_staff.py --password "NEW" --update-existing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.database import SessionLocal  # noqa: E402
from app.models import Student  # noqa: E402
from app.staff_policy import staff_email_allowlist  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision the two fixed staff login accounts.")
    parser.add_argument("--password", required=True, help="Initial password for new (or updated) staff rows.")
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Overwrite password for rows that already exist with role=staff.",
    )
    args = parser.parse_args()

    try:
        allow = sorted(staff_email_allowlist())
    except ValueError as exc:
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    db = SessionLocal()
    try:
        for idx, email in enumerate(allow, start=1):
            row = db.query(Student).filter(Student.email == email).first()
            if row is None:
                label = "Staff Admin" if idx == 1 else "Staff Moderator"
                db.add(
                    Student(
                        name=label,
                        email=email,
                        password=args.password,
                        role="staff",
                    )
                )
                print(f"Created staff user: {email}")
                continue

            if row.role != "staff":
                print(
                    f"Refusing — email exists as student: {email}. Choose different staff allowlist emails.",
                    file=sys.stderr,
                )
                raise SystemExit(2)

            if args.update_existing:
                row.password = args.password
                print(f"Updated password for existing staff user: {email}")
            else:
                print(f"Skipped (already exists): {email}")

        db.commit()
    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    main()
