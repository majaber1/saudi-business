export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

export type ApiError = { detail?: string };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    const message =
      (data as ApiError)?.detail || res.statusText || "Request failed";
    throw new Error(message);
  }
  return data as T;
}

function authedRequest<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  return request<T>(path, {
    ...init,
    headers: { Authorization: "Bearer " + token, ...(init?.headers ?? {}) },
  });
}

export type TokenResponse = { access_token: string; token_type: string };
export type UserProfile = {
  id: number;
  email: string;
  full_name?: string | null;
  role_key: string;
  locale: string;
};

const TOKEN_KEY = "sb_token";

export function saveToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem(TOKEN_KEY, token);
}
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
export function clearToken() {
  if (typeof window !== "undefined") localStorage.removeItem(TOKEN_KEY);
}

export function login(email: string, password: string) {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function register(payload: {
  email: string;
  password: string;
  full_name?: string;
  role_key?: string;
  locale?: string;
}) {
  return request<UserProfile>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function me(token: string) {
  return request<UserProfile>("/auth/me", {
    headers: { Authorization: "Bearer " + token },
  });
}

// --- Projects ---------------------------------------------------------------

export type Project = {
  id: number;
  owner_id: number | null;
  name: string;
  industry: string;
  investment: number;
  stage: string;
  created_at: string;
  workflow_status: string;
  is_archived: boolean;
  persisted: boolean;
};

export function listProjects(token: string) {
  return authedRequest<Project[]>("/projects/", token);
}

// --- Feasibility studies ------------------------------------------------------

export type FinancialResultOut = {
  roi_percent: number | null;
  payback_years: number | null;
  npv: number | null;
  irr_percent: number | null;
  break_even?: number | null;
  verdict: string;
  sensitivity: Array<{
    revenue_change_percent: number;
    npv: number | null;
    irr_percent: number | null;
    verdict: string;
  }>;
};

export type Study = {
  id: number;
  project_id: number;
  title: string;
  study_type: string;
  status: string;
  current_step: number;
  payload: Record<string, unknown>;
  result: FinancialResultOut | null;
};

export function listStudies(token: string, projectId?: number) {
  const qs = projectId ? "?project_id=" + projectId : "";
  return authedRequest<Study[]>("/feasibility/" + qs, token);
}

export function getStudy(token: string, studyId: number) {
  return authedRequest<Study>("/feasibility/" + studyId, token);
}

export function createStudy(
  token: string,
  payload: { title: string; industry: string; investment: number; study_type?: string; project_id?: number },
) {
  return authedRequest<Study>("/feasibility/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function saveStudyStep(token: string, studyId: number, step: number, data: Record<string, unknown>) {
  return authedRequest<Study>("/feasibility/" + studyId + "/step", token, {
    method: "PATCH",
    body: JSON.stringify({ step, data }),
  });
}

export function computeStudy(
  token: string,
  studyId: number,
  payload: { annual_cash_flows: number[]; discount_rate?: number },
) {
  return authedRequest<Study>("/feasibility/" + studyId + "/compute", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function reportDownloadUrl(studyId: number, fmt: "pdf" | "docx", locale: "ar" | "en") {
  return API_BASE + "/reports/study/" + studyId + "?fmt=" + fmt + "&locale=" + locale;
}

// --- Financial & funding engines (public, unauthenticated) ------------------

export type FeasibilityEvalResponse = {
  roi_percent: number | null;
  payback_years: number | null;
  npv: number | null;
  irr_percent: number | null;
  verdict: string;
};

export function evaluateFinancial(payload: {
  investment: number;
  annual_cash_flows: number[];
  discount_rate?: number;
}) {
  return request<FeasibilityEvalResponse>("/financial/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type FundingMatch = {
  program: string;
  name: string;
  score_percent: number;
  reasons: string[];
  missing: string[];
};

export function matchFunding(payload: {
  industry: string;
  stage?: string;
  has_mvp?: boolean;
  has_technical_team?: boolean;
}) {
  return request<FundingMatch[]>("/funding/match", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// --- Investment opportunities (public, unauthenticated) ---------------------

export type Opportunity = {
  id: number;
  title_en: string;
  title_ar: string;
  industry: string;
  summary_en?: string | null;
  summary_ar?: string | null;
  stage: string;
  risk_level: string;
  investment_min: number | null;
  investment_max: number | null;
  expected_return_percent: number | null;
  funding_goal: number | null;
  funding_committed: number;
  source_url?: string | null;
  verification_status: string;
  is_active: boolean;
};

export function listOpportunities(filters?: { industry?: string; risk_level?: string; max_amount?: number }) {
  const params = new URLSearchParams();
  if (filters?.industry) params.set("industry", filters.industry);
  if (filters?.risk_level) params.set("risk_level", filters.risk_level);
  if (filters?.max_amount !== undefined) params.set("max_amount", String(filters.max_amount));
  const qs = params.toString();
  return request<Opportunity[]>("/opportunities/" + (qs ? "?" + qs : ""));
}

// --- Sales lead capture (public, unauthenticated; not a payment endpoint) ---

export type LeadPayload = {
  full_name: string;
  email: string;
  company?: string;
  phone?: string;
  plan?: string;
  intent?: string;
  message?: string;
};

export function submitLead(payload: LeadPayload) {
  return request<{ received: boolean; persisted: boolean }>("/leads/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
