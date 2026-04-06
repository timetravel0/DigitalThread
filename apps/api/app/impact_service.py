
"""Domain facade for impact, dashboard, and detail views.

This module keeps impact-oriented entry points separate from the main
monolithic service facade while preserving the existing behavior.
"""

from uuid import UUID

from sqlmodel import Session

from app.services_legacy import (
    build_impact as _build_impact,
    build_matrix as _build_matrix,
    get_change_request_detail as _get_change_request_detail,
    get_component_detail as _get_component_detail,
    get_global_dashboard as _get_global_dashboard,
    get_project_dashboard as _get_project_dashboard,
    get_requirement_detail as _get_requirement_detail,
    get_test_case_detail as _get_test_case_detail,
)


def get_global_dashboard(session: Session):
    return _get_global_dashboard(session)


def get_project_dashboard(session: Session, project_id: UUID):
    return _get_project_dashboard(session, project_id)


def build_matrix(session: Session, project_id: UUID, mode: str, status=None, category=None):
    return _build_matrix(session, project_id, mode, status=status, category=category)


def build_impact(session: Session, project_id: UUID, object_type: str, object_id: UUID):
    return _build_impact(session, project_id, object_type, object_id)


def get_requirement_detail(session: Session, obj_id: UUID):
    return _get_requirement_detail(session, obj_id)


def get_component_detail(session: Session, obj_id: UUID):
    return _get_component_detail(session, obj_id)


def get_test_case_detail(session: Session, obj_id: UUID):
    return _get_test_case_detail(session, obj_id)


def get_change_request_detail(session: Session, obj_id: UUID):
    return _get_change_request_detail(session, obj_id)
