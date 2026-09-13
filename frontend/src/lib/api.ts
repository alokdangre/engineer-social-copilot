import type {
  ActionRecord,
  ActionPerformedInput,
  ConnectorAccount,
  Goal,
  GoalCreate,
  Hypothesis,
  MemoryCreate,
  MemoryLink,
  MemoryRecord,
  MetricsInput,
  Recommendation,
  ReviewInput,
  SchedulerStatus,
  StrategyVersion,
  WorkflowInvocationResult,
  WorkflowKind,
  WorkflowRun,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

// In-memory token storage (never localStorage, compliant with Secure Web Skills)
let inMemoryToken: string | null = null;

export function setAuthToken(token: string | null): void {
  inMemoryToken = token;
}

export function getAuthToken(): string | null {
  return inMemoryToken;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (inMemoryToken) {
    headers["Authorization"] = `Bearer ${inMemoryToken}`;
  }

  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Non-JSON error
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  login: async (email: string, password: string): Promise<string> => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch(`${API_BASE}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });
    if (!res.ok) {
      throw new Error("Failed to login. Please check your credentials.");
    }
    const data = await res.json();
    setAuthToken(data.access_token);
    return data.access_token;
  },

  register: async (email: string, displayName: string, password: string): Promise<void> => {
    await request("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        display_name: displayName,
        password,
      }),
    });
  },

  // Health
  getHealth: () => request<{ status: string; database: string }>("/health"),

  // Recommendations & Actions
  getRecommendations: (status?: string) =>
    request<Recommendation[]>(status ? `/recommendations?status=${encodeURIComponent(status)}` : "/recommendations"),

  reviewRecommendation: (id: string, review: ReviewInput) =>
    request<Recommendation>(`/recommendations/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: JSON.stringify(review),
    }),

  reportPerformed: (id: string, data: ActionPerformedInput) =>
    request<ActionRecord>(`/recommendations/${encodeURIComponent(id)}/performed`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  addMetrics: (actionId: string, data: MetricsInput) =>
    request<{ metric_snapshot_id: string }>(`/recommendations/actions/${encodeURIComponent(actionId)}/metrics`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getActions: (limit: number = 50) =>
    request<ActionRecord[]>(`/recommendations/actions?limit=${limit}`),

  // Workflows
  startWorkflow: (kind: WorkflowKind, input: Record<string, unknown> = {}, threadId?: string) =>
    request<WorkflowInvocationResult>("/workflows/start", {
      method: "POST",
      body: JSON.stringify({ kind, input, thread_id: threadId }),
    }),

  resumeWorkflow: (threadId: string, value: unknown) =>
    request<WorkflowInvocationResult>(`/workflows/${encodeURIComponent(threadId)}/resume`, {
      method: "POST",
      body: JSON.stringify({ value }),
    }),

  listWorkflows: (kind?: WorkflowKind) =>
    request<WorkflowRun[]>(kind ? `/workflows?kind=${encodeURIComponent(kind)}` : "/workflows"),

  // Memory
  listMemories: (category?: string) =>
    request<MemoryRecord[]>(category ? `/memory?category=${encodeURIComponent(category)}` : "/memory"),

  getMemory: (id: string) => request<MemoryRecord>(`/memory/${encodeURIComponent(id)}`),

  createMemory: (data: MemoryCreate) =>
    request<MemoryRecord>("/memory", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteMemory: (id: string) =>
    request<void>(`/memory/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  createMemoryLink: (fromRecordId: string, toRecordId: string, relation: string) =>
    request<MemoryLink>("/memory/links", {
      method: "POST",
      body: JSON.stringify({
        from_record_id: fromRecordId,
        to_record_id: toRecordId,
        relation,
      }),
    }),

  getRecommendationPacket: (query?: string) =>
    request<MemoryRecord[]>(query ? `/memory/recommendation-packet?query=${encodeURIComponent(query)}` : "/memory/recommendation-packet"),

  // Strategy & Hypotheses
  getCurrentStrategy: async (): Promise<StrategyVersion | null> => {
    try {
      return await request<StrategyVersion>("/strategies/current");
    } catch {
      return null;
    }
  },

  listStrategies: () => request<StrategyVersion[]>("/strategies"),

  listHypotheses: (status?: string) =>
    request<Hypothesis[]>(status ? `/strategies/hypotheses?status=${encodeURIComponent(status)}` : "/strategies/hypotheses"),

  // Goals
  listGoals: () => request<Goal[]>("/goals"),

  createGoal: (data: GoalCreate) =>
    request<Goal>("/goals", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Connectors
  listConnectors: () => request<ConnectorAccount[]>("/connectors"),

  saveConnectorToken: (platform: string, accessToken: string) =>
    request<ConnectorAccount>(`/connectors/${encodeURIComponent(platform)}/token`, {
      method: "POST",
      body: JSON.stringify({ access_token: accessToken }),
    }),

  syncConnector: (platform: string) =>
    request<{ platform: string; fetched: number; created: number; updated: number }>(
      `/connectors/${encodeURIComponent(platform)}/sync`,
      { method: "POST" }
    ),

  getAuthorizeUrl: (platform: string) =>
    request<{ authorization_url: string; state: string }>(`/connectors/${encodeURIComponent(platform)}/authorize`, {
      method: "POST",
    }),

  // Scheduler
  getSchedulerStatus: () => request<SchedulerStatus>("/scheduler/status"),

  runScheduler: () =>
    request<{ status: string; result: Record<string, unknown> }>("/scheduler/run", {
      method: "POST",
    }),
};

