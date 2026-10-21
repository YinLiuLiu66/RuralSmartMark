from enum import StrEnum


class AgentName(StrEnum):
    STORY = "story"
    PACKAGING = "packaging"
    MARKETING = "marketing"
    PRICING = "pricing"


class AgentStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    APPROVED = "approved"
    FAILED = "failed"
