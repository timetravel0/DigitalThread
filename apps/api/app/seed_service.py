from __future__ import annotations

"""Domain facade for demo seeding.

The demo seed is separated from the main service facade so startup and
project bootstrapping logic have an explicit home.
"""

from sqlmodel import Session

from app.services import seed_demo as _seed_demo


def seed_demo(session: Session) -> dict[str, object]:
    return _seed_demo(session)
