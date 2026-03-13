from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class RunType(StrEnum):
    CLARIFICATION_GENERATION = "clarification_generation"
    PRD_GENERATION = "prd_generation"
    PLANNING_GENERATION = "planning_generation"
    TASK_BREAKDOWN_GENERATION = "task_breakdown_generation"
    DEMO_GENERATION = "demo_generation"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunRead(BaseModel):
    id: str
    project_id: str
    type: RunType
    status: RunStatus
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
