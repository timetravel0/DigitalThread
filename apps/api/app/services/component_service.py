"""Component Service service layer for the DigitalThread API."""

from app.services_legacy import (
    create_component,
    update_component,
    list_components,
)

__all__ = [
    "create_component",
    "update_component",
    "list_components",
]
