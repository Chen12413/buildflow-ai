import json
import re
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.multi_agent_models import (
    DemoNarrativeNotes,
    DemoProductNotes,
    DemoUXNotes,
    TaskBreakdownArchitectNotes,
    TaskBreakdownDeliveryNotes,
    TaskBreakdownQANotes,
    assemble_demo_blueprint_document,
    assemble_task_breakdown_document,
)
from app.prompts.clarification_prompt import build_clarification_prompt
from app.prompts.demo_prompt import build_demo_narrative_prompt, build_demo_product_prompt, build_demo_ux_prompt
from app.prompts.planning_prompt import build_planning_prompt
from app.prompts.prd_prompt import build_prd_prompt
from app.prompts.task_breakdown_prompt import (
    build_task_breakdown_architect_prompt,
    build_task_breakdown_delivery_prompt,
    build_task_breakdown_qa_prompt,
)
from app.schemas.demo import DemoAgentCard, DemoBlueprintDocument, DemoFlowStep, DemoScreen, DemoScreenAction
from app.schemas.planning import PlanningDocument, PlanningMilestone, PlanningTask
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead
from app.schemas.task_breakdown import TaskBreakdownDocument, TaskBreakdownModule, TaskBreakdownTask

try:
    from openai import (
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        OpenAI,
        OpenAIError,
        PermissionDeniedError,
        RateLimitError,
    )
except ImportError:
    APIConnectionError = APITimeoutError = AuthenticationError = BadRequestError = NotFoundError = OpenAIError = PermissionDeniedError = RateLimitError = Exception
    OpenAI = None

SchemaT = TypeVar("SchemaT", bound=BaseModel)
DEFAULT_MOCK_MODEL = "mock-buildflow-v1"
DEFAULT_BAILIAN_MODEL = "qwen3.5-plus"
DEFAULT_BAILIAN_CHAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_BAILIAN_RESPONSES_BASE_URL = "https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1"
DEFAULT_BAILIAN_RESPONSES_TIMEOUT_SECONDS = 15.0
DEFAULT_BAILIAN_CHAT_TIMEOUT_SECONDS = 120.0
DEFAULT_BAILIAN_RESPONSES_MAX_RETRIES = 1
DEFAULT_BAILIAN_CHAT_MAX_RETRIES = 2
RESPONSES_FALLBACK_ERROR_CODES = {
    "bailian_empty_response",
    "bailian_parse_failed",
    "bailian_responses_unavailable",
    "bailian_request_failed",
    "bailian_timeout",
}
TRANSIENT_BAILIAN_ERROR_CODES = {
    "bailian_timeout",
    "bailian_request_failed",
    "bailian_responses_unavailable",
    "bailian_parse_failed",
    "bailian_rate_limited",
}


class ClarificationQuestionsDocument(BaseModel):
    questions: list[str] = Field(min_length=3, max_length=5)


