"""Link Service service layer for the DigitalThread API."""

from app.services_legacy import (
    create_link,
    delete_link,
    list_links,
    create_sysml_relation,
    delete_sysml_relation,
    list_sysml_relations,
)

__all__ = [
    "create_link",
    "delete_link",
    "list_links",
    "create_sysml_relation",
    "delete_sysml_relation",
    "list_sysml_relations",
]
