// Defaults to a same-origin path proxied to the backend by next.config.mjs's
// rewrites() -- this avoids needing any CORS configuration on the backend
// (see backend/app/core/config.py: production denies cross-origin requests
// by default unless CORS_ORIGINS is explicitly set, which this deployment
// does not require). Override with an absolute URL via
// NEXT_PUBLIC_API_BASE_URL if you point this frontend at a different backend.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "/api/backend";

export type ApiError = {
  detail?: string | Array<{ msg?: string; loc?: Array<string | number> }>;
  message?: string;
};

function apiErrorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const error = data as ApiError;
  if (typeof error.detail === "string") return error.detail;
  if (Array.isArray(error.detail)) {
    const messages = error.detail
      .map((item) => {
        if (!item || typeof item !== "object") return null;
        const field = Array.isArray(item.loc) ? item.loc.at(-1) : null;
        return item.msg ? `${field ? `${String(field)}: ` : ""}${item.msg}` : null;
      })
      .filter((item): item is string => Boolean(item));
    if (messages.length) return messages.join("، ");
  }
  if (typeof error.message === "string") return error.message;
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + path, {
    ...init,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    const message = apiErrorMessage(data, res.statusText || "Request failed");
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
  email_verified: boolean;
};

const TOKEN_KEY = "sb_token";

export function saveToken(token: string) {
  if (typeof window !== "undefined") {
    // Store only a non-secret UI hint. The real credential is an HTTP-only
    // SameSite cookie issued by /api/session/login and cannot be read by JS.
    localStorage.setItem(TOKEN_KEY, token === "session" ? "session" : token);
    window.dispatchEvent(new Event("sb-auth-change"));
  }
}
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    void fetch("/api/session/logout", { method: "POST", credentials: "same-origin" });
    window.dispatchEvent(new Event("sb-auth-change"));
  }
}

