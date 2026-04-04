export type ID = string;

export type ProjectStatus = "draft" | "active" | "archived";
export type RequirementCategory = "performance" | "safety" | "environment" | "operations" | "compliance";
export type Priority = "low" | "medium" | "high" | "critical";
export type VerificationMethod = "analysis" | "inspection" | "test" | "demonstration";
export type RequirementStatus = "draft" | "in_review" | "approved" | "rejected" | "implemented" | "verified" | "failed" | "obsolete" | "retired";
export type RequirementVerificationStatus = "not_covered" | "partially_verified" | "at_risk" | "failed" | "verified";
export type BlockKind = "system" | "subsystem" | "assembly" | "component" | "software" | "interface" | "other";
export type AbstractionLevel = "logical" | "physical";
export type BlockStatus = "draft" | "in_review" | "approved" | "rejected" | "obsolete";
export type ComponentType = "battery" | "motor" | "flight_controller" | "camera" | "sensor" | "frame" | "software_module" | "other";
export type ComponentStatus = "draft" | "selected" | "validated" | "retired";
export type TestMethod = "bench" | "simulation" | "field" | "inspection";
export type TestCaseStatus = "draft" | "in_review" | "approved" | "rejected" | "ready" | "executed" | "failed" | "passed" | "archived" | "obsolete";
export type TestRunResult = "passed" | "failed" | "partial";
export type OperationalOutcome = "success" | "degraded" | "failure";
export type VerificationEvidenceType = "test_result" | "simulation" | "telemetry" | "analysis" | "inspection" | "other";
export type SimulationEvidenceResult = "passed" | "failed" | "partial";
export type SimulationEvidenceLinkObjectType = "requirement" | "test_case" | "verification_evidence";
export type OperationalEvidenceSourceType = "sensor" | "system";
export type OperationalEvidenceQualityStatus = "good" | "warning" | "poor" | "unknown";
export type OperationalEvidenceLinkObjectType = "requirement" | "verification_evidence";
export type BaselineStatus = "draft" | "released" | "obsolete";
export type BaselineObjectType = "requirement" | "block" | "component" | "test_case";
export type LinkObjectType = "requirement" | "component" | "test_case" | "test_run" | "operational_run" | "change_request" | "non_conformity";
export type RelationType = "satisfies" | "allocated_to" | "verifies" | "tested_by" | "impacts" | "derived_from" | "depends_on" | "uses" | "reports_on" | "validates" | "fails";
export type SysMLObjectType = "requirement" | "block" | "test_case" | "component" | "operational_run";
export type SysMLRelationType = "satisfy" | "verify" | "deriveReqt" | "refine" | "trace" | "allocate" | "contain";
export type BlockContainmentRelationType = "contains" | "composed_of";
export type ChangeRequestStatus = "open" | "analysis" | "approved" | "rejected" | "implemented" | "closed";
export type NonConformityDisposition = "accept" | "rework" | "reject";
export type Severity = "low" | "medium" | "high" | "critical";
export type ImpactLevel = "low" | "medium" | "high";
export type ConnectorType = "doors" | "sysml" | "plm" | "simulation" | "test" | "telemetry" | "custom";
export type ExternalArtifactType = "requirement" | "sysml_element" | "block" | "cad_part" | "software_module" | "test_case" | "simulation_model" | "test_result" | "telemetry_source" | "document" | "other";
export type ExternalArtifactStatus = "active" | "deprecated" | "obsolete";
export type FederatedInternalObjectType = "project" | "requirement" | "block" | "test_case" | "baseline" | "change_request" | "non_conformity" | "component";
export type ArtifactLinkRelationType = "authoritative_reference" | "derived_from_external" | "synchronized_with" | "validated_against" | "exported_to" | "maps_to";
export type ConfigurationContextType = "working" | "baseline_candidate" | "review_gate" | "released" | "imported";
export type ConfigurationContextStatus = "draft" | "active" | "frozen" | "obsolete";
export type ConfigurationItemKind = "internal_requirement" | "internal_block" | "internal_test_case" | "baseline_item" | "external_artifact_version";

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
  approved_at?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
  review_comment?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Block {
  id: ID;
  project_id: ID;
  key: string;
  name: string;
  description: string;
  block_kind: BlockKind;
  abstraction_level: AbstractionLevel;
  status: BlockStatus;
  version: number;
  owner?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
  review_comment?: string | null;
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

export interface ComponentDetail {
  component: Component;
  links: Link[];
  verification_evidence: VerificationEvidence[];
  impact: ImpactResponse;
  change_impacts: ChangeImpact[];
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
  approved_at?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
  review_comment?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RequirementDetail {
  requirement: Requirement;
  links: Link[];
  artifact_links: ArtifactLink[];
  verification_evidence: VerificationEvidence[];
  simulation_evidence: SimulationEvidence[];
  operational_evidence: OperationalEvidence[];
  verification_evaluation: RequirementVerificationEvaluation;
  history: RevisionSnapshot[];
  impact: ImpactResponse;
}

export interface TestCaseDetail {
  test_case: TestCase;
  links: Link[];
  artifact_links: ArtifactLink[];
  verification_evidence: VerificationEvidence[];
  simulation_evidence: SimulationEvidence[];
  runs: TestRun[];
  history: RevisionSnapshot[];
  impact: ImpactResponse;
}

export interface RequirementVerificationEvaluation {
  status: RequirementVerificationStatus;
  decision_source: string;
  decision_summary: string;
  linked_evidence_count: number;
  fresh_evidence_count: number;
  stale_evidence_count: number;
  linked_operational_run_count: number;
  fresh_operational_run_count: number;
  stale_operational_run_count: number;
  successful_operational_run_count: number;
  degraded_operational_run_count: number;
  failed_operational_run_count: number;
  linked_test_case_count: number;
  passed_test_case_count: number;
  partial_test_case_count: number;
  failed_test_case_count: number;
  reasons: string[];
}

export interface VerificationStatusBreakdown {
  verified: number;
  partially_verified: number;
  at_risk: number;
  failed: number;
  not_covered: number;
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

export interface OperationalRunDetail {
  operational_run: OperationalRun;
  links: Link[];
  impact: ImpactResponse;
}

export interface VerificationEvidence {
  id: ID;
  project_id: ID;
  title: string;
  evidence_type: VerificationEvidenceType;
  summary: string;
  observed_at?: string | null;
  source_name?: string | null;
  source_reference?: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  linked_objects: ObjectSummary[];
}

export interface SimulationEvidence {
  id: ID;
  project_id: ID;
  title: string;
  model_reference: string;
  scenario_name: string;
  input_summary?: string | null;
  inputs_json: Record<string, unknown>;
  expected_behavior: string;
  observed_behavior: string;
  result: SimulationEvidenceResult;
  execution_timestamp: string;
  fmi_contract_id?: ID | null;
  fmi_contract_key?: string | null;
  fmi_contract_name?: string | null;
  fmi_contract_model_identifier?: string | null;
  fmi_contract_model_version?: string | null;
  fmi_contract_contract_version?: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  linked_objects: ObjectSummary[];
}

export interface FMIContract {
  id: ID;
  project_id: ID;
  key: string;
  name: string;
  description: string;
  model_identifier: string;
  model_version?: string | null;
  model_uri?: string | null;
  adapter_profile?: string | null;
  contract_version: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  linked_simulation_evidence_count: number;
}

export interface FMIContractDetail {
  fmi_contract: FMIContract;
  simulation_evidence: SimulationEvidence[];
}

export interface OperationalEvidence {
  id: ID;
  project_id: ID;
  title: string;
  source_name: string;
  source_type: OperationalEvidenceSourceType;
  captured_at: string;
  coverage_window_start: string;
  coverage_window_end: string;
  observations_summary: string;
  aggregated_observations_json: Record<string, unknown>;
  quality_status: OperationalEvidenceQualityStatus;
  derived_metrics_json: Record<string, unknown>;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  linked_objects: ObjectSummary[];
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

export interface BaselineDetail {
  baseline: Baseline;
  bridge_context: BaselineBridgeContext;
  items: BaselineItem[];
  related_configuration_contexts: ConfigurationContext[];
}

export interface BaselineBridgeContext {
  id: ID;
  project_id: ID;
  key: string;
  name: string;
  description: string | null;
  context_type: ConfigurationContextType;
  status: ConfigurationContextStatus;
  created_at: string;
  updated_at: string;
  item_count: number;
  baseline_id: ID;
  baseline_name: string;
}

export interface BaselineContextComparisonResponse {
  baseline: Baseline;
  configuration_context: ConfigurationContext;
  summary: ConfigurationContextComparisonSummary;
  groups: ConfigurationContextComparisonGroup[];
}

export interface BaselineComparisonResponse {
  left_baseline: Baseline;
  right_baseline: Baseline;
  summary: ConfigurationContextComparisonSummary;
  groups: ConfigurationContextComparisonGroup[];
}

export interface BaselineItem {
  id: ID;
  baseline_id: ID;
  object_type: BaselineObjectType;
  object_id: ID;
  object_version: number;
}

export interface RevisionSnapshot {
  id: ID;
  project_id: ID;
  object_type: string;
  object_id: ID;
  version: number;
  snapshot_json: Record<string, unknown>;
  changed_at: string;
  changed_by?: string | null;
  change_summary?: string | null;
}

export interface ReviewQueueItem {
  object_type: string;
  id: ID;
  key: string;
  title: string;
  status: string;
  version: number;
  updated_at: string;
}

export interface ReviewQueueResponse {
  project: Project;
  items: ReviewQueueItem[];
}

export interface BlockTreeNode {
  block: Block;
  children: BlockTreeNode[];
  satisfied_requirements: ObjectSummary[];
  linked_tests: ObjectSummary[];
}

export interface SysMLTreeResponse {
  project: Project;
  roots: BlockTreeNode[];
}

export interface SatisfactionRow {
  block: Block;
  requirements: ObjectSummary[];
}

export interface SysMLSatisfactionResponse {
  project: Project;
  rows: SatisfactionRow[];
}

export interface VerificationRow {
  test_case: TestCase;
  requirements: ObjectSummary[];
}

export interface SysMLVerificationResponse {
  project: Project;
  rows: VerificationRow[];
}

export interface DerivationRow {
  source_requirement: Requirement;
  derived_requirements: ObjectSummary[];
}

export interface SysMLDerivationResponse {
  project: Project;
  rows: DerivationRow[];
}

export interface SysMLMappingSummary {
  requirement_count: number;
  block_count: number;
  logical_block_count: number;
  physical_block_count: number;
  satisfy_relation_count: number;
  verify_relation_count: number;
  derive_relation_count: number;
  contain_relation_count: number;
}

export interface SysMLRequirementMappingRow {
  requirement: Requirement;
  sysml_concept: string;
  satisfy_blocks: ObjectSummary[];
  verify_tests: ObjectSummary[];
  derived_from: ObjectSummary[];
  derived_requirements: ObjectSummary[];
}

export interface SysMLBlockMappingRow {
  block: Block;
  sysml_concept: string;
  abstraction_level: AbstractionLevel;
  profile_label: string;
  contained_blocks: ObjectSummary[];
  contained_in: ObjectSummary[];
  satisfies_requirements: ObjectSummary[];
}

export interface SysMLMappingRelationRow {
  relation_type: string;
  source: ObjectSummary;
  target: ObjectSummary;
  semantics: string;
}

export interface SysMLMappingContractResponse {
  contract_schema: string;
  project: Project;
  generated_at: string;
  summary: SysMLMappingSummary;
  requirements: SysMLRequirementMappingRow[];
  blocks: SysMLBlockMappingRow[];
  relations: SysMLMappingRelationRow[];
}

export interface STEPAP242Summary {
  physical_component_count: number;
  cad_artifact_count: number;
  linked_cad_artifact_count: number;
  identifier_count: number;
}

export interface STEPAP242IdentifierRow {
  kind: string;
  value: string;
  source: string;
}

export interface STEPAP242PartRow {
  component: Component;
  part_number?: string | null;
  version: number;
  status: string;
  supplier?: string | null;
  profile_label: string;
  identifiers: STEPAP242IdentifierRow[];
  linked_cad_artifacts: ExternalArtifact[];
}

export interface STEPAP242RelationRow {
  relation_type: string;
  component: ObjectSummary;
  cad_artifact: ExternalArtifact;
  semantics: string;
}

export interface STEPAP242ContractResponse {
  contract_schema: string;
  project: Project;
  generated_at: string;
  summary: STEPAP242Summary;
  parts: STEPAP242PartRow[];
  cad_artifacts: ExternalArtifact[];
  relations: STEPAP242RelationRow[];
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

export interface SysMLRelation {
  id: ID;
  project_id: ID;
  source_type: SysMLObjectType;
  source_id: ID;
  target_type: SysMLObjectType;
  target_id: ID;
  relation_type: SysMLRelationType;
  rationale?: string | null;
  created_at: string;
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

export interface ApprovalActionLog {
  id: ID;
  project_id: ID;
  object_type: string;
  object_id: ID;
  from_status: string;
  to_status: string;
  action: string;
  actor?: string | null;
  comment?: string | null;
  created_at: string;
}

export interface ChangeRequestDetail {
  change_request: ChangeRequest;
  impacts: ChangeImpact[];
  impact_summary: ObjectSummary[];
  history: ApprovalActionLog[];
}

export interface NonConformity {
  id: ID;
  project_id: ID;
  key: string;
  title: string;
  description: string;
  status: "detected" | "analyzing" | "contained" | "corrected" | "verified" | "closed";
  disposition?: NonConformityDisposition | null;
  review_comment?: string | null;
  severity: Severity;
  created_at: string;
  updated_at: string;
}

export interface NonConformityDetail {
  non_conformity: NonConformity;
  links: Link[];
  related_requirements: ObjectSummary[];
  verification_evidence: VerificationEvidence[];
  impact: ImpactResponse;
  impact_summary: ObjectSummary[];
}

export interface ChangeImpact {
  id: ID;
  change_request_id: ID;
  object_type: string;
  object_id: ID;
  impact_level: ImpactLevel;
  notes: string;
}

export interface ConnectorDefinition {
  id: ID;
  project_id: ID;
  name: string;
  connector_type: ConnectorType;
  base_url?: string | null;
  description?: string | null;
  is_active: boolean;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  artifact_count?: number;
}

export interface ExternalArtifactVersion {
  id: ID;
  external_artifact_id: ID;
  version_label: string;
  revision_label?: string | null;
  checksum_or_signature?: string | null;
  effective_date?: string | null;
  source_timestamp?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface ExternalArtifact {
  id: ID;
  project_id: ID;
  connector_definition_id?: ID | null;
  external_id: string;
  artifact_type: ExternalArtifactType;
  name: string;
  description?: string | null;
  canonical_uri?: string | null;
  native_tool_url?: string | null;
  status: ExternalArtifactStatus;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  connector_name?: string | null;
  connector_type?: ConnectorType | null;
  versions?: ExternalArtifactVersion[];
}

export interface ArtifactLink {
  id: ID;
  project_id: ID;
  internal_object_type: FederatedInternalObjectType;
  internal_object_id: ID;
  external_artifact_id: ID;
  external_artifact_version_id?: ID | null;
  relation_type: ArtifactLinkRelationType;
  rationale?: string | null;
  created_at: string;
  internal_object_label?: string | null;
  external_artifact_name?: string | null;
  external_artifact_version_label?: string | null;
  connector_name?: string | null;
}

export interface ConfigurationContext {
  id: ID;
  project_id: ID;
  key: string;
  name: string;
  description?: string | null;
  context_type: ConfigurationContextType;
  status: ConfigurationContextStatus;
  created_at: string;
  updated_at: string;
  item_count?: number;
}

export interface ConfigurationItemMapping {
  id: ID;
  configuration_context_id: ID;
  item_kind: ConfigurationItemKind;
  internal_object_type?: FederatedInternalObjectType | null;
  internal_object_id?: ID | null;
  internal_object_version?: number | null;
  external_artifact_version_id?: ID | null;
  role_label?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface AuthoritativeRegistrySummary {
  connectors: number;
  external_artifacts: number;
  external_artifact_versions: number;
  artifact_links: number;
  configuration_contexts: number;
  configuration_item_mappings: number;
}

export interface ConnectorDetail {
  connector: ConnectorDefinition;
  artifacts: ExternalArtifact[];
}

export interface ExternalArtifactDetail {
  external_artifact: ExternalArtifact;
  versions: ExternalArtifactVersion[];
  artifact_links: ArtifactLink[];
}

export type ProjectImportFormat = "json" | "csv";

export interface ProjectImportSummary {
  parsed_records: number;
  created_external_artifacts: number;
  created_verification_evidence: number;
}

export interface ProjectImportResponse {
  project: Project;
  summary: ProjectImportSummary;
  external_artifacts: ExternalArtifact[];
  verification_evidence: VerificationEvidence[];
  warnings: string[];
}

export interface ConfigurationContextDetail {
  context: ConfigurationContext;
  items: ConfigurationItemMapping[];
  resolved_view: {
    internal: ConfigurationContextResolvedInternalItem[];
    external: ConfigurationContextResolvedExternalItem[];
  };
  related_baselines: Baseline[];
}

export interface ConfigurationContextResolvedInternalItem {
  mapping_id: ID;
  item_kind: ConfigurationItemKind;
  label: string;
  object_type: string;
  object_id: ID;
  version: number | null;
  role_label?: string | null;
  notes?: string | null;
}

export interface ConfigurationContextResolvedExternalItem {
  mapping_id: ID;
  item_kind: ConfigurationItemKind;
  artifact_name?: string | null;
  artifact_type?: string | null;
  version_label?: string | null;
  revision_label?: string | null;
  connector_name?: string | null;
  role_label?: string | null;
  notes?: string | null;
}

export interface ConfigurationContextComparisonEntry {
  item_kind: ConfigurationItemKind;
  label: string;
  object_type?: string | null;
  object_id?: ID | null;
  object_version?: number | null;
  external_artifact_id?: ID | null;
  external_artifact_version_id?: ID | null;
  version_label?: string | null;
  revision_label?: string | null;
  connector_name?: string | null;
  artifact_name?: string | null;
  artifact_type?: string | null;
  role_label?: string | null;
  notes?: string | null;
}

export interface ConfigurationContextComparisonChange {
  key: string;
  left?: ConfigurationContextComparisonEntry | null;
  right?: ConfigurationContextComparisonEntry | null;
}

export interface ConfigurationContextComparisonGroup {
  item_kind: ConfigurationItemKind;
  added: ConfigurationContextComparisonEntry[];
  removed: ConfigurationContextComparisonEntry[];
  version_changed: ConfigurationContextComparisonChange[];
}

export interface ConfigurationContextComparisonSummary {
  added: number;
  removed: number;
  version_changed: number;
}

export interface ConfigurationContextComparisonResponse {
  left_context: ConfigurationContext;
  right_context: ConfigurationContext;
  summary: ConfigurationContextComparisonSummary;
  groups: ConfigurationContextComparisonGroup[];
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
  verification_status_breakdown: VerificationStatusBreakdown;
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
  related_baselines: Baseline[];
  open_change_requests: ChangeRequest[];
}

export type WorkflowActionPayload = Record<string, unknown> & {
  actor?: string | null;
  comment?: string | null;
  reason?: string | null;
  change_summary?: string | null;
};
