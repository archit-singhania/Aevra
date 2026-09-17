export type Platform = "linkedin" | "instagram" | "threads" | "x" | "facebook" | "youtube";

export type User = {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
};

export type Workspace = {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
};

export type Brand = {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  description: string;
  website_url: string | null;
  industry: string | null;
  tone_attributes: string[];
  target_audiences: string[];
  preferred_ctas: string[];
  preferred_hashtags: string[];
  status: "draft" | "active" | "archived";
  created_at: string;
  updated_at: string;
};

export type Campaign = {
  id: string;
  workspace_id: string;
  brand_id: string;
  name: string;
  goal: string;
  product_service: string;
  audience: string;
  instructions: string;
  platforms: Platform[];
  media_types: string[];
  publishing_mode: "manual" | "assisted" | "autonomous";
  status: string;
  current_revision: number;
  latest_feedback: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type ContentVariant = {
  id: string;
  campaign_id: string;
  revision: number;
  platform: Platform;
  title: string | null;
  caption: string;
  hashtags: string[];
  call_to_action: string | null;
  status: "draft" | "approved" | "rejected" | "superseded";
  quality_score: number;
  validation_issues: string[];
  citations: Array<{ document_title?: string; excerpt?: string; [key: string]: unknown }>;
  generated_by_model: string;
  created_at: string;
};

export type KnowledgeDocument = {
  id: string;
  title: string;
  source_type: string;
  source_uri: string | null;
  content_length: number;
  status: string;
  created_at: string;
};

export type Citation = {
  chunk_id: string;
  document_id: string;
  document_title: string;
  source_uri: string | null;
  score: number;
  excerpt: string;
};

export type MediaAsset = {
  id: string;
  campaign_id: string;
  media_type: "image" | "video";
  status: string;
  filename: string;
  mime_type: string;
  width: number | null;
  height: number | null;
  prompt: string | null;
  created_at: string;
  download_url: string | null;
};

export type SocialAccount = {
  id: string;
  platform: Platform;
  external_account_id: string;
  display_name: string;
  status: "connected" | "paused" | "revoked";
  capabilities: string[];
  last_verified_at: string | null;
};

export type ScheduledPost = {
  id: string;
  campaign_id: string;
  social_account_id: string;
  scheduled_for: string;
  status: string;
  payload: { text?: string; media_urls?: string[] };
  created_at: string;
};

export type PublishJob = {
  id: string;
  status: string;
  external_url: string | null;
  error_message: string | null;
  published_at: string | null;
};

export type CampaignGeneration = {
  campaign: Campaign;
  variants: ContentVariant[];
  plan: Record<string, unknown>;
  steps: Array<{ node_name: string; status: string; duration_ms: number }>;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api/v1";

function apiUrl(path: string) {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function request<T>(
  path: string,
  token?: string | null,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  // Browser sessions use an HTTP-only cookie. Native clients can keep passing
  // a bearer token; the sentinel is deliberately never serialized as a header.
  if (token && token !== "cookie") headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(apiUrl(path), {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string | Array<{ msg?: string }>;
      error?: { message?: string };
    } | null;
    const detail = Array.isArray(payload?.detail)
      ? payload.detail
          .map((item) => item.msg)
          .filter(Boolean)
          .join(". ")
      : payload?.detail;
    throw new ApiError(
      payload?.error?.message ?? detail ?? "The request could not be completed.",
      response.status,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; expires_in: number }>("/auth/login", undefined, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (payload: {
    email: string;
    password: string;
    display_name: string;
    organization_name: string;
    workspace_name: string;
    timezone: string;
  }) =>
    request<{
      user: User;
      workspace: Workspace;
      token: { access_token: string; expires_in: number };
    }>("/auth/register", undefined, { method: "POST", body: JSON.stringify(payload) }),
  me: (token: string) => request<User>("/auth/me", token),
  logout: () => request<void>("/auth/logout", undefined, { method: "POST" }),
  workspaces: (token: string) => request<Workspace[]>("/workspaces", token),
  brands: (token: string, workspaceId: string) =>
    request<Brand[]>(`/workspaces/${workspaceId}/brands`, token),
  createBrand: (
    token: string,
    workspaceId: string,
    payload: Omit<Brand, "id" | "workspace_id" | "slug" | "created_at" | "updated_at">,
  ) =>
    request<Brand>(`/workspaces/${workspaceId}/brands`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  documents: (token: string, workspaceId: string) =>
    request<KnowledgeDocument[]>(`/workspaces/${workspaceId}/knowledge/documents`, token),
  ingest: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<{ document: KnowledgeDocument; chunks_created: number; deduplicated: boolean }>(
      `/workspaces/${workspaceId}/knowledge/documents`,
      token,
      { method: "POST", body: JSON.stringify(payload) },
    ),
  searchKnowledge: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<{ citations: Citation[] }>(`/workspaces/${workspaceId}/knowledge/search`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  campaigns: (token: string, workspaceId: string) =>
    request<Campaign[]>(`/workspaces/${workspaceId}/campaigns`, token),
  createCampaign: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<Campaign>(`/workspaces/${workspaceId}/campaigns`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  generateCampaign: (token: string, workspaceId: string, campaignId: string, feedback?: string) =>
    request<CampaignGeneration>(
      `/workspaces/${workspaceId}/campaigns/${campaignId}/generate`,
      token,
      {
        method: "POST",
        body: JSON.stringify({ feedback: feedback || null }),
      },
    ),
  decideCampaign: (
    token: string,
    workspaceId: string,
    campaignId: string,
    decision: "approve" | "reject",
    feedback?: string,
  ) =>
    request<CampaignGeneration>(
      `/workspaces/${workspaceId}/campaigns/${campaignId}/decision`,
      token,
      {
        method: "POST",
        body: JSON.stringify({ decision, feedback: feedback || null }),
      },
    ),
  variants: (token: string, workspaceId: string, campaignId: string) =>
    request<ContentVariant[]>(`/workspaces/${workspaceId}/campaigns/${campaignId}/variants`, token),
  media: (token: string, workspaceId: string) =>
    request<MediaAsset[]>(`/workspaces/${workspaceId}/media/assets`, token),
  generateImage: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<{ assets: MediaAsset[] }>(`/workspaces/${workspaceId}/media/images/generate`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  accounts: (token: string, workspaceId: string) =>
    request<SocialAccount[]>(`/workspaces/${workspaceId}/publishing/accounts`, token),
  connectAccount: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<SocialAccount>(`/workspaces/${workspaceId}/publishing/accounts`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  publish: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<PublishJob>(`/workspaces/${workspaceId}/publishing/jobs`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  schedule: (token: string, workspaceId: string, payload: Record<string, unknown>) =>
    request<ScheduledPost>(`/workspaces/${workspaceId}/operations/schedule`, token, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  scheduled: (token: string, workspaceId: string) =>
    request<ScheduledPost[]>(`/workspaces/${workspaceId}/operations/schedule`, token),
};
