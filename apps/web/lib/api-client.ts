import type {
  ArtifactLink,
  AuthoritativeRegistrySummary,
  Baseline,
  BaselineDetail,
  BaselineBridgeContext,
  BaselineContextComparisonResponse,
  BaselineComparisonResponse,
  ChangeImpact,
  ChangeRequest,
  ChangeRequestDetail,
  NonConformity,
  NonConformityDetail,
  ConfigurationContext,
  ConfigurationContextComparisonResponse,
  ConfigurationContextDetail,
  ConfigurationItemMapping,
  Component,
  Dashboard,
  Block,
  ConnectorDefinition,
  ConnectorDetail,
  ConnectorType,
  BlockTreeNode,
  ExternalArtifact,
  ExternalArtifactDetail,
  ExternalArtifactType,
  ExternalArtifactVersion,
  ComponentDetail,
  RequirementDetail,
  TestCaseDetail,
  VerificationEvidence,
  ReviewQueueResponse,
  RevisionSnapshot,
  ImpactResponse,
  Link,
  MatrixResponse,
  OperationalRun,
  OperationalRunDetail,
  Project,
  Requirement,
  TestCase,
  TestRun,
  SysMLDerivationResponse,
  SysMLSatisfactionResponse,
  SysMLRelation,
  SysMLTreeResponse,
  SysMLVerificationResponse,
  WorkflowActionPayload,
  FederatedInternalObjectType,
} from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}/api${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  request,
  seedDemo: () => request<{ project_id: string; seeded: boolean }>("/seed/demo", { method: "POST" }),
  dashboard: () => request<Dashboard>("/dashboard"),
  projectDashboard: (id: string) => request<Dashboard>(`/projects/${id}/dashboard`),
  projects: () => request<Project[]>("/projects"),
  project: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (payload: Record<string, unknown>) => request<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  updateProject: (id: string, payload: Record<string, unknown>) => request<Project>(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  exportProjectUrl: (id: string) => `${baseUrl}/api/projects/${id}/export`,
  requirements: (projectId: string, query?: Record<string, string>) => {
    const qs = new URLSearchParams(query || {}).toString();
    return request<Requirement[]>(`/requirements?project_id=${projectId}${qs ? `&${qs}` : ""}`);
  },
  requirement: (id: string) => request<RequirementDetail>(`/requirements/${id}`),
  createRequirement: (payload: Record<string, unknown>) => request<Requirement>(`/requirements`, { method: "POST", body: JSON.stringify(payload) }),
  updateRequirement: (id: string, payload: Record<string, unknown>) => request<Requirement>(`/requirements/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitRequirement: (id: string, payload?: WorkflowActionPayload) => request<Requirement>(`/requirements/${id}/submit-review`, { method: "POST", body: JSON.stringify(payload || {}) }),
  approveRequirement: (id: string, payload?: WorkflowActionPayload) => request<Requirement>(`/requirements/${id}/approve`, { method: "POST", body: JSON.stringify(payload || {}) }),
  rejectRequirement: (id: string, payload?: WorkflowActionPayload) => request<Requirement>(`/requirements/${id}/reject`, { method: "POST", body: JSON.stringify(payload || {}) }),
  sendRequirementToDraft: (id: string, payload?: WorkflowActionPayload) => request<Requirement>(`/requirements/${id}/send-draft`, { method: "POST", body: JSON.stringify(payload || {}) }),
  createRequirementDraftVersion: (id: string, payload?: WorkflowActionPayload) => request<Requirement>(`/requirements/${id}/create-draft-version`, { method: "POST", body: JSON.stringify(payload || {}) }),
  requirementHistory: (id: string) => request<RevisionSnapshot[]>(`/requirements/${id}/history`),
  blocks: (projectId: string) => request<Block[]>(`/blocks?project_id=${projectId}`),
  block: (id: string) => request<any>(`/blocks/${id}`),
  createBlock: (payload: Record<string, unknown>) => request<Block>(`/blocks`, { method: "POST", body: JSON.stringify(payload) }),
  updateBlock: (id: string, payload: Record<string, unknown>) => request<Block>(`/blocks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitBlock: (id: string, payload?: WorkflowActionPayload) => request<Block>(`/blocks/${id}/submit-review`, { method: "POST", body: JSON.stringify(payload || {}) }),
  approveBlock: (id: string, payload?: WorkflowActionPayload) => request<Block>(`/blocks/${id}/approve`, { method: "POST", body: JSON.stringify(payload || {}) }),
  rejectBlock: (id: string, payload?: WorkflowActionPayload) => request<Block>(`/blocks/${id}/reject`, { method: "POST", body: JSON.stringify(payload || {}) }),
  sendBlockToDraft: (id: string, payload?: WorkflowActionPayload) => request<Block>(`/blocks/${id}/send-draft`, { method: "POST", body: JSON.stringify(payload || {}) }),
  createBlockDraftVersion: (id: string, payload?: WorkflowActionPayload) => request<Block>(`/blocks/${id}/create-draft-version`, { method: "POST", body: JSON.stringify(payload || {}) }),
  blockHistory: (id: string) => request<RevisionSnapshot[]>(`/blocks/${id}/history`),
  components: (projectId: string) => request<Component[]>(`/components?project_id=${projectId}`),
  component: (id: string) => request<ComponentDetail>(`/components/${id}`),
  testCases: (projectId: string) => request<TestCase[]>(`/test-cases?project_id=${projectId}`),
  testCase: (id: string) => request<TestCaseDetail>(`/test-cases/${id}`),
  createTestCase: (payload: Record<string, unknown>) => request<TestCase>(`/test-cases`, { method: "POST", body: JSON.stringify(payload) }),
  updateTestCase: (id: string, payload: Record<string, unknown>) => request<TestCase>(`/test-cases/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitTestCase: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/submit-review`, { method: "POST", body: JSON.stringify(payload || {}) }),
  approveTestCase: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/approve`, { method: "POST", body: JSON.stringify(payload || {}) }),
  rejectTestCase: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/reject`, { method: "POST", body: JSON.stringify(payload || {}) }),
  sendTestCaseToDraft: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/send-draft`, { method: "POST", body: JSON.stringify(payload || {}) }),
  createTestCaseDraftVersion: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/create-draft-version`, { method: "POST", body: JSON.stringify(payload || {}) }),
  testCaseHistory: (id: string) => request<RevisionSnapshot[]>(`/test-cases/${id}/history`),
  verificationEvidence: (projectId: string, query?: { internal_object_type?: FederatedInternalObjectType; internal_object_id?: string }) => {
    const qs = new URLSearchParams();
    if (query?.internal_object_type && query.internal_object_id) {
      qs.set("internal_object_type", query.internal_object_type);
      qs.set("internal_object_id", query.internal_object_id);
    }
    return request<VerificationEvidence[]>(`/projects/${projectId}/verification-evidence${qs.toString() ? `?${qs.toString()}` : ""}`);
  },
  createVerificationEvidence: (projectId: string, payload: Record<string, unknown>) => request<VerificationEvidence>(`/projects/${projectId}/verification-evidence`, { method: "POST", body: JSON.stringify(payload) }),
  verificationEvidenceDetail: (id: string) => request<VerificationEvidence>(`/verification-evidence/${id}`),
  testRuns: (projectId: string) => request<TestRun[]>(`/test-runs?project_id=${projectId}`),
  operationalRuns: (projectId: string) => request<OperationalRun[]>(`/operational-runs?project_id=${projectId}`),
  operationalRun: (id: string) => request<OperationalRunDetail>(`/operational-runs/${id}`),
  createOperationalRun: (payload: Record<string, unknown>) => request<OperationalRun>(`/operational-runs`, { method: "POST", body: JSON.stringify(payload) }),
  links: (projectId: string, objectType?: string, objectId?: string) => {
    const qs = new URLSearchParams();
    qs.set("project_id", projectId);
    if (objectType && objectId) {
      qs.set("object_type", objectType);
      qs.set("object_id", objectId);
    }
    return request<Link[]>(`/links?${qs.toString()}`);
  },
  sysmlTree: (projectId: string) => request<SysMLTreeResponse>(`/projects/${projectId}/sysml/block-tree`),
  sysmlSatisfaction: (projectId: string) => request<SysMLSatisfactionResponse>(`/projects/${projectId}/sysml/satisfaction`),
  sysmlVerification: (projectId: string) => request<SysMLVerificationResponse>(`/projects/${projectId}/sysml/verification`),
  sysmlDerivations: (projectId: string) => request<SysMLDerivationResponse>(`/projects/${projectId}/sysml/derivations`),
  sysmlRelations: (projectId: string, query?: { object_type?: string; object_id?: string }) => {
    const qs = new URLSearchParams({ project_id: projectId });
    if (query?.object_type && query.object_id) {
      qs.set("object_type", query.object_type);
      qs.set("object_id", query.object_id);
    }
    return request<SysMLRelation[]>(`/sysml-relations?${qs.toString()}`);
  },
  reviewQueue: (projectId: string) => request<ReviewQueueResponse>(`/review-queue?project_id=${projectId}`),
  matrix: (projectId: string, mode: "components" | "tests", filters?: { status?: string; category?: string }) => {
    const qs = new URLSearchParams({ mode });
    if (filters?.status) qs.set("status", filters.status);
    if (filters?.category) qs.set("category", filters.category);
    return request<MatrixResponse>(`/projects/${projectId}/matrix?${qs.toString()}`);
  },
  impact: (projectId: string, objectType: string, objectId: string) =>
    request<ImpactResponse>(`/projects/${projectId}/impact/${objectType}/${objectId}`),
  baselines: (projectId: string) => request<Baseline[]>(`/baselines?project_id=${projectId}`),
  baseline: (id: string) => request<BaselineDetail>(`/baselines/${id}`),
  baselineBridgeContext: (id: string) => request<BaselineBridgeContext>(`/baselines/${id}/bridge-context`),
  compareBaselines: (baselineId: string, otherBaselineId: string) =>
    request<BaselineComparisonResponse>(`/baselines/${baselineId}/compare-baseline/${otherBaselineId}`),
  compareBaselineToConfigurationContext: (baselineId: string, contextId: string) =>
    request<BaselineContextComparisonResponse>(`/baselines/${baselineId}/compare/${contextId}`),
  createBaseline: (payload: Record<string, unknown>) => request<{ baseline: Baseline; items: unknown[] }>("/baselines", { method: "POST", body: JSON.stringify(payload) }),
  changeRequests: (projectId: string) => request<ChangeRequest[]>(`/change-requests?project_id=${projectId}`),
  changeRequest: (id: string) => request<ChangeRequestDetail>(`/change-requests/${id}`),
  updateChangeRequest: (id: string, payload: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  changeImpacts: (changeRequestId: string) => request<ChangeImpact[]>(`/change-impacts?change_request_id=${changeRequestId}`),
  submitChangeRequestAnalysis: (id: string, payload?: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}/submit-analysis`, { method: "POST", body: JSON.stringify(payload || {}) }),
  approveChangeRequest: (id: string, payload?: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}/approve`, { method: "POST", body: JSON.stringify(payload || {}) }),
  rejectChangeRequest: (id: string, payload?: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}/reject`, { method: "POST", body: JSON.stringify(payload || {}) }),
  implementChangeRequest: (id: string, payload?: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}/implement`, { method: "POST", body: JSON.stringify(payload || {}) }),
  closeChangeRequest: (id: string, payload?: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}/close`, { method: "POST", body: JSON.stringify(payload || {}) }),
  reopenChangeRequest: (id: string, payload?: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}/reopen`, { method: "POST", body: JSON.stringify(payload || {}) }),
  nonConformities: (projectId: string) => request<NonConformity[]>(`/projects/${projectId}/non-conformities`),
  nonConformity: (id: string) => request<NonConformityDetail>(`/non-conformities/${id}`),
  createNonConformity: (payload: Record<string, unknown>) => request<NonConformity>(`/non-conformities`, { method: "POST", body: JSON.stringify(payload) }),
  updateNonConformity: (id: string, payload: Record<string, unknown>) => request<NonConformity>(`/non-conformities/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  authoritativeRegistrySummary: (projectId: string) => request<AuthoritativeRegistrySummary>(`/projects/${projectId}/authoritative-registry-summary`),
  connectors: (projectId: string) => request<ConnectorDefinition[]>(`/projects/${projectId}/connectors`),
  connector: (id: string) => request<ConnectorDetail>(`/connectors/${id}`),
  createConnector: (payload: Record<string, unknown>) => request<ConnectorDefinition>(`/projects/${payload.project_id as string}/connectors`, { method: "POST", body: JSON.stringify(payload) }),
  updateConnector: (id: string, payload: Record<string, unknown>) => request<ConnectorDefinition>(`/connectors/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  externalArtifacts: (projectId: string, query?: { connector_definition_id?: string; connector_type?: ConnectorType; artifact_type?: ExternalArtifactType }) => {
    const qs = new URLSearchParams();
    if (query?.connector_definition_id) qs.set("connector_definition_id", query.connector_definition_id);
    if (query?.connector_type) qs.set("connector_type", query.connector_type);
    if (query?.artifact_type) qs.set("artifact_type", query.artifact_type);
    return request<ExternalArtifact[]>(`/projects/${projectId}/external-artifacts${qs.toString() ? `?${qs.toString()}` : ""}`);
  },
  externalArtifact: (id: string) => request<ExternalArtifactDetail>(`/external-artifacts/${id}`),
  createExternalArtifact: (payload: Record<string, unknown>) => request<ExternalArtifact>(`/projects/${payload.project_id as string}/external-artifacts`, { method: "POST", body: JSON.stringify(payload) }),
  updateExternalArtifact: (id: string, payload: Record<string, unknown>) => request<ExternalArtifact>(`/external-artifacts/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  externalArtifactVersions: (id: string) => request<ExternalArtifactVersion[]>(`/external-artifacts/${id}/versions`),
  createExternalArtifactVersion: (id: string, payload: Record<string, unknown>) => request<ExternalArtifactVersion>(`/external-artifacts/${id}/versions`, { method: "POST", body: JSON.stringify(payload) }),
  artifactLinks: (projectId: string, query?: { internal_object_type?: FederatedInternalObjectType; internal_object_id?: string; external_artifact_id?: string }) => {
    const qs = new URLSearchParams();
    if (query?.internal_object_type && query.internal_object_id) {
      qs.set("internal_object_type", query.internal_object_type);
      qs.set("internal_object_id", query.internal_object_id);
    }
    if (query?.external_artifact_id) qs.set("external_artifact_id", query.external_artifact_id);
    return request<ArtifactLink[]>(`/projects/${projectId}/artifact-links${qs.toString() ? `?${qs.toString()}` : ""}`);
  },
  createArtifactLink: (projectId: string, payload: Record<string, unknown>) => request<ArtifactLink>(`/projects/${projectId}/artifact-links`, { method: "POST", body: JSON.stringify(payload) }),
  deleteArtifactLink: (id: string) => request<void>(`/artifact-links/${id}`, { method: "DELETE" }),
  configurationContexts: (projectId: string) => request<ConfigurationContext[]>(`/projects/${projectId}/configuration-contexts`),
  configurationContext: (id: string) => request<ConfigurationContextDetail>(`/configuration-contexts/${id}`),
  compareConfigurationContexts: (id: string, otherId: string) => request<ConfigurationContextComparisonResponse>(`/configuration-contexts/${id}/compare/${otherId}`),
  createConfigurationContext: (payload: Record<string, unknown>) => request<ConfigurationContext>(`/projects/${payload.project_id as string}/configuration-contexts`, { method: "POST", body: JSON.stringify(payload) }),
  updateConfigurationContext: (id: string, payload: Record<string, unknown>) => request<ConfigurationContext>(`/configuration-contexts/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  configurationContextItems: (id: string) => request<ConfigurationItemMapping[]>(`/configuration-contexts/${id}/items`),
  createConfigurationContextItem: (id: string, payload: Record<string, unknown>) => request<ConfigurationItemMapping>(`/configuration-contexts/${id}/items`, { method: "POST", body: JSON.stringify(payload) }),
  deleteConfigurationContextItem: (id: string) => request<void>(`/configuration-item-mappings/${id}`, { method: "DELETE" }),
};
