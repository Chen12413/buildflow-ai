from pydantic import BaseModel, Field


class DemoScreenAction(BaseModel):
    label: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    result_preview: str | None = None


class DemoScreen(BaseModel):
    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    description: str = Field(min_length=1)
    highlights: list[str] = Field(min_length=1)
    actions: list[DemoScreenAction] = Field(min_length=1)
    sample_inputs: list[str] = Field(default_factory=list)
    sample_outputs: list[str] = Field(default_factory=list)
    success_signal: str | None = None


class DemoFlowStep(BaseModel):
    step_title: str = Field(min_length=1)
    user_goal: str = Field(min_length=1)
    system_response: str = Field(min_length=1)


class DemoAgentCard(BaseModel):
    agent_name: str = Field(min_length=1)
    responsibility: str = Field(min_length=1)
    prompt_focus: str = Field(min_length=1)
    output_summary: str = Field(min_length=1)
    status: str = Field(default="completed", min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    system_prompt_preview: str | None = None
    user_prompt_preview: str | None = None
    model_used: str | None = None


class DemoBlueprintDocument(BaseModel):
    product_name: str = Field(min_length=1)
    demo_goal: str = Field(min_length=1)
    hero_title: str = Field(min_length=1)
    hero_subtitle: str = Field(min_length=1)
    target_persona: str = Field(min_length=1)
    primary_cta: str = Field(min_length=1)
    secondary_cta: str | None = None
    key_metrics: list[str] = Field(min_length=1)
    screens: list[DemoScreen] = Field(min_length=1)
    flow_steps: list[DemoFlowStep] = Field(min_length=1)
    agent_cards: list[DemoAgentCard] = Field(min_length=1)
    demo_script: list[str] = Field(min_length=1)
