from pydantic import BaseModel, Field


class PRDDocument(BaseModel):
    product_summary: str = Field(min_length=1)
    problem_statement: str = Field(min_length=1)
    target_users: list[str] = Field(min_length=1)
    core_scenarios: list[str] = Field(min_length=1)
    mvp_goal: str = Field(min_length=1)
    in_scope: list[str] = Field(min_length=1)
    out_of_scope: list[str] = Field(min_length=1)
    user_stories: list[str] = Field(min_length=1)
    success_metrics: list[str] = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