class MockLLMProvider(LLMProvider):
    def generate_clarification_questions(self, project: ProjectRead) -> list[str]:
        constraints = project.constraints or "暂无额外约束"
        return [
            f"{project.name} 当前最优先要解决的用户痛点是什么？",
            f"{project.target_user} 会在什么场景下高频使用 {project.name}？",
            f"{project.name} 的 v0.1 最小可用功能边界应该保留哪些能力？",
            f"在约束“{constraints}”下，{project.name} 的成功标准是什么？",
        ]

    def generate_prd_document(self, project: ProjectRead, answers: list[str]) -> PRDDocument:
        answer_summary = answers[:3] if answers else ["用户尚未补充详细澄清答案，系统基于初始想法生成首版 PRD。"]
        return PRDDocument(
            product_summary=f"{project.name} 是一款面向 {project.target_user} 的 AI 产品交付助手，用于把模糊想法整理成结构化 PRD。",
            problem_statement=f"目标用户缺少稳定、可复用的方法，将“{project.idea}”这类模糊想法快速整理为可执行需求文档。",
            target_users=_split_target_users(project.target_user),
            core_scenarios=[
                f"围绕“{project.idea}”快速创建项目草案。",
                "通过澄清问答补齐关键背景与边界。",
                "导出 Markdown 并进入后续开发协作流程。",
            ],
            mvp_goal="让用户在 10 分钟内从产品想法得到一份结构化 PRD。",
            in_scope=["项目创建", "澄清问题生成", "澄清答案保存", "PRD 生成与 Markdown 导出"],
            out_of_scope=["自动生成完整代码", "自动部署生产环境", "复杂权限系统"],
            user_stories=[
                f"作为 {project.target_user}，我希望快速得到结构化 PRD，以便继续推进产品落地。",
                "作为项目发起人，我希望导出 Markdown，方便同步到 GitHub 或文档平台。",
            ],
            success_metrics=["PRD 生成成功率 > 90%", "首版 PRD 输出时间 < 10 分钟", "用户无需从零手写 PRD"],
            risks=[*answer_summary, "如果输入信息过少，PRD 可能偏泛，需要继续迭代补充。"],
        )

    def generate_planning_document(self, project: ProjectRead, prd_document: PRDDocument, answers: list[str]) -> PlanningDocument:
        short_answers = answers[:2] if answers else ["澄清信息有限，规划基于最新 PRD 自动生成。"]
        scope_items = prd_document.in_scope[:4]
        return PlanningDocument(
            objective=f"围绕 {project.name} 的 v0.1 能力，形成一份可执行的开发与验证计划。",
            delivery_strategy="按照基础工程、Agent 工作流、前后端联调与交付验收三阶段推进，每段都要求可运行、可验证、可回滚。",
            milestones=[
                PlanningMilestone(
                    title="基础工程与数据模型",
                    goal="先稳定项目骨架、核心实体和基础 API，为后续 Agent 能力提供清晰边界。",
                    tasks=[
                        PlanningTask(
                            title="初始化前后端工程",
                            description="完成 Next.js 与 FastAPI 的基础目录、配置与开发环境约定。",
                            owner_focus="工程基础",
                            acceptance_criteria=["前后端项目可独立启动", "基础配置文件齐全"],
                        ),
                        PlanningTask(
                            title="落地核心模型",
                            description=f"围绕 {', '.join(scope_items) if scope_items else '主链路'} 建立 Project、Run、Artifact 等核心实体。",
                            owner_focus="后端数据层",
                            acceptance_criteria=["核心表结构清晰", "基础 CRUD 可联调"],
                        ),
                    ],
                ),
                PlanningMilestone(
                    title="Agent 工作流接入",
                    goal="把 Clarify、PRD、Planning 串成可观察工作流，而不是零散函数调用。",
                    tasks=[
                        PlanningTask(
                            title="接入 Clarify Agent",
                            description="根据项目输入生成澄清问题，并保存问题结果。",
                            owner_focus="Workflow",
                            acceptance_criteria=["可生成 3-5 个问题", "问题结果持久化"],
                        ),
                        PlanningTask(
                            title="接入 PRD Agent",
                            description="基于澄清答案生成结构化 PRD 与 Markdown。",
                            owner_focus="Workflow",
                            acceptance_criteria=["PRD 通过 schema 校验", "支持 Markdown 导出"],
                        ),
                        PlanningTask(
                            title="接入 Planning Agent",
                            description="基于最新 PRD 生成里程碑、任务与发布说明。",
                            owner_focus="Workflow",
                            acceptance_criteria=["Planning 产物可查看", "支持 Markdown 导出"],
                        ),
                    ],
                ),
                PlanningMilestone(
                    title="联调、测试与交付",
                    goal="补齐结果页、导出链路和主链路测试，确保项目适合演示与继续迭代。",
                    tasks=[
                        PlanningTask(
                            title="完成结果页面",
                            description="实现 PRD/Planning 的查看、状态轮询与导出按钮。",
                            owner_focus="前端体验",
                            acceptance_criteria=["页面可访问", "生成状态可追踪"],
                        ),
                        PlanningTask(
                            title="补充测试与 README",
                            description="覆盖主链路 API 与 E2E 测试，并补充运行与部署说明。",
                            owner_focus="质量保障",
                            acceptance_criteria=["主链路测试存在", "README 可指引他人启动"],
                        ),
                    ],
                ),
            ],
            dependencies=[
                "必须先生成并持久化最新 PRD，Planning Agent 才能运行。",
                "前端结果页依赖后端 artifact 与 run status API 稳定返回。",
                *short_answers,
            ],
            testing_focus=[
                "Project -> Clarification -> PRD -> Planning 主链路集成测试",
                "artifact 版本与导出内容一致性测试",
                "前端轮询 run 状态与异常展示测试",
            ],
            rollout_notes=[
                "优先用 mock provider 保证链路完整，再切换真实模型供应商。",
                "演示环境建议使用 PostgreSQL，避免 SQLite 文件状态问题。",
                "Planning 属于扩展能力，需要保持对 v0.1 PRD 主链路的兼容。",
            ],
        )

    def generate_task_breakdown_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        answers: list[str],
    ) -> TaskBreakdownDocument:
        answer_hint = answers[0] if answers else "优先保证主链路、代码可维护性和测试覆盖。"
        _ = planning_document
        return TaskBreakdownDocument(
            delivery_goal=f"围绕 {project.name} 的主链路完成模块任务拆解，并把开发与测试一起前置。",
            sequencing_strategy="按照基础设施 -> 主业务链路 -> Demo 展示层 -> 回归测试与发布检查的顺序推进，每个模块完成后立即验证。",
            modules=[
                TaskBreakdownModule(
                    module_name="项目创建与数据模型",
                    goal="稳定承接用户输入并持久化项目上下文。",
                    user_value="让用户可以可靠创建项目并进入后续 Agent 链路。",
                    tasks=[
                        TaskBreakdownTask(
                            title="完善项目创建表单校验",
                            description="确保项目名称、想法、目标用户和约束条件都能稳定保存。",
                            owner_focus="Frontend + API",
                            dependencies=[],
                            acceptance_criteria=["表单必填项校验完整", "创建成功后可进入澄清页"],
                            test_cases=["验证空值提交被阻止", "验证创建成功后返回项目 ID"],
                        ),
                        TaskBreakdownTask(
                            title="统一 Project / Run / Artifact 关联关系",
                            description="确保后续 PRD、规划、任务拆解和 Demo 都可回溯。",
                            owner_focus="Backend Data",
                            dependencies=["完善项目创建表单校验"],
                            acceptance_criteria=["Run 与 Artifact 可按 project_id 正确查询", "最新产物接口稳定返回"],
                            test_cases=["查询最新 artifact 返回正确版本", "生成失败时 run 状态正确落库"],
                        ),
                    ],
                ),
                TaskBreakdownModule(
                    module_name="PRD 与规划工作流",
                    goal="把澄清结果串成可重复执行的 PRD 与开发规划。",
                    user_value="帮助用户快速得到结构化产品文档，而不是停留在原型想法层。",
                    tasks=[
                        TaskBreakdownTask(
                            title="固化 PRD 生成链路",
                            description="确保从澄清问答到 PRD 的结构化输出持续可用。",
                            owner_focus="Workflow",
                            dependencies=["统一 Project / Run / Artifact 关联关系"],
                            acceptance_criteria=["PRD 生成完成后 artifact 可读取", "PRD Markdown 可导出"],
                            test_cases=["主链路生成 PRD 成功", "导出 PRD Markdown 内容非空"],
                        ),
                        TaskBreakdownTask(
                            title="固化规划生成与容错回退",
                            description=f"围绕“{answer_hint}”强化 responses 优先、chat 后备的容错逻辑。",
                            owner_focus="LLM Provider",
                            dependencies=["固化 PRD 生成链路"],
                            acceptance_criteria=["规划生成失败时有明确错误信息", "网络抖动时可自动回退"],
                            test_cases=["模拟 responses 失败后能回退 chat", "规划 artifact 可正确落库"],
                        ),
                    ],
                ),
                TaskBreakdownModule(
                    module_name="任务拆解与 Demo Agent",
                    goal="新增多 Agent 扩展能力，把规划继续拆成模块任务，并自动生成可展示 Demo。",
                    user_value="让项目从文档产物升级为可演示成果，更适合简历和作品集。",
                    tasks=[
                        TaskBreakdownTask(
                            title="实现 Task Breakdown Agent",
                            description="基于 PRD 与规划输出模块、子任务、验收标准和测试清单。",
                            owner_focus="Multi-Agent",
                            dependencies=["固化规划生成与容错回退"],
                            acceptance_criteria=["至少生成 3 个模块", "每个模块含任务、验收和测试用例"],
                            test_cases=["任务拆解 artifact 可读取", "Markdown 导出成功"],
                        ),
                        TaskBreakdownTask(
                            title="实现 Demo Generator Agent",
                            description="自动生成适合面试展示的 Demo 蓝图，并提供前端可视化页面。",
                            owner_focus="Multi-Agent + Frontend",
                            dependencies=["实现 Task Breakdown Agent"],
                            acceptance_criteria=["Demo 页面可展示 Hero、屏幕流和 Agent 分工", "Demo Markdown 可导出"],
                            test_cases=["Demo artifact 可读取", "前端 Demo 页面渲染至少 3 个 screen"],
                        ),
                    ],
                ),
            ],
            integration_risks=[
                "真实 LLM Provider 在高峰期可能出现响应超时，需要回退与重试策略。",
                "多 Agent 输出结构不稳定时需要统一 JSON schema 与兜底合并逻辑。",
                "前端展示页若缺少空态处理，用户会误判生成为失败。",
            ],
            qa_strategy=[
                "后端优先用 mock provider 做全链路回归测试。",
                "关键节点均保留 artifact 接口与 markdown 导出断言。",
                "前端使用 E2E 覆盖从 PRD 到 Demo 的完整主链路。",
            ],
            release_checklist=[
                "确认最新 PRD、规划、任务拆解、Demo 四类 artifact 都能读取。",
                "确认导出按钮和下载文件名正确。",
                "确认异常时页面会展示明确错误信息。",
            ],
        )

    def generate_demo_blueprint_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        task_breakdown_document: TaskBreakdownDocument,
        answers: list[str],
    ) -> DemoBlueprintDocument:
        active_answer = answers[0] if answers else "需要一套适合面试展示的交互式 Demo。"
        _ = prd_document, planning_document, task_breakdown_document
        return DemoBlueprintDocument(
            product_name=project.name,
            demo_goal="向面试官清晰展示：用户如何从一个想法出发，逐步获得 PRD、规划、任务拆解和可演示 Demo。",
            hero_title=f"{project.name}：从模糊想法到可交付方案",
            hero_subtitle="一个面向 AI 产品经理与独立开发者的多 Agent 产品交付工作台，兼顾文档生成、任务拆解与 Demo 展示。",
            target_persona=project.target_user,
            primary_cta="开始一次完整生成",
            secondary_cta="查看多 Agent 分工",
            key_metrics=["10 分钟生成结构化 PRD", "主链路全程可导出", "每个阶段都可回看 artifact"],
            screens=[
                DemoScreen(
                    name="Clarify Workspace",
                    purpose="补齐产品背景与约束，形成高质量输入。",
                    headline="先问清楚，再生成文档",
                    description="系统根据项目想法自动生成澄清问题，用户补充答案后即可进入 PRD 生成阶段。",
                    highlights=["自动生成 3-5 个关键澄清问题", "支持保存答案并重复进入页面", f"围绕“{active_answer}”动态补充背景"],
                    actions=[
                        DemoScreenAction(label="生成澄清问题", detail="触发 Clarify Agent，快速拉起产品背景问答。", result_preview="结果台出现 4 个高价值澄清问题。"),
                        DemoScreenAction(label="保存澄清答案", detail="把答案持久化，供 PRD 与后续 Agent 使用。", result_preview="页面提示答案已同步到 PRD 生成链路。"),
                    ],
                    sample_inputs=["项目名称", "目标用户", "约束条件"],
                    sample_outputs=["澄清问题列表", "已保存答案数", "下一步状态提示"],
                    success_signal="用户明确知道自己已经具备生成 PRD 的足够上下文。",
                ),
                DemoScreen(
                    name="PRD Studio",
                    purpose="基于澄清答案输出结构化 PRD。",
                    headline="把想法沉淀成结构化产品文档",
                    description="PRD Agent 输出问题定义、目标用户、MVP 边界、用户故事和成功指标。",
                    highlights=["一键生成结构化 PRD", "支持 Markdown 导出", "保留范围边界与风险项"],
                    actions=[
                        DemoScreenAction(label="生成 PRD", detail="根据项目输入和澄清结果生成首版 PRD。", result_preview="文档区展示目标用户、核心场景和 MVP 目标。"),
                        DemoScreenAction(label="导出 Markdown", detail="导出适合 GitHub 和文档平台同步的 Markdown 文本。", result_preview="浏览器开始下载 PRD Markdown 文件。"),
                    ],
                    sample_inputs=["澄清答案摘要", "初始产品想法", "目标用户画像"],
                    sample_outputs=["产品摘要", "In Scope / Out of Scope", "Success Metrics"],
                    success_signal="用户拿到一份能继续推进开发和展示的首版 PRD。",
                ),
                DemoScreen(
                    name="Execution Planner",
                    purpose="把 PRD 继续转成开发规划与任务地图。",
                    headline="从文档走向交付计划",
                    description="Planning Agent 与 Task Breakdown Agent 协同输出里程碑、模块任务、验收标准和测试清单。",
                    highlights=["规划与任务拆解联动生成", "每个任务都附带验收标准", "测试思维前置到模块级"],
                    actions=[
                        DemoScreenAction(label="生成开发规划", detail="输出阶段目标、任务负责方向和发布说明。", result_preview="规划面板展示 3 个里程碑与关键任务。"),
                        DemoScreenAction(label="拆解模块任务", detail="将规划进一步拆到模块、任务、依赖与测试用例。", result_preview="任务地图出现模块卡片与验收标准清单。"),
                    ],
                    sample_inputs=["PRD JSON", "计划目标", "主链路优先级"],
                    sample_outputs=["里程碑列表", "模块任务树", "测试清单"],
                    success_signal="团队可以直接按模块推进开发，而不是停留在抽象想法阶段。",
                ),
                DemoScreen(
                    name="Demo Studio",
                    purpose="向面试官或用户展示整个多 Agent 交付链路。",
                    headline="一个可互动的多 Agent Demo 面板",
                    description="前端以交互原型方式展示每个 screen、每个 action 的即时反馈，并可查看 Agent Prompt 摘要。",
                    highlights=["点击 action 即可看到模拟结果", "多 Agent 运行状态可视化", "适合作品集与 GitHub 展示"],
                    actions=[
                        DemoScreenAction(label="切换 Demo Screen", detail="按 flow step 或 Hero CTA 快速切换当前演示页面。", result_preview="原型区切换到对应 screen，右侧同步更新结果台。"),
                        DemoScreenAction(label="展开 Agent Prompt", detail="查看每个 Agent 的职责、依赖和 Prompt 摘要。", result_preview="Agent 运行面板展开，显示 system/user prompt preview。"),
                    ],
                    sample_inputs=["当前项目 artifact", "Demo flow step", "Agent prompt preview"],
                    sample_outputs=["交互式页面预览", "结果台反馈", "Agent 运行状态"],
                    success_signal="面试官能在 2-3 分钟内直观看懂产品价值与多 Agent 分工。",
                ),
            ],
            flow_steps=[
                DemoFlowStep(step_title="澄清需求", user_goal="补齐产品背景，避免空泛 PRD。", system_response="Clarify Agent 输出问题并保存答案。"),
                DemoFlowStep(step_title="生成 PRD", user_goal="拿到一份结构化、可导出的产品文档。", system_response="PRD Agent 产出目标用户、场景、边界与成功指标。"),
                DemoFlowStep(step_title="规划与拆解", user_goal="把文档继续转成开发计划和模块任务。", system_response="Planning / Task Breakdown Agents 输出里程碑、依赖和测试点。"),
                DemoFlowStep(step_title="展示 Demo", user_goal="快速向面试官、协作者或用户演示整个链路。", system_response="Demo Generator 输出交互原型和多 Agent 运行面板。"),
            ],
            agent_cards=[
                DemoAgentCard(agent_name="Product Strategist Agent", responsibility="定义 Demo 目标、Hero 文案与关键指标。", prompt_focus="强调产品价值、求职展示价值和商业化表达。", output_summary="生成 Demo 目标、Hero 标题、副标题和关键指标。", status="completed", depends_on=[], system_prompt_preview="You are the Product Strategist Agent.", user_prompt_preview=f"Project: {project.name}; target user: {project.target_user}", model_used=DEFAULT_MOCK_MODEL),
                DemoAgentCard(agent_name="UX Prototype Agent", responsibility="输出 Demo screen、交互动作、样例输入输出和成功信号。", prompt_focus="强调页面结构清晰、交互可演示、适合前端直接渲染。", output_summary="生成 4 个 screen，并为每个 action 附加 result preview。", status="completed", depends_on=["Product Strategist Agent"], system_prompt_preview="You are the UX Prototype Agent.", user_prompt_preview="Generate interactive showcase screens with previews.", model_used=DEFAULT_MOCK_MODEL),
                DemoAgentCard(agent_name="Demo Narrative Agent", responsibility="组织演示脚本、流程步骤和面试讲述顺序。", prompt_focus="强调讲解节奏、故事线和对外展示表达。", output_summary="生成 4 步 demo flow 和面试话术。", status="completed", depends_on=["Product Strategist Agent", "UX Prototype Agent"], system_prompt_preview="You are the Demo Narrative Agent.", user_prompt_preview="Organize the story for a 2-3 minute showcase.", model_used=DEFAULT_MOCK_MODEL),
            ],
            demo_script=[
                "先用一句话说明 BuildFlow AI 解决的问题：把模糊产品想法变成结构化交付链路。",
                "再展示澄清问题与 PRD 生成，让面试官看到系统如何把输入结构化。",
                "随后切换到开发规划与任务拆解，强调可维护性、测试前置和多 Agent 协作。",
                "最后打开 Demo Studio 与 Agent 运行面板，展示这个项目为何适合写进简历与作品集。",
            ],
        )


