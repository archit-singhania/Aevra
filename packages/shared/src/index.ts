export const PRODUCT_NAME = "VAE" as const;
export const API_VERSION = "v1" as const;

export const APPROVAL_MODES = ["MANUAL", "ASSISTED", "AUTONOMOUS"] as const;
export type ApprovalMode = (typeof APPROVAL_MODES)[number];

export const CAMPAIGN_STATES = [
  "DRAFT",
  "CONTEXT_RETRIEVAL",
  "PLANNING",
  "CONTENT_GENERATION",
  "MEDIA_GENERATION",
  "PLATFORM_ADAPTATION",
  "VALIDATION",
  "AWAITING_APPROVAL",
  "APPROVED",
  "SCHEDULED",
  "PUBLISHING",
  "PUBLISHED",
  "ANALYZING",
  "COMPLETED",
  "FAILED",
  "RETRYING",
  "CANCELLED",
] as const;

export type CampaignState = (typeof CAMPAIGN_STATES)[number];