export function login(email: string, password: string) {
  return fetch("/api/session/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ email, password }),
  }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(apiErrorMessage(data, res.statusText || "Sign in failed"));
    return data as TokenResponse;
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

export function listProjects(token: string, includeArchived = false) {
  return authedRequest<Project[]>("/projects/" + (includeArchived ? "?include_archived=true" : ""), token);
}

export function getProject(token: string, projectId: number) {
  return authedRequest<Project>(`/projects/${projectId}`, token);
}

export function createProject(token: string, payload: { name: string; industry: string; investment: number; stage?: string }) {
  return authedRequest<Project>("/projects/", token, { method: "POST", body: JSON.stringify(payload) });
}

export function updateProject(token: string, projectId: number, payload: Partial<Pick<Project, "name" | "industry" | "investment" | "stage">>) {
  return authedRequest<Project>(`/projects/${projectId}`, token, { method: "PATCH", body: JSON.stringify(payload) });
}

export function setProjectArchived(token: string, projectId: number, archived: boolean) {
  return authedRequest<Project>(`/projects/${projectId}/${archived ? "archive" : "unarchive"}`, token, { method: "POST" });
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
  revision: number;
  payload: Record<string, unknown>;
  result: FinancialResultOut | null;
};

export type StudySaveState = "idle" | "saving" | "saved" | "error";

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

export function saveStudyStep(token: string, studyId: number, step: number, data: Record<string, unknown>, expectedRevision?: number) {
  return authedRequest<Study>("/feasibility/" + studyId + "/step", token, {
    method: "PATCH",
    body: JSON.stringify({ step, data, expected_revision: expectedRevision }),
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

// --- Quick idea check (Entry 1: "لدي فكرة مشروع") -----------------------------

export type QuickIdeaCheckStatus = "PROMISING" | "NEEDS_VALIDATION" | "INSUFFICIENT_DATA" | "HIGH_UNCERTAINTY";

export type QuickIdeaCheckPayload = {
  idea_text: string;
  estimated_capital: number;
  city?: string;
  region?: string;
  customer_segment?: string;
  goal?: string;
  is_existing_business?: boolean;
  project_id?: number;
};

export type QuickIdeaCheckResult = {
  project_id: number;
  study_id: number;
  status: QuickIdeaCheckStatus;
  industry_guess: string | null;
  regulatory_complexity_hint: string;
  known_fields: string[];
  missing_fields: string[];
  evidence_coverage: number;
  assumption_coverage: number;
  main_uncertainties: string[];
  recommended_next_step: string;
};

export function submitQuickIdeaCheck(token: string, payload: QuickIdeaCheckPayload) {
  return authedRequest<QuickIdeaCheckResult>("/quick-idea-check/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// --- Business profile (structured, reusable business facts) -----------------

export type BusinessProfile = {
  study_id: number;
  business_activity: string | null;
  description: string | null;
  city: string | null;
  region: string | null;
  customer_segment: string | null;
  capacity_value: number | null;
  capacity_unit: string | null;
  legal_entity_type: string | null;
  ownership_notes: string | null;
  is_existing_business: boolean;
  company_age_years: number | null;
  current_revenue: number | null;
};

export type BusinessProfileUpdate = Partial<Omit<BusinessProfile, "study_id">>;

export async function getBusinessProfile(token: string, studyId: number): Promise<BusinessProfile | null> {
  const res = await fetch(`${API_BASE}/studies/${studyId}/business-profile/`, {
    credentials: "same-origin",
    headers: { Authorization: "Bearer " + token },
  });
  if (res.status === 404) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(apiErrorMessage(data, res.statusText || "Request failed"));
  return data as BusinessProfile;
}

export function saveBusinessProfile(token: string, studyId: number, payload: BusinessProfileUpdate) {
  return authedRequest<BusinessProfile>(`/studies/${studyId}/business-profile/`, token, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

// --- Evidence (study provenance layer) ---------------------------------------

export const SOURCE_TYPES = [
  "official_statistic",
  "regulation",
  "funding_program",
  "market_report",
  "news",
  "survey",
  "user_document",
  "ai_inference",
  "other",
] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

export const VERIFICATION_STATUSES = ["verified", "user_provided", "unverified"] as const;
export type VerificationStatus = (typeof VERIFICATION_STATUSES)[number];

export const CONFIDENCE_LEVELS = ["low", "medium", "high"] as const;
export type ConfidenceLevel = (typeof CONFIDENCE_LEVELS)[number];

export type AuthorityLevel =
  | "OFFICIAL_PRIMARY"
  | "OFFICIAL_SECONDARY"
  | "REGULATOR"
  | "REPUTABLE_INSTITUTION"
  | "COMMERCIAL_SOURCE"
  | "USER_DOCUMENT"
  | "AI_INFERENCE"
  | "UNVERIFIED";

export type EvidenceItem = {
  id: number;
  study_id: number;
  source_type: SourceType;
  source_name: string | null;
  source_url: string | null;
  publisher: string | null;
  title: string;
  claim: string;
  value_number: number | null;
  value_text: string | null;
  unit: string | null;
  geography: string | null;
  sector: string | null;
  published_at: string | null;
  retrieved_at: string;
  effective_from: string | null;
  effective_to: string | null;
  superseded_by_id: number | null;
  confidence: ConfidenceLevel;
  verification_status: VerificationStatus;
  authority_level: AuthorityLevel;
  snapshot_text: string | null;
  created_at: string;
  updated_at: string;
};

export type EvidenceCreatePayload = {
  source_type: SourceType;
  title: string;
  claim: string;
  source_name?: string;
  source_url?: string;
  publisher?: string;
  value_number?: number;
  value_text?: string;
  unit?: string;
  geography?: string;
  sector?: string;
  confidence?: ConfidenceLevel;
  verification_status?: VerificationStatus;
};

export function listEvidence(token: string, studyId: number) {
  return authedRequest<EvidenceItem[]>(`/studies/${studyId}/evidence`, token);
}

export function createEvidence(token: string, studyId: number, payload: EvidenceCreatePayload) {
  return authedRequest<EvidenceItem>(`/studies/${studyId}/evidence`, token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteEvidence(token: string, studyId: number, evidenceId: number) {
  return authedRequest<void>(`/studies/${studyId}/evidence/${evidenceId}`, token, { method: "DELETE" });
}

export type SourceRegistryEntry = {
  key: string;
  name_en: string;
  name_ar: string;
  domain: string;
  authority_level: AuthorityLevel;
};

export function getSourceRegistry(token: string) {
  return authedRequest<{ authority_levels: AuthorityLevel[]; sources: SourceRegistryEntry[] }>(
    "/sources/registry",
    token,
  );
}

// --- Study assumptions (versioned, provenance-tagged) -------------------------

export const ASSUMPTION_ORIGINS = ["USER", "EVIDENCE_DERIVED", "AI_SUGGESTED", "DEFAULT"] as const;
export type AssumptionOrigin = (typeof ASSUMPTION_ORIGINS)[number];

export type StudyAssumption = {
  id: number;
  study_id: number;
  key: string;
  label_en: string;
  label_ar: string;
  value_number: number | null;
  value_text: string | null;
  unit: string | null;
  origin: AssumptionOrigin;
  reason: string | null;
  confidence: ConfidenceLevel;
  evidence_id: number | null;
  version: number;
  is_active: boolean;
};

export type AssumptionCreatePayload = {
  key: string;
  label_en: string;
  label_ar: string;
  origin: AssumptionOrigin;
  value_number?: number;
  value_text?: string;
  unit?: string;
  reason?: string;
  confidence?: ConfidenceLevel;
  evidence_id?: number;
};

export function listAssumptions(token: string, studyId: number, includeInactive = false) {
  return authedRequest<StudyAssumption[]>(
    `/studies/${studyId}/assumptions/${includeInactive ? "?include_inactive=true" : ""}`,
    token,
  );
}

export function createAssumption(token: string, studyId: number, payload: AssumptionCreatePayload) {
  return authedRequest<StudyAssumption>(`/studies/${studyId}/assumptions/`, token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function retireAssumption(token: string, studyId: number, assumptionId: number) {
  return authedRequest<StudyAssumption>(`/studies/${studyId}/assumptions/${assumptionId}`, token, {
    method: "DELETE",
  });
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
  name_ar: string;
  source_url: string;
  eligibility_sample_ar: string[];
  provider_role_ar: string;
  verified_at: string;
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

export type FundingDocument = { id: number; project_id: number | null; name: string; content_type?: string | null; size_bytes?: number | null; created_at: string };

export async function uploadFundingDocument(token: string, projectId: number, file: File) {
  const form = new FormData(); form.append("project_id", String(projectId)); form.append("file", file);
  const res = await fetch(API_BASE + "/documents/", { method: "POST", headers: { Authorization: "Bearer " + token }, body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(apiErrorMessage(data, res.statusText || "Upload failed"));
  return data as FundingDocument;
}

export function listFundingDocuments(token: string, projectId: number) {
  return authedRequest<FundingDocument[]>(`/documents/?project_id=${projectId}`, token);
}

export async function downloadProtectedFile(path: string, token: string, filename: string) {
  const res = await fetch(API_BASE + path, { headers: { Authorization: "Bearer " + token } });
  if (!res.ok) throw new Error(apiErrorMessage(await res.json().catch(() => ({})), res.statusText));
  const url = URL.createObjectURL(await res.blob()); const link = document.createElement("a"); link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

export function exportProposal(token: string, proposalId: number, fmt: "pdf" | "docx", locale: "ar" | "en") {
  return downloadProtectedFile(`/proposals/${proposalId}/export?fmt=${fmt}&locale=${locale}`, token, `proposal_${proposalId}_${locale}.${fmt}`);
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

export function updateProfile(token: string, payload: { full_name?: string | null; locale?: "ar" | "en" }) {
  return authedRequest<UserProfile>("/auth/me", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function changePassword(token: string, currentPassword: string, newPassword: string) {
  return authedRequest<AccountAction>("/auth/password/change", token, {
    method: "POST",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}

export type AccountAction = {
  accepted: boolean;
  delivery_configured: boolean;
  dev_token?: string | null;
};

export function requestEmailVerification(email: string) {
  return request<AccountAction>("/auth/verification/request", {
    method: "POST", body: JSON.stringify({ email }),
  });
}

export function confirmEmailVerification(token: string) {
  return request<AccountAction>("/auth/verification/confirm", {
    method: "POST", body: JSON.stringify({ token }),
  });
}

export function requestPasswordReset(email: string) {
  return request<AccountAction>("/auth/password/forgot", {
    method: "POST", body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, password: string) {
  return request<AccountAction>("/auth/password/reset", {
    method: "POST", body: JSON.stringify({ token, password }),
  });
}

// --- Proposals -----------------------------------------------------------

export type Proposal = {
  id: number;
  owner_id: number | null;
  project_id: number | null;
  title: string;
  proposal_type: string;
  status: string;
  locale: string;
  payload: Record<string, unknown>;
  version: string;
  feasibility_study_id: number | null;
};

export function listProposals(token: string) {
  return authedRequest<Proposal[]>("/proposals/", token);
}

export function createProposal(token: string, payload: {
  title: string;
  proposal_type?: string;
  locale?: string;
  project_id?: number;
  feasibility_study_id?: number;
  payload?: Record<string, unknown>;
}) {
  return authedRequest<Proposal>("/proposals/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getProposal(token: string, proposalId: number) {
  return authedRequest<Proposal>(`/proposals/${proposalId}`, token);
}

export function updateProposal(token: string, proposalId: number, payload: {
  title?: string;
  status?: string;
  payload?: Record<string, unknown>;
  version?: string;
}) {
  return authedRequest<Proposal>(`/proposals/${proposalId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteProposal(token: string, proposalId: number) {
  return authedRequest<void>(`/proposals/${proposalId}`, token, { method: "DELETE" });
}

// --- Entitlements --------------------------------------------------------

export type Entitlement = {
  service_key: string;
  enabled: boolean;
  plan: string;
  quota: number | null;
  used: number;
};

export function listEntitlements(token: string) {
  return authedRequest<Entitlement[]>("/entitlements/", token);
}

// --- Franchises (public, unauthenticated) ---------------------------------

export type Franchise = {
  id: number;
  brand: string;
  description_en?: string | null;
  description_ar?: string | null;
  sector: string;
  investment_min?: number | null;
  investment_max?: number | null;
  franchise_fee?: number | null;
  regions: string[];
  verification_status: string;
  is_active: boolean;
};

export function listFranchises() {
  return request<Franchise[]>("/franchises/");
}

// --- Business qualification & readiness -----------------------------------

export type QualificationProfile = {
  id: number;
  owner_id: number | null;
  company_name_en?: string | null;
  company_name_ar?: string | null;
  cr_number?: string | null;
  sector?: string | null;
  company_size?: string | null;
  saudization_rate?: number | null;
  overall_score: number;
  category_scores: Record<string, number>;
  recommendations: Array<Record<string, unknown>>;
};

export type QualificationRequirement = {
  id: number;
  profile_id: number;
  category: string;
  title_en: string;
  title_ar: string;
  status: string;
  is_mandatory: boolean;
  authority?: string | null;
};

export function listQualificationProfiles(token: string) {
  return authedRequest<QualificationProfile[]>("/api/qualification/", token);
}

export function createQualificationProfile(token: string, payload: Record<string, unknown>) {
  return authedRequest<QualificationProfile>("/api/qualification/", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listQualificationRequirements(token: string, profileId: number) {
  return authedRequest<QualificationRequirement[]>(`/api/qualification/${profileId}/requirements`, token);
}

export function addQualificationRequirement(token: string, profileId: number, payload: Record<string, unknown>) {
  return authedRequest<QualificationRequirement>(`/api/qualification/${profileId}/requirements`, token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateQualificationRequirement(token: string, profileId: number, requirementId: number, status: string) {
  return authedRequest<QualificationRequirement>(`/api/qualification/${profileId}/requirements/${requirementId}`, token, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export type AdminStats = {
  db_enabled: boolean;
  db_backend: string;
  users: number;
  projects: number;
  studies: number;
  ideas: number;
  franchises: number;
  reports: number;
  recent_activity: Array<{ id: number; action: string; entity?: string | null; entity_id?: number | null }>;
};

export function getAdminStats(token: string) {
  return authedRequest<AdminStats>("/admin/stats", token);
}

export type AdminLead = LeadPayload & { id: number; status: string };

export function listAdminLeads(token: string) {
  return authedRequest<AdminLead[]>("/leads/", token);
}

export function listAdminUsers(token: string) {
  return authedRequest<UserProfile[]>("/admin/users", token);
}

export function createAdminUser(token: string, payload: {
  email: string;
  password: string;
  full_name?: string;
  role_key: string;
  locale: "ar" | "en";
}) {
  return authedRequest<UserProfile>("/admin/users", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
