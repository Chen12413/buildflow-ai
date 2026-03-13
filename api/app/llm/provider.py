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
        context = self._build_mock_product_context(project, [])
        if context["domain"] == "travel":
            return [
                f"{project.name} 当前最优先要覆盖的出行场景是什么？例如周末短途、3 天 2 晚自由行或亲子出游。",
                "用户生成行程时最在意哪些约束？例如预算上限、景点密度、拍照/美食偏好、步行距离或节奏松紧。",
                f"{project.name} 的 v0.1 是否需要同时输出每日路线、预算拆分、旅行清单和注意事项？",
                f"在约束“{context['constraint_text']}”下，{project.name} 最先要打磨的成功体验是什么？",
            ]

        return [
            f"{project.name} 当前最优先要解决的用户痛点是什么？",
            f"{project.target_user} 会在什么场景下高频使用 {project.name}？",
            f"{project.name} 的 v0.1 最小可用功能边界应该保留哪些能力？",
            f"在约束“{context['constraint_text']}”下，{project.name} 的成功标准是什么？",
        ]

    def generate_prd_document(self, project: ProjectRead, answers: list[str]) -> PRDDocument:
        context = self._build_mock_product_context(project, answers)
        if context["domain"] == "travel":
            return self._build_mock_travel_prd_document(project, context)
        return self._build_mock_generic_prd_document(project, context)

    def generate_planning_document(self, project: ProjectRead, prd_document: PRDDocument, answers: list[str]) -> PlanningDocument:
        context = self._build_mock_product_context(project, answers)
        if context["domain"] == "travel":
            return self._build_mock_travel_planning_document(project, prd_document, context)
        return self._build_mock_generic_planning_document(project, prd_document, context)

    def generate_task_breakdown_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        answers: list[str],
    ) -> TaskBreakdownDocument:
        context = self._build_mock_product_context(project, answers)
        if context["domain"] == "travel":
            return self._build_mock_travel_task_breakdown_document(project, prd_document, planning_document, context)
        return self._build_mock_generic_task_breakdown_document(project, prd_document, planning_document, context)

    def generate_demo_blueprint_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        task_breakdown_document: TaskBreakdownDocument,
        answers: list[str],
    ) -> DemoBlueprintDocument:
        context = self._build_mock_product_context(project, answers)
        if context["domain"] == "travel":
            return self._build_mock_travel_demo_blueprint_document(project, prd_document, planning_document, task_breakdown_document, context)
        return self._build_mock_generic_demo_blueprint_document(project, prd_document, planning_document, task_breakdown_document, context)

    def _build_mock_product_context(self, project: ProjectRead, answers: list[str]) -> dict[str, object]:
        combined_text = " ".join(
            filter(
                None,
                [project.name, project.idea, project.target_user, project.constraints or "", *answers],
            )
        ).lower()
        target_users = _split_target_users(project.target_user)
        answer_summary = answers[:3] if answers else ["用户尚未补充详细澄清答案，系统基于初始想法生成首版内容。"]
        planning_answers = answers[:2] if answers else ["澄清信息有限，当前内容基于首版 PRD 自动生成。"]
        platform_label = {
            "web": "Web",
            "mobile": "移动端",
            "both": "Web + Mobile",
        }.get(str(project.platform), "Web")
        primary_persona = target_users[0] if target_users else project.target_user
        constraint_text = project.constraints or "暂无额外约束"
        is_travel = any(
            keyword in combined_text
            for keyword in ["旅游", "旅行", "行程", "自由行", "出游", "trip", "travel", "itinerary", "destination"]
        )
        return {
            "domain": "travel" if is_travel else "generic",
            "target_users": target_users,
            "answer_summary": answer_summary,
            "planning_answers": planning_answers,
            "platform_label": platform_label,
            "primary_persona": primary_persona,
            "constraint_text": constraint_text,
        }

    def _build_mock_travel_prd_document(self, project: ProjectRead, context: dict[str, object]) -> PRDDocument:
        target_users = context["target_users"]
        answer_summary = context["answer_summary"]
        primary_persona = context["primary_persona"]
        platform_label = context["platform_label"]
        constraint_text = context["constraint_text"]
        return PRDDocument(
            product_summary=f"{project.name} 是一款面向 {project.target_user} 的 AI 旅游规划产品，帮助用户根据目的地、天数、预算和偏好快速生成可执行的每日行程。",
            problem_statement="自由行用户做攻略时通常需要在景点筛选、路线安排、预算控制和节奏平衡之间反复切换，手动整理成本高且信息容易分散。",
            target_users=target_users,
            core_scenarios=[
                "输入目的地、出行天数、预算区间和旅行偏好，快速得到首版行程建议。",
                "根据美食、拍照、亲子、轻松或特种兵等节奏偏好，微调每日路线和停留顺序。",
                "查看每日安排、预算拆分、旅行清单和注意事项，再决定是否导出分享。",
            ],
            mvp_goal=f"让 {primary_persona} 在 {platform_label} 上用 3 分钟得到一份可执行的旅行行程方案。",
            in_scope=["旅行需求输入", "AI 行程生成", "每日路线展示", "预算拆分与清单建议", "结果导出与分享"],
            out_of_scope=["实时机酒预订", "实时地图导航", "跨国签证办理", "多城市复杂联运优化"],
            user_stories=[
                f"作为 {primary_persona}，我希望输入目的地和预算后立即得到可执行行程，而不是自己从零做攻略。",
                "作为旅行决策者，我希望系统告诉我每天去哪、预计花多少钱、路线是否顺畅。",
                "作为第一次去陌生城市的用户，我希望在结果里同时看到注意事项、打包建议和时间分配。",
            ],
            success_metrics=["首版行程生成时间 < 30 秒", "用户 3 分钟内拿到可执行方案", "预算建议可读且按天展示", "至少 80% 的测试用户认为方案可以直接作为出行草稿"],
            risks=[*answer_summary, f"当前约束“{constraint_text}”可能压缩首版功能范围，需要先聚焦高频出行场景。"],
        )

    def _build_mock_generic_prd_document(self, project: ProjectRead, context: dict[str, object]) -> PRDDocument:
        target_users = context["target_users"]
        answer_summary = context["answer_summary"]
        primary_persona = context["primary_persona"]
        constraint_text = context["constraint_text"]
        return PRDDocument(
            product_summary=f"{project.name} 是一款面向 {project.target_user} 的 AI 产品，帮助用户围绕“{project.idea}”快速得到结构化方案和可执行结果。",
            problem_statement=f"{project.target_user} 在处理“{project.idea}”相关任务时，往往需要在信息整理、方案比较和执行落地之间频繁切换，效率低且结果不稳定。",
            target_users=target_users,
            core_scenarios=[
                "输入目标、限制条件和偏好，快速得到首版解决方案。",
                "基于反馈迭代结果，持续收敛到更可执行的版本。",
                "导出结果并分享给协作者或真实用户继续验证。",
            ],
            mvp_goal=f"让 {primary_persona} 在 10 分钟内从想法得到一份可演示的产品方案。",
            in_scope=["需求输入", "AI 方案生成", "结果解释", "二次编辑", "导出分享"],
            out_of_scope=["完整生产部署", "复杂组织权限系统", "高成本实时数据接入"],
            user_stories=[
                f"作为 {primary_persona}，我希望只输入最关键的信息就能得到首版方案。",
                "作为产品推进者，我希望系统能把抽象想法转成可讨论、可演示的结果。",
                "作为协作者，我希望结果能够被分享、复用和继续迭代。",
            ],
            success_metrics=["首版结果输出时间 < 2 分钟", "核心流程一次通过率 > 90%", "用户无需从零开始整理方案"],
            risks=[*answer_summary, f"当前约束“{constraint_text}”如果变化较大，后续需要继续迭代功能边界。"],
        )
    def _build_mock_travel_planning_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        context: dict[str, object],
    ) -> PlanningDocument:
        planning_answers = context["planning_answers"]
        platform_label = context["platform_label"]
        return PlanningDocument(
            objective=f"围绕 {project.name} 的 v0.1 旅游规划 MVP，形成一套可在 {platform_label} 上交付和验证的开发计划。",
            delivery_strategy="按照需求输入建模 -> 行程生成引擎 -> 结果展示与微调 -> 演示验收四个阶段推进，每段都要求可运行、可验证、可回滚。",
            milestones=[
                PlanningMilestone(
                    title="需求输入与约束建模",
                    goal="先把目的地、天数、预算、出游偏好等信息结构化，保证后续生成逻辑稳定可复用。",
                    tasks=[
                        PlanningTask(
                            title="定义旅行需求输入模型",
                            description="明确目的地、出行日期、预算、偏好标签、节奏和禁忌项等字段。",
                            owner_focus="产品设计 + 后端 Schema",
                            acceptance_criteria=["表单字段能覆盖首版场景", "输入参数可以稳定透传到生成链路"],
                        ),
                        PlanningTask(
                            title="完成创建项目与澄清链路联调",
                            description="保证用户创建项目后，可以围绕旅行场景补齐关键需求并进入 PRD 阶段。",
                            owner_focus="Frontend + API",
                            acceptance_criteria=["项目创建成功可进入澄清页", "澄清答案保存后可触发 PRD 生成"],
                        ),
                    ],
                ),
                PlanningMilestone(
                    title="行程生成与结果呈现",
                    goal="把结构化输入转成可执行的每日路线、预算建议和旅行说明。",
                    tasks=[
                        PlanningTask(
                            title="实现首版行程生成服务",
                            description="基于目的地、预算和偏好输出按天组织的路线、时段安排和推荐理由。",
                            owner_focus="LLM Workflow",
                            acceptance_criteria=["能生成至少 3 天行程样例", "输出结构适合前端分屏展示"],
                        ),
                        PlanningTask(
                            title="完成行程结果页",
                            description="展示每日路线、亮点景点、预算拆分、注意事项和可点击的微调入口。",
                            owner_focus="Frontend Experience",
                            acceptance_criteria=["结果页可读性稳定", "支持展示预算、清单与每日详情"],
                        ),
                    ],
                ),
                PlanningMilestone(
                    title="微调、演示与质量验收",
                    goal="让用户能够调整行程方案，并把结果作为真实可演示 Demo 对外展示。",
                    tasks=[
                        PlanningTask(
                            title="增加偏好微调与重生成入口",
                            description="支持用户改成慢节奏、美食优先、拍照优先或更严格预算后再次生成。",
                            owner_focus="Product + Workflow",
                            acceptance_criteria=["至少支持 3 种常见偏好切换", "重生成后结果可继续浏览"],
                        ),
                        PlanningTask(
                            title="补齐测试与展示素材",
                            description="覆盖主链路测试、Demo 页面走查和展示截图，为 GitHub 与作品集准备素材。",
                            owner_focus="QA + DX",
                            acceptance_criteria=["主链路测试通过", "展示图能体现真实旅游规划产品体验"],
                        ),
                    ],
                ),
            ],
            dependencies=[
                "必须先确定 v0.1 只覆盖单目的地、短天数、高频出行场景。",
                "行程生成输出必须与预算、路线和清单使用同一份结构化结果。",
                *planning_answers,
            ],
            testing_focus=[
                "项目创建 -> 澄清 -> PRD -> Planning 主链路集成测试",
                "行程结构化输出与前端展示一致性测试",
                "偏好微调、重生成和错误提示可用性测试",
            ],
            rollout_notes=[
                "先用 mock provider 保证旅游规划链路完整，再切换真实模型供应商。",
                "首版只承诺展示 AI 生成方案，不直接承诺实时预订与地图导航。",
                "上线展示环境应优先保证响应稳定和错误提示友好。",
            ],
        )

    def _build_mock_generic_planning_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        context: dict[str, object],
    ) -> PlanningDocument:
        planning_answers = context["planning_answers"]
        scope_items = prd_document.in_scope[:4]
        return PlanningDocument(
            objective=f"围绕 {project.name} 的 v0.1 能力，形成一份可执行的开发与验证计划。",
            delivery_strategy="按照基础工程、核心业务链路、演示体验与验收交付三阶段推进，每段都要求可运行、可验证、可回滚。",
            milestones=[
                PlanningMilestone(
                    title="基础工程与数据模型",
                    goal="先稳定项目骨架、核心实体和基础 API，为后续产品能力提供清晰边界。",
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
                    title="核心业务链路",
                    goal="把关键输入、AI 生成和结果展示串成稳定可回放的工作流。",
                    tasks=[
                        PlanningTask(
                            title="固化主流程接口",
                            description="确保从用户输入到结果产出的关键 API 都具备稳定契约。",
                            owner_focus="API 设计",
                            acceptance_criteria=["主流程接口可串联", "结构化产物可追踪"],
                        ),
                        PlanningTask(
                            title="补齐前端结果页",
                            description="让用户能读取结构化结果、查看关键信息并继续操作。",
                            owner_focus="Frontend UX",
                            acceptance_criteria=["关键结果页可读", "空态和异常态可理解"],
                        ),
                    ],
                ),
                PlanningMilestone(
                    title="演示验收与发布准备",
                    goal="补齐测试、文档和展示素材，让项目具备作品集价值。",
                    tasks=[
                        PlanningTask(
                            title="增加自动化验证",
                            description="补齐核心测试、构建检查和长任务状态验证。",
                            owner_focus="QA",
                            acceptance_criteria=["核心测试通过", "构建可重复执行"],
                        ),
                        PlanningTask(
                            title="准备展示素材",
                            description="整理 README、截图、亮点文案和对外演示路径。",
                            owner_focus="DX + Showcase",
                            acceptance_criteria=["仓库可公开展示", "项目亮点表达清晰"],
                        ),
                    ],
                ),
            ],
            dependencies=[
                "必须先生成并持久化最新 PRD，规划阶段才能稳定推进。",
                "前端结果页依赖后端 artifact 与 run status API 稳定返回。",
                *planning_answers,
            ],
            testing_focus=[
                "主链路集成测试",
                "artifact 版本与导出内容一致性测试",
                "前端轮询 run 状态与异常展示测试",
            ],
            rollout_notes=[
                "优先用 mock provider 保证链路完整，再切换真实模型供应商。",
                "演示环境建议使用 PostgreSQL，避免 SQLite 文件状态问题。",
                "新增能力要保持对主链路的兼容。",
            ],
        )
    def _build_mock_travel_task_breakdown_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        context: dict[str, object],
    ) -> TaskBreakdownDocument:
        _ = prd_document, planning_document
        answer_hint = context["planning_answers"][0]
        return TaskBreakdownDocument(
            delivery_goal=f"围绕 {project.name} 完成 AI 旅游规划 MVP 的模块拆解，并把开发、测试和演示素材一起前置。",
            sequencing_strategy="按照需求采集 -> 行程生成 -> 结果展示与微调 -> Demo 走查与回归测试的顺序推进，每个模块完成后立即验证。",
            modules=[
                TaskBreakdownModule(
                    module_name="旅行需求采集",
                    goal="稳定收集目的地、预算、天数和偏好，为生成链路提供清晰输入。",
                    user_value="用户能快速表达自己的旅行需求，而不是在表单里反复试错。",
                    tasks=[
                        TaskBreakdownTask(
                            title="完善旅行需求表单",
                            description="支持目的地、出行天数、预算区间、出游偏好和节奏标签输入。",
                            owner_focus="Frontend + API",
                            dependencies=[],
                            acceptance_criteria=["核心字段可提交", "表单错误提示简洁易懂"],
                            test_cases=["验证缺少目的地时不能提交", "验证创建成功后进入澄清页"],
                        ),
                        TaskBreakdownTask(
                            title="统一旅行上下文存储",
                            description="保证项目、运行记录和生成产物都能按 project_id 回溯。",
                            owner_focus="Backend Data",
                            dependencies=["完善旅行需求表单"],
                            acceptance_criteria=["项目可查询最新运行结果", "产物版本切换稳定"],
                            test_cases=["查询最新 artifact 返回正确版本", "失败运行状态可正确落库"],
                        ),
                    ],
                ),
                TaskBreakdownModule(
                    module_name="行程生成与结果解释",
                    goal="输出按天组织的旅行方案，并让结果对用户可读、可比较、可修改。",
                    user_value="用户可以快速拿到能直接参考的出行路线，而不是只有一段泛泛建议。",
                    tasks=[
                        TaskBreakdownTask(
                            title="实现行程生成链路",
                            description="基于旅行需求输出每日路线、推荐理由、预算建议和注意事项。",
                            owner_focus="Workflow",
                            dependencies=["统一旅行上下文存储"],
                            acceptance_criteria=["至少生成 3 个结构化结果区块", "结果可供前端分屏展示"],
                            test_cases=["主链路生成 PRD 和规划成功", "行程结果内容非空且结构化"],
                        ),
                        TaskBreakdownTask(
                            title="补齐偏好微调与回退策略",
                            description=f"围绕“{answer_hint}”优化重生成体验，并在 LLM 波动时提供可理解的回退提示。",
                            owner_focus="LLM Provider + UX",
                            dependencies=["实现行程生成链路"],
                            acceptance_criteria=["微调后可重新生成结果", "失败时错误提示对普通用户可理解"],
                            test_cases=["模拟 provider 超时后展示友好错误", "重试后可恢复结果展示"],
                        ),
                    ],
                ),
                TaskBreakdownModule(
                    module_name="Demo 展示与质量保障",
                    goal="把旅游规划产品体验包装成可展示 Demo，并补齐测试和截图素材。",
                    user_value="用户、面试官和协作者可以直接看到最终产品体验，而不是只看到文档。",
                    tasks=[
                        TaskBreakdownTask(
                            title="生成旅游产品 Demo 蓝图",
                            description="产出需求输入、行程方案、每日详情和预算清单等 Demo 屏幕。",
                            owner_focus="Multi-Agent",
                            dependencies=["补齐偏好微调与回退策略"],
                            acceptance_criteria=["至少生成 4 个屏幕", "Demo 能体现真实旅游产品价值"],
                            test_cases=["Demo artifact 可读取", "前端 Demo 页面渲染至少 4 个 screen"],
                        ),
                        TaskBreakdownTask(
                            title="补齐回归测试与展示截图",
                            description="覆盖从创建项目到 Demo 的完整主链路，并生成 GitHub 可展示素材。",
                            owner_focus="QA + Showcase",
                            dependencies=["生成旅游产品 Demo 蓝图"],
                            acceptance_criteria=["主链路测试通过", "截图体现 AI 旅游规划案例"],
                            test_cases=["Playwright 流程走通", "截图文件生成成功"],
                        ),
                    ],
                ),
            ],
            integration_risks=[
                "真实 LLM Provider 在高峰期可能出现响应超时，需要回退与重试策略。",
                "旅行结果如果结构不稳定，前端展示容易出现空态或错位。",
                "若预算、路线和注意事项来源不一致，用户会降低对结果的信任。",
            ],
            qa_strategy=[
                "后端优先用 mock provider 做全链路回归测试。",
                "关键节点均保留 artifact 接口与 Markdown 导出断言。",
                "前端使用 E2E 覆盖从 PRD 到旅游 Demo 的完整主链路。",
            ],
            release_checklist=[
                "确认最新 PRD、规划、任务拆解、Demo 四类 artifact 都能读取。",
                "确认 Demo 中展示的是目标产品，而不是 BuildFlow 自身功能。",
                "确认异常时页面会展示明确、用户可理解的错误信息。",
            ],
        )

    def _build_mock_generic_task_breakdown_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        context: dict[str, object],
    ) -> TaskBreakdownDocument:
        _ = prd_document, planning_document
        answer_hint = context["planning_answers"][0]
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
                    module_name="主业务链路与结果展示",
                    goal="把输入结果串成可重复执行的产品主流程。",
                    user_value="帮助用户快速得到结构化结果，而不是停留在抽象想法层。",
                    tasks=[
                        TaskBreakdownTask(
                            title="固化主链路生成流程",
                            description="确保从输入到结果的结构化输出持续可用。",
                            owner_focus="Workflow",
                            dependencies=["统一 Project / Run / Artifact 关联关系"],
                            acceptance_criteria=["主流程完成后 artifact 可读取", "Markdown 可导出"],
                            test_cases=["主链路生成成功", "导出 Markdown 内容非空"],
                        ),
                        TaskBreakdownTask(
                            title="固化容错回退",
                            description=f"围绕“{answer_hint}”强化 responses 优先、chat 后备的容错逻辑。",
                            owner_focus="LLM Provider",
                            dependencies=["固化主链路生成流程"],
                            acceptance_criteria=["生成失败时有明确错误信息", "网络抖动时可自动回退"],
                            test_cases=["模拟 responses 失败后能回退 chat", "artifact 可正确落库"],
                        ),
                    ],
                ),
                TaskBreakdownModule(
                    module_name="Demo 展示与质量保障",
                    goal="把结果进一步包装成可展示成果，更适合简历和作品集。",
                    user_value="让项目从文档产物升级为可演示成果。",
                    tasks=[
                        TaskBreakdownTask(
                            title="生成目标产品 Demo",
                            description="自动生成适合面试展示的 Demo 蓝图，并提供前端可视化页面。",
                            owner_focus="Multi-Agent + Frontend",
                            dependencies=["固化容错回退"],
                            acceptance_criteria=["Demo 页面可展示核心屏幕和 Agent 分工", "Demo Markdown 可导出"],
                            test_cases=["Demo artifact 可读取", "前端 Demo 页面渲染至少 3 个 screen"],
                        ),
                        TaskBreakdownTask(
                            title="补齐回归测试与展示素材",
                            description="覆盖主链路并生成对外可展示的截图与文案。",
                            owner_focus="QA + Showcase",
                            dependencies=["生成目标产品 Demo"],
                            acceptance_criteria=["主链路测试通过", "GitHub 素材更新完成"],
                            test_cases=["E2E 流程走通", "截图文件生成成功"],
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
                "前端使用 E2E 覆盖从主链路到 Demo 的完整流程。",
            ],
            release_checklist=[
                "确认最新 PRD、规划、任务拆解、Demo 四类 artifact 都能读取。",
                "确认导出按钮和下载文件名正确。",
                "确认异常时页面会展示明确错误信息。",
            ],
        )
    def _build_mock_travel_demo_blueprint_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        task_breakdown_document: TaskBreakdownDocument,
        context: dict[str, object],
    ) -> DemoBlueprintDocument:
        _ = prd_document, planning_document, task_breakdown_document
        primary_persona = context["primary_persona"]
        return DemoBlueprintDocument(
            product_name=project.name,
            demo_goal="向面试官、协作者或真实用户展示：如何把一个 AI 旅游规划想法推进成真正可演示的产品体验。",
            hero_title=f"{project.name}：输入偏好，生成可执行旅行方案",
            hero_subtitle="用户输入目的地、天数、预算和旅行偏好后，系统生成首版行程、每日路线、预算建议和出行清单，并支持继续微调。",
            target_persona=str(primary_persona),
            primary_cta="查看示例行程",
            secondary_cta="查看 Agent 分工",
            key_metrics=["30 秒生成首版行程", "按天展示路线与预算", "支持偏好微调与结果重生成"],
            screens=[
                DemoScreen(
                    name="行程需求输入",
                    purpose="帮助用户快速输入目的地、天数、预算和偏好。",
                    headline="先说清楚你想怎么旅行",
                    description="页面聚焦最少必要输入，减少用户做攻略前的准备负担。",
                    highlights=["目的地、天数、预算一次输入", "支持美食/拍照/亲子/慢节奏等偏好", "可补充特殊约束与禁忌项"],
                    actions=[
                        DemoScreenAction(label="填写东京 3 天 2 晚", detail="输入目的地、预算区间和偏好，准备生成首版行程。", result_preview="系统记录东京、3 天 2 晚、预算 3000-5000 元、拍照 + 美食优先。"),
                        DemoScreenAction(label="切换成周末短途模式", detail="把场景改成 2 天 1 晚周边游，验证输入模型的灵活性。", result_preview="系统把行程节奏切换为周末短途模式，并降低每日景点数量。"),
                    ],
                    sample_inputs=["目的地：东京", "天数：3 天 2 晚", "预算：3000-5000 元", "偏好：拍照、美食、轻松节奏"],
                    sample_outputs=["结构化旅行需求", "可用于生成的偏好标签", "首版行程请求参数"],
                    success_signal="用户可以在 1 分钟内完成需求输入，并愿意继续生成行程。",
                ),
                DemoScreen(
                    name="首版行程方案",
                    purpose="展示 AI 生成的旅行方案总览。",
                    headline="先拿到一份可以直接参考的行程",
                    description="结果区给出按天组织的路线、亮点景点、推荐理由和节奏说明。",
                    highlights=["按天展示路线结构", "给出每一天的核心亮点", "为每段推荐附上简短理由"],
                    actions=[
                        DemoScreenAction(label="生成首版东京路线", detail="根据用户输入直接生成 3 天 2 晚首版行程。", result_preview="页面展示 Day 1 浅草寺-晴空塔、Day 2 银座-东京塔、Day 3 涩谷-代官山等路线建议。"),
                        DemoScreenAction(label="改成美食优先", detail="在不改变总天数的前提下，提升餐饮和夜间行程比重。", result_preview="系统重排路线，把筑地、居酒屋和夜景安排加入每日计划。"),
                    ],
                    sample_inputs=["旅行需求 JSON", "偏好标签", "预算区间"],
                    sample_outputs=["按天行程总览", "核心景点列表", "推荐理由与节奏说明"],
                    success_signal="用户看到首版方案后，认为这已经不是抽象建议，而是可继续执行的草稿。",
                ),
                DemoScreen(
                    name="每日路线详情",
                    purpose="帮助用户查看单日安排、时间分配和出行逻辑。",
                    headline="每一天怎么走、为什么这样排，一眼看懂",
                    description="系统把每日路线拆到上午/下午/晚上，并补充交通、停留时长与注意事项。",
                    highlights=["按时段拆分每日安排", "展示交通与停留建议", "支持查看替代路线和雨天方案"],
                    actions=[
                        DemoScreenAction(label="展开 Day 2 详情", detail="查看银座、东京塔、六本木一整天的节奏安排。", result_preview="页面展开 Day 2：上午银座逛街，中午寿司，傍晚东京塔，晚上六本木夜景。"),
                        DemoScreenAction(label="切换雨天备选方案", detail="模拟下雨场景，查看室内替代路线。", result_preview="系统建议将户外拍照景点替换为美术馆、商场和展望台等室内路线。"),
                    ],
                    sample_inputs=["单日路线", "天气条件", "节奏偏好"],
                    sample_outputs=["分时段日程", "交通建议", "备选路线"],
                    success_signal="用户可以基于单日详情直接安排当天行动，而不是继续回到外部攻略站搜索。",
                ),
                DemoScreen(
                    name="预算与出行清单",
                    purpose="把预算控制、准备事项和导出动作放在同一页，方便用户做最终决策。",
                    headline="预算够不够、需要带什么、能不能直接分享",
                    description="系统汇总预算拆分、出行清单、注意事项和导出能力，形成可带走的旅行方案。",
                    highlights=["预算按天与按类别拆分", "自动生成出行清单", "支持导出与分享给同行人"],
                    actions=[
                        DemoScreenAction(label="查看预算拆分", detail="展示交通、餐饮、门票和住宿的预计花费。", result_preview="系统显示预算拆分：住宿 1800、餐饮 900、交通 400、门票与杂项 600 元。"),
                        DemoScreenAction(label="下载旅行清单", detail="导出打包清单、注意事项和简版路线，方便临出发查看。", result_preview="页面提示已生成旅行清单：证件、充电器、舒适鞋、防晒、常用药品与离线地图。"),
                    ],
                    sample_inputs=["预算规则", "每日路线结果", "用户出行方式"],
                    sample_outputs=["预算拆分卡片", "旅行清单", "可分享的行程摘要"],
                    success_signal="用户愿意把结果分享给同行人，说明这个 Demo 已接近真实产品体验。",
                ),
            ],
            flow_steps=[
                DemoFlowStep(step_title="输入旅行需求", user_goal="快速表达目的地、预算和偏好。", system_response="需求采集 Agent 将输入整理成结构化旅行约束。"),
                DemoFlowStep(step_title="生成首版行程", user_goal="拿到一份可直接参考的旅行方案。", system_response="Itinerary Agent 输出按天组织的路线、推荐理由和预算建议。"),
                DemoFlowStep(step_title="查看每日详情", user_goal="确认每天怎么走、遇到变化怎么办。", system_response="Experience Agent 展示分时段路线、替代方案和注意事项。"),
                DemoFlowStep(step_title="确认预算与清单", user_goal="判断方案是否可执行，并准备出发。", system_response="Delivery Agent 汇总预算拆分、清单和分享导出结果。"),
            ],
            agent_cards=[
                DemoAgentCard(agent_name="Travel Product Agent", responsibility="把旅行需求整理成可生成的产品输入与约束。", prompt_focus="强调目的地、预算、天数、偏好和禁止项的结构化表达。", output_summary="生成结构化旅行需求、关键约束和首版生成参数。", status="completed", depends_on=[], system_prompt_preview="You are the Travel Product Agent.", user_prompt_preview=f"Project: {project.name}; target user: {project.target_user}", model_used=DEFAULT_MOCK_MODEL),
                DemoAgentCard(agent_name="Itinerary Planner Agent", responsibility="输出按天行程、每日路线、预算建议和推荐理由。", prompt_focus="强调路线可执行性、节奏平衡和结果可读性。", output_summary="生成首版行程总览、单日详情和预算建议。", status="completed", depends_on=["Travel Product Agent"], system_prompt_preview="You are the Itinerary Planner Agent.", user_prompt_preview="Generate a travel itinerary with daily routes, budgets and rationale.", model_used=DEFAULT_MOCK_MODEL),
                DemoAgentCard(agent_name="Travel Experience Agent", responsibility="补充替代路线、旅行清单、导出结果和演示讲述顺序。", prompt_focus="强调真实用户体验、展示质量和对外沟通表达。", output_summary="生成预算清单页、导出结果和 2-3 分钟演示话术。", status="completed", depends_on=["Travel Product Agent", "Itinerary Planner Agent"], system_prompt_preview="You are the Travel Experience Agent.", user_prompt_preview="Organize the showcase for a portfolio-friendly travel product demo.", model_used=DEFAULT_MOCK_MODEL),
            ],
            demo_script=[
                "先展示用户只输入目的地、天数、预算和偏好，系统如何快速收集旅行需求。",
                "再点击生成首版行程，让面试官看到系统会产出按天组织的路线、推荐理由和预算建议。",
                "继续切到每日详情和预算清单，说明这已经是用户真正可用的旅游规划产品体验，而不是抽象工作流。",
                "最后展开 Agent 分工，说明 BuildFlow AI 如何把一个想法一路推进成这个 AI 旅游规划 Demo。",
            ],
        )

    def _build_mock_generic_demo_blueprint_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        task_breakdown_document: TaskBreakdownDocument,
        context: dict[str, object],
    ) -> DemoBlueprintDocument:
        _ = prd_document, planning_document, task_breakdown_document
        primary_persona = context["primary_persona"]
        return DemoBlueprintDocument(
            product_name=project.name,
            demo_goal="向面试官、协作者或真实用户展示：如何把一个产品想法推进成真正可演示的目标产品体验。",
            hero_title=f"{project.name}：从想法到可演示产品体验",
            hero_subtitle="系统围绕用户输入生成结构化结果、关键页面和演示话术，帮助项目快速完成首版对外展示。",
            target_persona=str(primary_persona),
            primary_cta="查看核心流程",
            secondary_cta="查看 Agent 分工",
            key_metrics=["快速生成首版结果", "支持继续迭代和微调", "可导出并用于对外展示"],
            screens=[
                DemoScreen(
                    name="需求输入",
                    purpose="帮助用户说明目标、约束和偏好。",
                    headline="先把问题说清楚",
                    description="页面聚焦最少必要输入，确保系统可以生成可靠的首版结果。",
                    highlights=["输入目标和边界", "保留关键偏好", "快速进入生成阶段"],
                    actions=[
                        DemoScreenAction(label="填写核心需求", detail="录入目标、限制条件和成功标准。", result_preview="系统记录核心目标、边界条件和优先级。"),
                        DemoScreenAction(label="切换场景模板", detail="在高频场景之间切换，验证输入模型适配性。", result_preview="页面加载对应场景的推荐字段和默认约束。"),
                    ],
                    sample_inputs=["目标描述", "约束条件", "用户偏好"],
                    sample_outputs=["结构化输入", "首版生成参数"],
                    success_signal="用户愿意继续点击下一步，说明输入门槛足够低。",
                ),
                DemoScreen(
                    name="方案总览",
                    purpose="展示系统生成的首版产品方案。",
                    headline="先拿到一份能讨论的结果",
                    description="页面呈现系统输出的核心方案、重点模块和推荐理由。",
                    highlights=["结果结构清晰", "重点内容可快速扫描", "适合作为首版方案继续讨论"],
                    actions=[
                        DemoScreenAction(label="生成首版方案", detail="基于当前输入快速生成结构化结果。", result_preview="系统输出首版方案、关键模块和优先级建议。"),
                        DemoScreenAction(label="改成保守方案", detail="压缩范围和复杂度，查看更稳妥的版本。", result_preview="系统返回更聚焦的 MVP 方案，并降低非核心能力占比。"),
                    ],
                    sample_inputs=["结构化输入", "生成参数"],
                    sample_outputs=["首版方案", "关键模块", "优先级建议"],
                    success_signal="用户能立刻说出这套方案要先做什么。",
                ),
                DemoScreen(
                    name="结果详情",
                    purpose="帮助用户查看更细的分步结果与说明。",
                    headline="细节展开后仍然讲得通",
                    description="页面拆解核心结果、操作步骤和补充说明，让方案更易落地。",
                    highlights=["支持分步展示", "每项结果都有解释", "可查看替代路径"],
                    actions=[
                        DemoScreenAction(label="展开模块详情", detail="查看模块目标、职责和验收点。", result_preview="页面展开每个模块的交付目标、依赖和测试点。"),
                        DemoScreenAction(label="查看替代路径", detail="切换到更轻量的执行方式。", result_preview="系统展示更精简的备选路径和对应权衡。"),
                    ],
                    sample_inputs=["首版方案", "细节参数"],
                    sample_outputs=["模块详情", "替代路径"],
                    success_signal="用户可以把页面内容直接拿去沟通或继续开发。",
                ),
                DemoScreen(
                    name="导出与分享",
                    purpose="把结果包装成可交付、可分享、可展示的产物。",
                    headline="不仅能生成，还能带走和展示",
                    description="页面汇总导出、分享、清单和演示入口，形成完整的对外展示闭环。",
                    highlights=["支持导出结果", "便于分享给协作者", "适合作品集展示"],
                    actions=[
                        DemoScreenAction(label="导出结果摘要", detail="把当前方案导出为可复用文档。", result_preview="系统生成可分享的结构化摘要与链接。"),
                        DemoScreenAction(label="打开演示模式", detail="进入适合面试或作品集展示的视图。", result_preview="页面切换到展示模式，并同步展示 Agent 分工。"),
                    ],
                    sample_inputs=["当前结果", "导出配置"],
                    sample_outputs=["结构化摘要", "分享链接", "展示模式视图"],
                    success_signal="协作者或面试官能快速看懂这是什么产品、有什么价值。",
                ),
            ],
            flow_steps=[
                DemoFlowStep(step_title="输入需求", user_goal="快速表达目标和边界。", system_response="Input Agent 整理结构化需求。"),
                DemoFlowStep(step_title="生成方案", user_goal="拿到首版可讨论结果。", system_response="Solution Agent 输出核心方案与理由。"),
                DemoFlowStep(step_title="查看详情", user_goal="确认细节是否足够落地。", system_response="Detail Agent 展开模块说明和替代路径。"),
                DemoFlowStep(step_title="导出展示", user_goal="把结果用于协作或展示。", system_response="Delivery Agent 汇总导出结果与演示脚本。"),
            ],
            agent_cards=[
                DemoAgentCard(agent_name="Product Strategy Agent", responsibility="把用户目标整理成可执行输入与价值主张。", prompt_focus="强调产品目标、约束条件和用户价值。", output_summary="生成结构化需求、目标用户和关键约束。", status="completed", depends_on=[], system_prompt_preview="You are the Product Strategy Agent.", user_prompt_preview=f"Project: {project.name}; target user: {project.target_user}", model_used=DEFAULT_MOCK_MODEL),
                DemoAgentCard(agent_name="Solution Design Agent", responsibility="输出首版方案、核心模块和执行路径。", prompt_focus="强调结果结构、优先级和可落地性。", output_summary="生成首版方案和关键模块。", status="completed", depends_on=["Product Strategy Agent"], system_prompt_preview="You are the Solution Design Agent.", user_prompt_preview="Generate a product-ready solution blueprint.", model_used=DEFAULT_MOCK_MODEL),
                DemoAgentCard(agent_name="Showcase Agent", responsibility="组织展示页面、导出结果和演示脚本。", prompt_focus="强调对外表达、页面可演示性和作品集友好度。", output_summary="生成展示屏幕、导出入口和演示话术。", status="completed", depends_on=["Product Strategy Agent", "Solution Design Agent"], system_prompt_preview="You are the Showcase Agent.", user_prompt_preview="Turn the product results into a portfolio-friendly demo narrative.", model_used=DEFAULT_MOCK_MODEL),
            ],
            demo_script=[
                "先展示用户如何用最少输入描述需求和约束。",
                "再生成首版方案，强调系统输出的是可以继续推进的产品结果。",
                "继续展开详情与导出页面，让对方看到这不是一次性答案，而是可交付成果。",
                "最后展示 Agent 分工，说明 BuildFlow AI 如何帮助用户把想法快速推进成产品 Demo。",
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

