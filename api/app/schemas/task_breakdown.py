from pydantic import BaseModel, Field


class TaskBreakdownTask(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_focus: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(min_length=1)
    test_cases: list[str] = Field(min_length=1)


class TaskBreakdownModule(BaseModel):
    module_name: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    user_value: str = Field(min_length=1)
    tasks: list[TaskBreakdownTask] = Field(min_length=1)


class TaskBreakdownDocument(BaseModel):
    delivery_goal: str = Field(min_length=1)
    sequencing_strategy: str = Field(min_length=1)
    modules: list[TaskBreakdownModule] = Field(min_length=1)
    integration_risks: list[str] = Field(min_length=1)
    qa_strategy: list[str] = Field(min_length=1)
    release_checklist: list[str] = Field(min_length=1)