class AliyunBailianLLMProvider(LLMProvider):
    def __init__(self, settings: Settings):
        if not settings.dashscope_api_key:
            raise ValueError("bailian_api_key_required")
        if OpenAI is None:
            raise ValueError("bailian_sdk_not_installed")

        self.settings = settings
        self.model = _resolve_bailian_model(settings)
        self.api_mode = settings.llm_api_mode
        self.chat_client = OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_chat_base_url or DEFAULT_BAILIAN_CHAT_BASE_URL, timeout=DEFAULT_BAILIAN_CHAT_TIMEOUT_SECONDS, max_retries=DEFAULT_BAILIAN_CHAT_MAX_RETRIES)
        self.responses_client = OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_responses_base_url or DEFAULT_BAILIAN_RESPONSES_BASE_URL, timeout=DEFAULT_BAILIAN_RESPONSES_TIMEOUT_SECONDS, max_retries=DEFAULT_BAILIAN_RESPONSES_MAX_RETRIES)

    def generate_clarification_questions(self, project: ProjectRead) -> list[str]:
        user_prompt = build_clarification_prompt(project.name, project.idea, project.target_user, project.constraints)
        system_prompt = "You are BuildFlow Clarification Agent. Generate 3 to 5 high-value clarification questions and return strict JSON only."
        document = self._generate_structured_document(system_prompt, user_prompt, ClarificationQuestionsDocument)
        return document.questions

    def generate_prd_document(self, project: ProjectRead, answers: list[str]) -> PRDDocument:
        user_prompt = build_prd_prompt(project.name, project.idea, project.target_user, answers)
        system_prompt = "You are BuildFlow PRD Agent. Turn the product idea and clarifications into a structured PRD and return strict JSON only."
        return self._generate_structured_document(system_prompt, user_prompt, PRDDocument)

    def generate_planning_document(self, project: ProjectRead, prd_document: PRDDocument, answers: list[str]) -> PlanningDocument:
        prd_summary = " | ".join([prd_document.product_summary, prd_document.mvp_goal, *(answers[:2] or [])])
        user_prompt = build_planning_prompt(project.name, prd_summary)
        system_prompt = "You are BuildFlow Planning Agent. Convert the PRD into an execution plan and return strict JSON only."
        return self._generate_structured_document(system_prompt, user_prompt, PlanningDocument)

    def generate_task_breakdown_document(self, project: ProjectRead, prd_document: PRDDocument, planning_document: PlanningDocument, answers: list[str]) -> TaskBreakdownDocument:
        prd_json = prd_document.model_dump_json(indent=2)
        planning_json = planning_document.model_dump_json(indent=2)
        answers_text = " | ".join(answers) if answers else "No extra clarifications"
        architect_user_prompt = build_task_breakdown_architect_prompt(project.name, prd_json, planning_json, answers_text)
        architect_notes = self._generate_structured_document("You are BuildFlow Solution Architect Agent. Break the plan into clear modules and tasks. Return strict JSON only.", architect_user_prompt, TaskBreakdownArchitectNotes)
        delivery_user_prompt = build_task_breakdown_delivery_prompt(project.name, prd_json, planning_json, answers_text)
        delivery_notes = self._generate_structured_document("You are BuildFlow Delivery Manager Agent. Provide sequencing strategy, integration risks and release checklist. Return strict JSON only.", delivery_user_prompt, TaskBreakdownDeliveryNotes)
        qa_user_prompt = build_task_breakdown_qa_prompt(project.name, prd_json, planning_json, answers_text)
        qa_notes = self._generate_structured_document("You are BuildFlow QA Lead Agent. Add acceptance criteria and test cases. Return strict JSON only.", qa_user_prompt, TaskBreakdownQANotes)
        return assemble_task_breakdown_document(architect_notes, delivery_notes, qa_notes)

    def generate_demo_blueprint_document(self, project: ProjectRead, prd_document: PRDDocument, planning_document: PlanningDocument, task_breakdown_document: TaskBreakdownDocument, answers: list[str]) -> DemoBlueprintDocument:
        _ = answers
        demo_context = _build_demo_context_summary(project, prd_document, planning_document, task_breakdown_document, compact=False)
        demo_retry_context = _build_demo_context_summary(project, prd_document, planning_document, task_breakdown_document, compact=True)
        product_system_prompt = "You are BuildFlow Product Strategist Agent. Define the demo goal, hero copy, target persona and key showcase metrics. Return strict JSON only."
        product_user_prompt = build_demo_product_prompt(project.name, demo_context)
        product_retry_prompt = build_demo_product_prompt(project.name, demo_retry_context)
        product_notes = self._generate_structured_document_with_retry(product_system_prompt, product_user_prompt, product_retry_prompt, DemoProductNotes)
        ux_system_prompt = "You are BuildFlow UX Prototype Agent. Translate the product into interactive showcase screens with actions, previews and success signals. Return strict JSON only."
        ux_user_prompt = build_demo_ux_prompt(project.name, demo_context)
        ux_retry_prompt = build_demo_ux_prompt(project.name, demo_retry_context)
        ux_notes = self._generate_structured_document_with_retry(ux_system_prompt, ux_user_prompt, ux_retry_prompt, DemoUXNotes)
        narrative_system_prompt = "You are BuildFlow Demo Narrative Agent. Organize a concise walkthrough, flow steps and talking points. Return strict JSON only."
        narrative_user_prompt = build_demo_narrative_prompt(project.name, demo_context)
        narrative_retry_prompt = build_demo_narrative_prompt(project.name, demo_retry_context)
        narrative_notes = self._generate_structured_document_with_retry(narrative_system_prompt, narrative_user_prompt, narrative_retry_prompt, DemoNarrativeNotes)
        agent_cards = [
            DemoAgentCard(agent_name="Product Strategist Agent", responsibility="定义 Demo 的展示目标、Hero 文案与关键指标。", prompt_focus="产品定位、价值主张、目标人群与展示亮点。", output_summary=product_notes.demo_goal, status="completed", depends_on=[], system_prompt_preview=_prompt_preview(product_system_prompt), user_prompt_preview=_prompt_preview(product_user_prompt), model_used=self.model),
            DemoAgentCard(agent_name="UX Prototype Agent", responsibility="生成 Demo screen、动作、样例输入输出与成功信号。", prompt_focus="确保页面可演示、可交互、适合前端直接渲染。", output_summary=f"生成 {len(ux_notes.screens)} 个可演示 screen。", status="completed", depends_on=["Product Strategist Agent"], system_prompt_preview=_prompt_preview(ux_system_prompt), user_prompt_preview=_prompt_preview(ux_user_prompt), model_used=self.model),
            DemoAgentCard(agent_name="Demo Narrative Agent", responsibility="组织 flow steps 与讲解脚本，形成完整展示故事线。", prompt_focus="突出讲解节奏、产品亮点和多 Agent 协作价值。", output_summary=narrative_notes.demo_script[0], status="completed", depends_on=["Product Strategist Agent", "UX Prototype Agent"], system_prompt_preview=_prompt_preview(narrative_system_prompt), user_prompt_preview=_prompt_preview(narrative_user_prompt), model_used=self.model),
        ]
        return assemble_demo_blueprint_document(project.name, product_notes, ux_notes, narrative_notes, agent_cards)

    def _generate_structured_document_with_retry(self, system_prompt: str, user_prompt: str, retry_user_prompt: str, schema: type[SchemaT]) -> SchemaT:
        try:
            return self._generate_structured_document(system_prompt, user_prompt, schema)
        except ValueError as exc:
            if str(exc) not in TRANSIENT_BAILIAN_ERROR_CODES:
                raise
            retry_system_prompt = system_prompt + " Keep the response concise. Prefer shorter strings and 3-5 items per list while still satisfying the schema."
            return self._parse_with_chat(retry_system_prompt, retry_user_prompt, schema)

    def _generate_structured_document(self, system_prompt: str, user_prompt: str, schema: type[SchemaT]) -> SchemaT:
        if self.api_mode == "responses":
            return self._parse_with_responses(system_prompt, user_prompt, schema)
        if self.api_mode == "chat":
            return self._parse_with_chat(system_prompt, user_prompt, schema)
        if self.api_mode != "auto":
            raise ValueError("llm_api_mode_not_supported")

        try:
            return self._parse_with_responses(system_prompt, user_prompt, schema)
        except ValueError as exc:
            if str(exc) not in RESPONSES_FALLBACK_ERROR_CODES:
                raise
            return self._parse_with_chat(system_prompt, user_prompt, schema)

    def _parse_with_responses(self, system_prompt: str, user_prompt: str, schema: type[SchemaT]) -> SchemaT:
        try:
            response = self.responses_client.responses.create(model=self.model, input=[{"role": "system", "content": system_prompt}, {"role": "user", "content": _build_responses_json_prompt(user_prompt, schema)}])
        except (BadRequestError, NotFoundError) as exc:
            raise ValueError("bailian_responses_unavailable") from exc
        except RateLimitError as exc:
            raise _map_rate_limit_error(exc)
        except AuthenticationError as exc:
            raise ValueError("bailian_auth_failed") from exc
        except PermissionDeniedError as exc:
            raise ValueError("bailian_permission_denied") from exc
        except APITimeoutError as exc:
            raise ValueError("bailian_timeout") from exc
        except APIConnectionError as exc:
            raise ValueError("bailian_request_failed") from exc
        except OpenAIError as exc:
            raise ValueError("bailian_request_failed") from exc

        output_text = getattr(response, "output_text", None)
        if not output_text or not output_text.strip():
            raise ValueError("bailian_empty_response")

        try:
            payload = _extract_json_payload(output_text)
            return schema.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise ValueError("bailian_parse_failed") from exc

    def _parse_with_chat(self, system_prompt: str, user_prompt: str, schema: type[SchemaT]) -> SchemaT:
        try:
            completion = self.chat_client.chat.completions.create(model=self.model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": _build_responses_json_prompt(user_prompt, schema)}])
        except RateLimitError as exc:
            raise _map_rate_limit_error(exc)
        except AuthenticationError as exc:
            raise ValueError("bailian_auth_failed") from exc
        except PermissionDeniedError as exc:
            raise ValueError("bailian_permission_denied") from exc
        except BadRequestError as exc:
            raise ValueError("bailian_bad_request") from exc
        except APITimeoutError as exc:
            raise ValueError("bailian_timeout") from exc
        except APIConnectionError as exc:
            raise ValueError("bailian_request_failed") from exc
        except OpenAIError as exc:
            raise ValueError("bailian_request_failed") from exc

        raw_text = _extract_chat_message_text(completion)
        if not raw_text or not raw_text.strip():
            raise ValueError("bailian_empty_response")

        try:
            payload = _extract_json_payload(raw_text)
            return schema.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise ValueError("bailian_parse_failed") from exc


def _summarize_items(items: list[str], limit: int) -> list[str]:
    return [item.strip() for item in items if item and item.strip()][:limit]


def _build_demo_context_summary(
    project: ProjectRead,
    prd_document: PRDDocument,
    planning_document: PlanningDocument,
    task_breakdown_document: TaskBreakdownDocument,
    compact: bool = False,
) -> str:
    scenario_limit = 2 if compact else 3
    in_scope_limit = 3 if compact else 5
    success_metric_limit = 2 if compact else 4
    milestone_limit = 2 if compact else 3
    milestone_task_limit = 1 if compact else 2
    module_limit = 2 if compact else 3
    module_task_limit = 2 if compact else 3

    lines = [
        f"项目名称: {project.name}",
        f"一句话想法: {project.idea}",
        f"目标用户: {project.target_user}",
        f"平台: {project.platform}",
        "",
        "PRD 摘要:",
        f"- 产品概述: {prd_document.product_summary}",
        f"- 问题陈述: {prd_document.problem_statement}",
        f"- MVP 目标: {prd_document.mvp_goal}",
    ]
    lines.extend(f"- 核心场景: {item}" for item in _summarize_items(prd_document.core_scenarios, scenario_limit))
    lines.extend(f"- 功能范围: {item}" for item in _summarize_items(prd_document.in_scope, in_scope_limit))
    lines.extend(f"- 成功指标: {item}" for item in _summarize_items(prd_document.success_metrics, success_metric_limit))

    lines.extend(["", "开发规划摘要:", f"- 目标: {planning_document.objective}", f"- 交付策略: {planning_document.delivery_strategy}"])
    for milestone in planning_document.milestones[:milestone_limit]:
        lines.append(f"- 里程碑 {milestone.title}: {milestone.goal}")
        for task in milestone.tasks[:milestone_task_limit]:
            lines.append(f"  - 任务 {task.title}: {task.description}")
    lines.extend(f"- 测试重点: {item}" for item in _summarize_items(planning_document.testing_focus, success_metric_limit))

    lines.extend(["", "模块任务拆解摘要:", f"- 交付目标: {task_breakdown_document.delivery_goal}", f"- 排序策略: {task_breakdown_document.sequencing_strategy}"])
    for module in task_breakdown_document.modules[:module_limit]:
        lines.append(f"- 模块 {module.module_name}: {module.goal} | 用户价值: {module.user_value}")
        for task in module.tasks[:module_task_limit]:
            lines.append(f"  - 子任务 {task.title}: {task.description}")
    lines.extend(f"- 发布检查: {item}" for item in _summarize_items(task_breakdown_document.release_checklist, success_metric_limit))

    lines.extend(["", "请只基于以上摘要生成结果，不要复述全部上下文。"])
    return "\n".join(lines)


def _build_responses_json_prompt(user_prompt: str, schema: type[SchemaT]) -> str:
    schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)
    return "\n\n".join(
        [
            user_prompt,
            "请仅输出一个严格合法的 JSON 对象，不要输出 Markdown 代码块，不要添加解释、前缀或后缀。",
            "输出必须满足以下 JSON Schema：",
            schema_json,
        ]
    )


