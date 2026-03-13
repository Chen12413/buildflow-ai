from pydantic import BaseModel, Field

from app.schemas.demo import DemoAgentCard, DemoBlueprintDocument, DemoFlowStep, DemoScreen, DemoScreenAction
from app.schemas.task_breakdown import TaskBreakdownDocument, TaskBreakdownModule, TaskBreakdownTask


class ArchitectTaskDraft(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_focus: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)


class ArchitectModuleDraft(BaseModel):
    module_name: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    user_value: str = Field(min_length=1)
    tasks: list[ArchitectTaskDraft] = Field(min_length=1)


class TaskBreakdownArchitectNotes(BaseModel):
    delivery_goal: str = Field(min_length=1)
    modules: list[ArchitectModuleDraft] = Field(min_length=1)


class TaskBreakdownDeliveryNotes(BaseModel):
    sequencing_strategy: str = Field(min_length=1)
    integration_risks: list[str] = Field(min_length=1)
    release_checklist: list[str] = Field(min_length=1)


class TaskBreakdownTaskQualityDraft(BaseModel):
    module_name: str = Field(min_length=1)
    task_title: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)
    test_cases: list[str] = Field(min_length=1)


class TaskBreakdownQANotes(BaseModel):
    qa_strategy: list[str] = Field(min_length=1)
    task_quality_plans: list[TaskBreakdownTaskQualityDraft] = Field(min_length=1)


class DemoProductNotes(BaseModel):
    demo_goal: str = Field(min_length=1)
    hero_title: str = Field(min_length=1)
    hero_subtitle: str = Field(min_length=1)
    target_persona: str = Field(min_length=1)
    primary_cta: str = Field(min_length=1)
    secondary_cta: str | None = None
    key_metrics: list[str] = Field(min_length=1)


class DemoUXActionDraft(BaseModel):
    label: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    result_preview: str | None = None


class DemoUXScreenDraft(BaseModel):
    name: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    description: str = Field(min_length=1)
    highlights: list[str] = Field(min_length=1)
    actions: list[DemoUXActionDraft] = Field(min_length=1)
    sample_inputs: list[str] = Field(default_factory=list)
    sample_outputs: list[str] = Field(default_factory=list)
    success_signal: str | None = None


class DemoUXNotes(BaseModel):
    screens: list[DemoUXScreenDraft] = Field(min_length=1)


class DemoNarrativeStepDraft(BaseModel):
    step_title: str = Field(min_length=1)
    user_goal: str = Field(min_length=1)
    system_response: str = Field(min_length=1)


class DemoNarrativeNotes(BaseModel):
    flow_steps: list[DemoNarrativeStepDraft] = Field(min_length=1)
    demo_script: list[str] = Field(min_length=1)


def _normalize_key(value: str) -> str:
    return value.strip().casefold()


def assemble_task_breakdown_document(
    architect_notes: TaskBreakdownArchitectNotes,
    delivery_notes: TaskBreakdownDeliveryNotes,
    qa_notes: TaskBreakdownQANotes,
) -> TaskBreakdownDocument:
    quality_map = {
        (_normalize_key(item.module_name), _normalize_key(item.task_title)): item
        for item in qa_notes.task_quality_plans
    }

    modules: list[TaskBreakdownModule] = []
    for module in architect_notes.modules:
        tasks: list[TaskBreakdownTask] = []
        for task in module.tasks:
            quality = quality_map.get((_normalize_key(module.module_name), _normalize_key(task.title)))
            acceptance_criteria = quality.acceptance_criteria if quality else [f"完成 {task.title} 的核心交付并通过人工验收"]
            test_cases = quality.test_cases if quality else [f"验证 {task.title} 在主链路中可正常运行"]
            tasks.append(
                TaskBreakdownTask(
                    title=task.title,
                    description=task.description,
                    owner_focus=task.owner_focus,
                    dependencies=task.dependencies,
                    acceptance_criteria=acceptance_criteria,
                    test_cases=test_cases,
                )
            )

        modules.append(
            TaskBreakdownModule(
                module_name=module.module_name,
                goal=module.goal,
                user_value=module.user_value,
                tasks=tasks,
            )
        )

    return TaskBreakdownDocument(
        delivery_goal=architect_notes.delivery_goal,
        sequencing_strategy=delivery_notes.sequencing_strategy,
        modules=modules,
        integration_risks=delivery_notes.integration_risks,
        qa_strategy=qa_notes.qa_strategy,
        release_checklist=delivery_notes.release_checklist,
    )


def assemble_demo_blueprint_document(
    project_name: str,
    product_notes: DemoProductNotes,
    ux_notes: DemoUXNotes,
    narrative_notes: DemoNarrativeNotes,
    agent_cards: list[DemoAgentCard],
) -> DemoBlueprintDocument:
    screens = [
        DemoScreen(
            name=screen.name,
            purpose=screen.purpose,
            headline=screen.headline,
            description=screen.description,
            highlights=screen.highlights,
            actions=[
                DemoScreenAction(
                    label=action.label,
                    detail=action.detail,
                    result_preview=action.result_preview,
                )
                for action in screen.actions
            ],
            sample_inputs=screen.sample_inputs,
            sample_outputs=screen.sample_outputs,
            success_signal=screen.success_signal,
        )
        for screen in ux_notes.screens
    ]
    flow_steps = [
        DemoFlowStep(
            step_title=step.step_title,
            user_goal=step.user_goal,
            system_response=step.system_response,
        )
        for step in narrative_notes.flow_steps
    ]
    return DemoBlueprintDocument(
        product_name=project_name,
        demo_goal=product_notes.demo_goal,
        hero_title=product_notes.hero_title,
        hero_subtitle=product_notes.hero_subtitle,
        target_persona=product_notes.target_persona,
        primary_cta=product_notes.primary_cta,
        secondary_cta=product_notes.secondary_cta,
        key_metrics=product_notes.key_metrics,
        screens=screens,
        flow_steps=flow_steps,
        agent_cards=agent_cards,
        demo_script=narrative_notes.demo_script,
    )
