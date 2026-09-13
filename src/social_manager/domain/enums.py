from enum import StrEnum


class Platform(StrEnum):
    GITHUB = "github"
    X = "x"
    LINKEDIN = "linkedin"
    USER = "user"
    WEB = "web"


class ConnectorStatus(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class MemoryCategory(StrEnum):
    IDENTITY_PREFERENCE = "identity_preference"
    GOAL_AUDIENCE = "goal_audience"
    TECHNICAL_KNOWLEDGE = "technical_knowledge"
    PROJECT_CONTRIBUTION = "project_contribution"
    READING_MEDIA = "reading_media"
    EVENT_EXPERIENCE = "event_experience"
    OPINION_REFLECTION = "opinion_reflection"
    PERSON_RELATIONSHIP = "person_relationship"
    CONTENT_ACTION = "content_action"
    STRATEGY_EXPERIMENT = "strategy_experiment"
    QUESTION_UNCERTAINTY = "question_uncertainty"


class EvidenceStatus(StrEnum):
    OBSERVED = "observed"
    SELF_REPORTED = "self_reported"
    USER_CONFIRMED = "user_confirmed"
    INFERRED = "inferred"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


class Visibility(StrEnum):
    PRIVATE = "private"
    POTENTIALLY_SHAREABLE = "potentially_shareable"
    APPROVED_PUBLIC = "approved_public"


class Sensitivity(StrEnum):
    NONE = "none"
    PERSONAL = "personal"
    THIRD_PARTY = "third_party"
    EMPLOYER = "employer"
    INTERVIEW = "interview"
    PRIVATE_PROJECT = "private_project"


class ActionType(StrEnum):
    ORIGINAL_POST = "original_post"
    COMMENT = "comment"
    REPLY = "reply"
    REPOST = "repost"
    RELATIONSHIP_FOLLOWUP = "relationship_followup"
    READ_LEARN = "read_learn"
    BUILD_TEST = "build_test"
    DOCUMENT_CONTRIBUTE = "document_contribute"
    CAREER_OPPORTUNITY = "career_opportunity"
    PROFILE_IMPROVEMENT = "profile_improvement"
    NO_ACTION = "no_action"


class RecommendationStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    POSTPONED = "postponed"
    HANDED_OFF = "handed_off"
    REPORTED_PERFORMED = "reported_performed"
    VERIFIED_PERFORMED = "verified_performed"
    MEASUREMENT_SCHEDULED = "measurement_scheduled"
    MEASURED = "measured"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    LATER = "later"


class FeedbackScope(StrEnum):
    THIS_ONLY = "this_only"
    SIMILAR = "similar"
    GENERAL = "general"


class WorkflowKind(StrEnum):
    PROFILE = "profile"
    DAILY_CAPTURE = "daily_capture"
    RESEARCH = "research"
    RECOMMENDATION_REVIEW = "recommendation_review"
    OUTCOME_STRATEGY = "outcome_strategy"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    PAUSED = "paused"
    RETIRED = "retired"


class ContentType(StrEnum):
    PROFILE = "profile"
    REPOSITORY = "repository"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    POST = "post"
    COMMENT = "comment"
    REPLY = "reply"
    REPOST = "repost"
    ANALYTICS = "analytics"
    OTHER = "other"


class SourceAccessMethod(StrEnum):
    OFFICIAL_API = "official_api"
    USER_EXPORT = "user_export"
    USER_PROVIDED = "user_provided"
    PUBLIC_LINK = "public_link"
