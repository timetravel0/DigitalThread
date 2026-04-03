import type {
  Baseline,
  ChangeImpact,
  ChangeRequest,
  Component,
  Dashboard,
  ImpactResponse,
  Link,
  MatrixResponse,
  OperationalRun,
  Project,
  Requirement,
  TestCase,
  TestRun,
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
  requirements: (projectId: string, query?: Record<string, string>) => {
    const qs = new URLSearchParams(query || {}).toString();
    return request<Requirement[]>(`/requirements?project_id=${projectId}${qs ? `&${qs}` : ""}`);
  },
  requirement: (id: string) => request<any>(`/requirements/${id}`),
  components: (projectId: string) => request<Component[]>(`/components?project_id=${projectId}`),
  component: (id: string) => request<any>(`/components/${id}`),
  testCases: (projectId: string) => request<TestCase[]>(`/test-cases?project_id=${projectId}`),
  testCase: (id: string) => request<any>(`/test-cases/${id}`),
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
  changeRequests: (projectId: string) => request<ChangeRequest[]>(`/change-requests?project_id=${projectId}`),
  changeRequest: (id: string) => request<any>(`/change-requests/${id}`),
  changeImpacts: (changeRequestId: string) => request<ChangeImpact[]>(`/change-impacts?change_request_id=${changeRequestId}`),
};
