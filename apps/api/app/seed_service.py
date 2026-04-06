
"""Domain facade for demo seeding.

The demo seed is separated from the main service facade so startup and
project bootstrapping logic have an explicit home.
"""

from sqlmodel import Session

from app.services_legacy import seed_demo as _seed_demo
from app.services_legacy import seed_manufacturing_demo as _seed_manufacturing_demo
from app.services_legacy import seed_personal_demo as _seed_personal_demo


def seed_demo(session: Session) -> dict[str, object]:
    return _seed_demo(session)


def seed_manufacturing_demo(session: Session) -> dict[str, object]:
    return _seed_manufacturing_demo(session)


def seed_personal_demo(session: Session) -> dict[str, object]:
    return _seed_personal_demo(session)
