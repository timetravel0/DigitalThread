import type {
  Baseline,
  ChangeImpact,
  ChangeRequest,
  Component,
  Dashboard,
  Block,
  BlockTreeNode,
  ReviewQueueResponse,
  RevisionSnapshot,
  ImpactResponse,
  Link,
  MatrixResponse,
  OperationalRun,
  Project,
  Requirement,
  TestCase,
  TestRun,
  SysMLDerivationResponse,
  SysMLSatisfactionResponse,
  SysMLTreeResponse,
  SysMLVerificationResponse,
  WorkflowActionPayload,
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
  requirement: (id: string) => request<any>(`/requirements/${id}`),
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
  component: (id: string) => request<any>(`/components/${id}`),
  testCases: (projectId: string) => request<TestCase[]>(`/test-cases?project_id=${projectId}`),
  testCase: (id: string) => request<any>(`/test-cases/${id}`),
  createTestCase: (payload: Record<string, unknown>) => request<TestCase>(`/test-cases`, { method: "POST", body: JSON.stringify(payload) }),
  updateTestCase: (id: string, payload: Record<string, unknown>) => request<TestCase>(`/test-cases/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  submitTestCase: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/submit-review`, { method: "POST", body: JSON.stringify(payload || {}) }),
  approveTestCase: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/approve`, { method: "POST", body: JSON.stringify(payload || {}) }),
  rejectTestCase: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/reject`, { method: "POST", body: JSON.stringify(payload || {}) }),
  sendTestCaseToDraft: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/send-draft`, { method: "POST", body: JSON.stringify(payload || {}) }),
  createTestCaseDraftVersion: (id: string, payload?: WorkflowActionPayload) => request<TestCase>(`/test-cases/${id}/create-draft-version`, { method: "POST", body: JSON.stringify(payload || {}) }),
  testCaseHistory: (id: string) => request<RevisionSnapshot[]>(`/test-cases/${id}/history`),
  testRuns: (projectId: string) => request<TestRun[]>(`/test-runs?project_id=${projectId}`),
  operationalRuns: (projectId: string) => request<OperationalRun[]>(`/operational-runs?project_id=${projectId}`),
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
  baseline: (id: string) => request<any>(`/baselines/${id}`),
  createBaseline: (payload: Record<string, unknown>) => request<{ baseline: Baseline; items: unknown[] }>("/baselines", { method: "POST", body: JSON.stringify(payload) }),
  changeRequests: (projectId: string) => request<ChangeRequest[]>(`/change-requests?project_id=${projectId}`),
  changeRequest: (id: string) => request<any>(`/change-requests/${id}`),
  updateChangeRequest: (id: string, payload: Record<string, unknown>) => request<ChangeRequest>(`/change-requests/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  changeImpacts: (changeRequestId: string) => request<ChangeImpact[]>(`/change-impacts?change_request_id=${changeRequestId}`),
};
