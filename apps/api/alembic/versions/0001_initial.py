"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.Enum("draft", "active", "archived", name="projectstatus"), nullable=False),
    )
    op.create_table(
        "requirements",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("category", sa.Enum("performance", "safety", "environment", "operations", "compliance", name="requirementcategory"), nullable=False),
        sa.Column("priority", sa.Enum("low", "medium", "high", "critical", name="priority"), nullable=False),
        sa.Column("verification_method", sa.Enum("analysis", "inspection", "test", "demonstration", name="verificationmethod"), nullable=False),
        sa.Column("status", sa.Enum("draft", "approved", "implemented", "verified", "failed", "retired", name="requirementstatus"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_requirement_id", sa.Uuid(), sa.ForeignKey("requirements.id")),
    )
    op.create_table(
        "components",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("type", sa.Enum("battery", "motor", "flight_controller", "camera", "sensor", "frame", "software_module", "other", name="componenttype"), nullable=False),
        sa.Column("part_number", sa.String(), nullable=True),
        sa.Column("supplier", sa.String(), nullable=True),
        sa.Column("status", sa.Enum("draft", "selected", "validated", "retired", name="componentstatus"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "test_cases",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("method", sa.Enum("bench", "simulation", "field", "inspection", name="testmethod"), nullable=False),
        sa.Column("status", sa.Enum("draft", "ready", "executed", "failed", "passed", "archived", name="testcasestatus"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "test_runs",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("test_case_id", sa.Uuid(), sa.ForeignKey("test_cases.id"), nullable=False),
        sa.Column("execution_date", sa.Date(), nullable=False),
        sa.Column("result", sa.Enum("passed", "failed", "partial", name="testrunresult"), nullable=False),
        sa.Column("summary", sa.String(), nullable=False, server_default=""),
        sa.Column("measured_values_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("executed_by", sa.String(), nullable=True),
    )
    op.create_table(
        "operational_runs",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("drone_serial", sa.String(length=128), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("max_temperature_c", sa.Float(), nullable=True),
        sa.Column("battery_consumption_pct", sa.Float(), nullable=True),
        sa.Column("outcome", sa.Enum("success", "degraded", "failure", name="operationaloutcome"), nullable=False),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
        sa.Column("telemetry_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "baselines",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.Enum("draft", "released", "obsolete", name="baselinestatus"), nullable=False),
    )
    op.create_table(
        "baseline_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("baseline_id", sa.Uuid(), sa.ForeignKey("baselines.id"), nullable=False),
        sa.Column("object_type", sa.Enum("requirement", "component", "test_case", name="baselineobjecttype"), nullable=False),
        sa.Column("object_id", sa.Uuid(), nullable=False),
        sa.Column("object_version", sa.Integer(), nullable=False),
    )
    op.create_table(
        "links",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_type", sa.Enum("requirement", "component", "test_case", "test_run", "operational_run", "change_request", name="linkobjecttype"), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.Enum("requirement", "component", "test_case", "test_run", "operational_run", "change_request", name="linkobjecttype"), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sa.Enum("satisfies", "allocated_to", "verifies", "tested_by", "impacts", "derived_from", "depends_on", "uses", "reports_on", "validates", "fails", name="relationtype"), nullable=False),
        sa.Column("rationale", sa.String(), nullable=True),
    )
    op.create_table(
        "change_requests",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.Enum("open", "analysis", "approved", "rejected", "implemented", name="changerequeststatus"), nullable=False),
        sa.Column("severity", sa.Enum("low", "medium", "high", "critical", name="severity"), nullable=False),
    )
    op.create_table(
        "change_impacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("change_request_id", sa.Uuid(), sa.ForeignKey("change_requests.id"), nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("object_id", sa.Uuid(), nullable=False),
        sa.Column("impact_level", sa.Enum("low", "medium", "high", name="impactlevel"), nullable=False),
        sa.Column("notes", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("change_impacts")
    op.drop_table("change_requests")
    op.drop_table("links")
    op.drop_table("baseline_items")
    op.drop_table("baselines")
    op.drop_table("operational_runs")
    op.drop_table("test_runs")
    op.drop_table("test_cases")
    op.drop_table("components")
    op.drop_table("requirements")
    op.drop_table("projects")

