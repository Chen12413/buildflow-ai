from pydantic import BaseModel, Field


class PlanningTask(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_focus: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)


class PlanningMilestone(BaseModel):
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    tasks: list[PlanningTask] = Field(min_length=1)


class PlanningDocument(BaseModel):
    objective: str = Field(min_length=1)
    delivery_strategy: str = Field(min_length=1)
    milestones: list[PlanningMilestone] = Field(min_length=1)
    dependencies: list[str] = Field(min_length=1)
    testing_focus: list[str] = Field(min_length=1)
    rollout_notes: list[str] = Field(min_length=1)
