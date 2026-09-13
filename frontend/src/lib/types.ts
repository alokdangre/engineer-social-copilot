export type Platform = "github" | "x" | "linkedin" | "user" | "other";

export type ActionType =
  | "original_post"
  | "comment"
  | "reply"
  | "repost"
  | "quote_post"
  | "relationship_action"
  | "read_learn"
  | "build_experiment"
  | "contribution"
  | "application"
  | "profile_improvement"
  | "collect_evidence"
  | "no_action";

export type RecommendationStatus =
  | "draft"
  | "awaiting_review"
  | "approved"
  | "edited"
  | "rejected"
  | "postponed"
  | "handed_off"
  | "reported_performed"
  | "verified_performed"
  | "measurement_scheduled"
  | "measured"
  | "expired";

export type ReviewDecision = "approve" | "edit" | "reject" | "later";

export type FeedbackScope = "this_only" | "similar" | "general";

export type EvidenceStatus =
  | "observed"
  | "self_reported"
  | "user_confirmed"
  | "inferred"
  | "disputed"
  | "superseded";

export type Visibility = "private" | "potentially_shareable" | "approved_public";

export type Sensitivity = "none" | "low" | "medium" | "high" | "confidential";

export type MemoryCategory =
  | "identity_preferences"
  | "goals_audiences"
  | "technical_knowledge"
  | "projects_contributions"
  | "reading_media"
  | "events_experiences"
  | "opinions_reflections"
  | "people_relationships"
  | "content_actions"
  | "strategies_experiments";

export type HypothesisStatus =
  | "proposed"
  | "testing"
  | "supported"
  | "weakened"
  | "contradicted"
  | "retired";

export type WorkflowKind =
  | "profile"
  | "daily_capture"
  | "research"
  | "recommendation_review"
  | "outcome_strategy";

export type WorkflowStatus = "pending" | "running" | "interrupted" | "completed" | "failed";

export type ConnectorStatus =
  | "not_connected"
  | "pending_auth"
  | "connected"
  | "expired"
  | "revoked"
  | "error";

export interface UserAccount {
  id: string;
  email: string;
  display_name: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

export interface Recommendation {
  id: string;
  action_type: ActionType;
  platform: Platform | null;
  status: RecommendationStatus;
  title: string;
  purpose: string;
  target_audience: string;
  why_now: string;
  draft: string | null;
  final_text: string | null;
  effort_minutes: number;
  score: number;
  evidence_ids: string[];
  source_urls: string[];
  risks: string[];
  unknowns: string[];
  expires_at: string | null;
  created_at: string;
}

export interface ReviewInput {
  decision: ReviewDecision;
  recommendation_id?: string;
  final_text?: string;
  reason_category?: string;
  reason_text?: string;
  scope?: FeedbackScope;
  postpone_until?: string;
}

export interface ActionPerformedInput {
  performed_at?: string;
  public_url?: string;
  external_id?: string;
  notes?: string;
}

export interface ActionRecord {
  id: string;
  user_id: string;
  recommendation_id: string;
  status: RecommendationStatus;
  performed_at: string | null;
  verified_at: string | null;
  public_url: string | null;
  external_id: string | null;
  verification_source: string | null;
  measurement_due_at: string | null;
  action_metadata: Record<string, unknown>;
  created_at: string;
}

export interface MetricsInput {
  metrics: Record<string, number | null>;
  source?: string;
}

export interface MemoryRecord {
  id: string;
  category: MemoryCategory;
  title: string;
  statement: string;
  evidence_status: EvidenceStatus;
  confidence: number;
  visibility: Visibility;
  sensitivity: Sensitivity;
  source_platform: Platform;
  source_reference: string | null;
  source_content_id: string | null;
  observed_at: string | null;
  captured_at: string;
  valid_until: string | null;
  retention_expires_at: string | null;
  usage_rules: Record<string, unknown>;
  record_metadata: Record<string, unknown>;
  created_at: string;
}

export interface MemoryCreate {
  category: MemoryCategory;
  title: string;
  statement: string;
  evidence_status: EvidenceStatus;
  confidence?: number;
  visibility?: Visibility;
  sensitivity?: Sensitivity;
  source_platform?: Platform;
  source_reference?: string;
}

export interface MemoryLink {
  id: string;
  from_record_id: string;
  to_record_id: string;
  relation: string;
  link_metadata: Record<string, unknown>;
}

export interface StrategyVersion {
  id: string;
  version: number;
  status: string;
  positioning: string;
  content_pillars: string[];
  audience_priorities: string[];
  platform_tactics: Record<string, unknown>;
  relationship_approach: string;
  excluded_tactics: string[];
  rationale: string;
  previous_version_id: string | null;
  activated_at: string | null;
  created_at: string;
}

export interface Hypothesis {
  id: string;
  strategy_version_id: string | null;
  statement: string;
  observation: string;
  platform: Platform | null;
  target_audience: string;
  expected_outcome: string;
  status: HypothesisStatus;
  confidence: number;
}

export interface Goal {
  id: string;
  title: string;
  description: string;
  target_audiences: string[];
  success_criteria: string[];
  priority: number;
  status: string;
  target_date: string | null;
}

export interface GoalCreate {
  title: string;
  description: string;
  target_audiences?: string[];
  success_criteria?: string[];
  priority?: number;
}

export interface ConnectorAccount {
  id: string;
  platform: Platform;
  status: ConnectorStatus;
  external_user_id: string | null;
  username: string | null;
  scopes: string[];
  token_expires_at: string | null;
  last_sync_at: string | null;
  last_error: string | null;
}

export interface WorkflowRun {
  id: string;
  kind: WorkflowKind;
  thread_id: string;
  status: WorkflowStatus;
  current_node: string | null;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  interrupt_data: Record<string, unknown>;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface WorkflowInvocationResult {
  run: WorkflowRun;
  recommendations: Recommendation[];
}

export interface SchedulerStatus {
  is_running: boolean;
  interval_seconds: number;
  last_run_at: string | null;
  last_result: Record<string, unknown> | null;
}