def _extract_json_payload(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    if start == -1:
        raise ValueError("json_object_not_found")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[start : index + 1]
                parsed = json.loads(candidate)
                if not isinstance(parsed, dict):
                    raise ValueError("json_object_not_found")
                return parsed

    raise ValueError("json_object_not_found")


def _extract_chat_message_text(completion: object) -> str:
    choices = getattr(completion, "choices", None)
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                continue

            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)

        return "".join(parts)

    return ""

def _prompt_preview(text: str, limit: int = 320) -> str:
    cleaned = re.sub(r'\s+', ' ', text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + '...'


def _map_rate_limit_error(exc: Exception) -> ValueError:
    error_text = str(exc).lower()
    if getattr(exc, "code", None) == "insufficient_quota" or "insufficient_quota" in error_text:
        return ValueError("bailian_quota_exceeded")
    return ValueError("bailian_rate_limited")


def _split_target_users(target_user: str) -> list[str]:
    users = [item.strip() for item in re.split(r"[、，,;/；]", target_user) if item.strip()]
    return users or [target_user]


def _resolve_bailian_model(settings: Settings) -> str:
    if not settings.llm_model or settings.llm_model == DEFAULT_MOCK_MODEL:
        return DEFAULT_BAILIAN_MODEL
    return settings.llm_model


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    resolved_settings = settings or get_settings()
    if resolved_settings.llm_provider == "mock":
        return MockLLMProvider()
    if resolved_settings.llm_provider == "aliyun_bailian":
        return AliyunBailianLLMProvider(resolved_settings)
    raise ValueError("llm_provider_not_supported")

