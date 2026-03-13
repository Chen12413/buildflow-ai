from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from app.schemas.demo import DemoBlueprintDocument
from app.schemas.planning import PlanningDocument
from app.schemas.prd import PRDDocument
from app.schemas.task_breakdown import TaskBreakdownDocument


class ArtifactType(StrEnum):
    PRD = "prd"
    PLANNING = "planning"
    TASK_BREAKDOWN = "task_breakdown"
    DEMO = "demo"


class ArtifactBaseRead(BaseModel):
    id: str
    project_id: str
    run_id: str
    type: ArtifactType
    version: int
    content_markdown: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PRDArtifactRead(ArtifactBaseRead):
    type: Literal[ArtifactType.PRD] = ArtifactType.PRD
    content_json: PRDDocument


class PlanningArtifactRead(ArtifactBaseRead):
    type: Literal[ArtifactType.PLANNING] = ArtifactType.PLANNING
    content_json: PlanningDocument


class TaskBreakdownArtifactRead(ArtifactBaseRead):
    type: Literal[ArtifactType.TASK_BREAKDOWN] = ArtifactType.TASK_BREAKDOWN
    content_json: TaskBreakdownDocument


class DemoArtifactRead(ArtifactBaseRead):
    type: Literal[ArtifactType.DEMO] = ArtifactType.DEMO
    content_json: DemoBlueprintDocument


ArtifactRead = PRDArtifactRead | PlanningArtifactRead | TaskBreakdownArtifactRead | DemoArtifactRead
