"""Evidence Service service layer for the DigitalThread API."""

from app.services_legacy import (
    create_verification_evidence,
    list_verification_evidence,
    get_verification_evidence_service,
    create_simulation_evidence,
    list_simulation_evidence,
    get_simulation_evidence_service,
    create_operational_evidence,
    list_operational_evidence,
    get_operational_evidence_service,
    create_operational_run,
    update_operational_run,
    list_operational_runs,
    get_operational_run_detail,
)

__all__ = [
    "create_verification_evidence",
    "list_verification_evidence",
    "get_verification_evidence_service",
    "create_simulation_evidence",
    "list_simulation_evidence",
    "get_simulation_evidence_service",
    "create_operational_evidence",
    "list_operational_evidence",
    "get_operational_evidence_service",
    "create_operational_run",
    "update_operational_run",
    "list_operational_runs",
    "get_operational_run_detail",
]
