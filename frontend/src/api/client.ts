// Minimal typed wrapper around the 3 endpoints this app uses. Deliberately
// thin - just fetch() + typed return shapes, no client library.
//
// Requests go to "/api/..." (not a full http://localhost:8000 URL) - the
// Vite dev-server proxy (see vite.config.ts) forwards those to FastAPI,
// so the browser only ever talks to its own origin and there's no CORS
// config to worry about in dev.

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LeaderSummary {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  location: string;
  is_direct_staff: boolean;
}

export interface MemberSummary {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface TeamInsight {
  id: string;
  name: string;
  location: string;
  leader: LeaderSummary | null;
  members: MemberSummary[];
  member_count: number;
  non_direct_staff_count: number;
  non_direct_staff_ratio: number;
  leader_co_located: boolean;
  leader_is_non_direct_staff: boolean;
  reports_to_org_leader: boolean;
}

export interface InsightsSummary {
  total_teams: number;
  teams_with_leader_not_colocated: number;
  teams_with_non_direct_leader: number;
  teams_with_high_non_direct_ratio: number;
  teams_reporting_to_org_leader: number;
}

class ApiError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

async function parseErrorOrThrow(res: Response): Promise<never> {
  const body = await res.json().catch(() => ({}));
  const detail =
    typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`;
  throw new ApiError(res.status, detail);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  // FastAPI's OAuth2PasswordRequestForm expects form-encoded body, not
  // JSON - hence URLSearchParams + this content-type instead of
  // JSON.stringify.
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  if (!res.ok) return parseErrorOrThrow(res);
  return res.json();
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

export async function getTeamsOverview(token: string): Promise<TeamInsight[]> {
  const res = await fetch("/api/insights/teams-overview", { headers: authHeaders(token) });
  if (!res.ok) return parseErrorOrThrow(res);
  return res.json();
}

export async function getSummary(token: string): Promise<InsightsSummary> {
  const res = await fetch("/api/insights/summary", { headers: authHeaders(token) });
  if (!res.ok) return parseErrorOrThrow(res);
  return res.json();
}
