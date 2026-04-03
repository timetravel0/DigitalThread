export type ID = string;

export type ProjectStatus = "draft" | "active" | "archived";
export type RequirementCategory = "performance" | "safety" | "environment" | "operations" | "compliance";
export type Priority = "low" | "medium" | "high" | "critical";
export type VerificationMethod = "analysis" | "inspection" | "test" | "demonstration";
export type RequirementStatus = "draft" | "approved" | "implemented" | "verified" | "failed" | "retired";
export type ComponentType = "battery" | "motor" | "flight_controller" | "camera" | "sensor" | "frame" | "software_module" | "other";
export type ComponentStatus = "draft" | "selected" | "validated" | "retired";
export type TestMethod = "bench" | "simulation" | "field" | "inspection";
export type TestCaseStatus = "draft" | "ready" | "executed" | "failed" | "passed" | "archived";
export type TestRunResult = "passed" | "failed" | "partial";
export type OperationalOutcome = "success" | "degraded" | "failure";
export type BaselineStatus = "draft" | "released" | "obsolete";
export type BaselineObjectType = "requirement" | "component" | "test_case";
export type LinkObjectType = "requirement" | "component" | "test_case" | "test_run" | "operational_run" | "change_request";
export type RelationType = "satisfies" | "allocated_to" | "verifies" | "tested_by" | "impacts" | "derived_from" | "depends_on" | "uses" | "reports_on" | "validates" | "fails";
export type ChangeRequestStatus = "open" | "analysis" | "approved" | "rejected" | "implemented";
export type Severity = "low" | "medium" | "high" | "critical";
export type ImpactLevel = "low" | "medium" | "high";

export interface Project {
  id: ID;
  code: string;
  name: string;
  description: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface Requirement {
  id: ID;
  project_id: ID;
  key: string;
  title: string;
  description: string;
  category: RequirementCategory;
  priority: Priority;
  verification_method: VerificationMethod;
  status: RequirementStatus;
  version: number;
  parent_requirement_id?: ID | null;
  created_at: string;
  updated_at: string;
}

export interface Component {
  id: ID;
  project_id: ID;
  key: string;
  name: string;
  description: string;
  type: ComponentType;
  part_number?: string | null;
  supplier?: string | null;
  status: ComponentStatus;
  version: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: ID;
  project_id: ID;
  key: string;
  title: string;
  description: string;
  method: TestMethod;
  status: TestCaseStatus;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface TestRun {
  id: ID;
  test_case_id: ID;
  execution_date: string;
  result: TestRunResult;
  summary: string;
  measured_values_json: Record<string, unknown>;
  notes: string;
  executed_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OperationalRun {
  id: ID;
  project_id: ID;
  key: string;
  date: string;
  drone_serial: string;
  location: string;
  duration_minutes: number;
  max_temperature_c?: number | null;
  battery_consumption_pct?: number | null;
  outcome: OperationalOutcome;
  notes: string;
  telemetry_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Baseline {
  id: ID;
  project_id: ID;
  name: string;
  description: string;
  status: BaselineStatus;
  created_at: string;
  updated_at: string;
}

export interface BaselineItem {
  id: ID;
  baseline_id: ID;
  object_type: BaselineObjectType;
  object_id: ID;
  object_version: number;
}

export interface Link {
  id: ID;
  project_id: ID;
  source_type: LinkObjectType;
  source_id: ID;
  target_type: LinkObjectType;
  target_id: ID;
  relation_type: RelationType;
  rationale?: string | null;
  created_at: string;
  source_label?: string | null;
  target_label?: string | null;
}

export interface ChangeRequest {
  id: ID;
  project_id: ID;
  key: string;
  title: string;
  description: string;
  status: ChangeRequestStatus;
  severity: Severity;
  created_at: string;
  updated_at: string;
}

export interface ChangeImpact {
  id: ID;
  change_request_id: ID;
  object_type: string;
  object_id: ID;
  impact_level: ImpactLevel;
  notes: string;
}

export interface DashboardKpis {
  total_requirements: number;
  requirements_with_allocated_components: number;
  requirements_with_verifying_tests: number;
  requirements_at_risk: number;
  failed_tests_last_30_days: number;
  open_change_requests: number;
}

export interface Dashboard {
  project?: Project;
  projects?: Project[];
  kpis: DashboardKpis;
  recent_test_runs: TestRun[];
  recent_changes: ChangeRequest[];
  recent_links: Link[];
}

export interface MatrixColumn {
  object_type: LinkObjectType;
  object_id: ID;
  label: string;
  code?: string | null;
  status?: string | null;
}

export interface MatrixRow {
  requirement: Requirement;
}

export interface MatrixCell {
  row_requirement_id: ID;
  column_object_type: LinkObjectType;
  column_object_id: ID;
  linked: boolean;
  relation_types: RelationType[];
  link_ids: ID[];
}

export interface MatrixResponse {
  project: Project;
  mode: "components" | "tests";
  requirement_filters: { status: string | null; category: string | null };
  rows: MatrixRow[];
  columns: MatrixColumn[];
  cells: MatrixCell[];
}

export interface ObjectSummary {
  object_type: string;
  object_id: ID;
  label: string;
  code?: string | null;
  status?: string | null;
  version?: number | null;
}

export interface ImpactResponse {
  project: Project;
  object: ObjectSummary;
  direct: ObjectSummary[];
  secondary: ObjectSummary[];
  likely_impacted: ObjectSummary[];
  links: Link[];
}
