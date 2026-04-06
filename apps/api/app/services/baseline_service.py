"""Baseline Service service layer for the DigitalThread API."""

from app.services_legacy import (
    create_baseline,
    release_baseline,
    obsolete_baseline,
    list_baselines,
    get_baseline_detail,
    list_baseline_history,
    get_baseline_bridge_context,
    compare_baselines,
    _related_baselines_for_configuration_context,
    _released_baselines_for_object,
)

__all__ = [
    "create_baseline",
    "release_baseline",
    "obsolete_baseline",
    "list_baselines",
    "get_baseline_detail",
    "list_baseline_history",
    "get_baseline_bridge_context",
    "compare_baselines",
    "_related_baselines_for_configuration_context",
    "_released_baselines_for_object",
]
