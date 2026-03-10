import json
import re
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.prompts.clarification_prompt import build_clarification_prompt
from app.prompts.planning_prompt import build_planning_prompt
from app.prompts.prd_prompt import build_prd_prompt
from app.schemas.planning import PlanningDocument, PlanningMilestone, PlanningTask
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead

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
RESPONSES_FALLBACK_ERROR_CODES = {
    "bailian_empty_response",
    "bailian_parse_failed",
    "bailian_responses_unavailable",
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
        answer_summary = answers[:3] if answers else ["用户尚未补充详细澄清答案，系统基于原始想法生成初版 PRD。"]
        return PRDDocument(
            product_summary=f"{project.name} 是一款面向 {project.target_user} 的 AI 产品交付助手，用于把模糊想法整理为结构化 PRD。",
            problem_statement=f"目标用户缺少稳定、可复用的方法，将“{project.idea}”这类模糊想法快速整理为可执行需求文档。",
            target_users=_split_target_users(project.target_user),
            core_scenarios=[
                f"围绕“{project.idea}”快速创建项目草案",
                "通过澄清问答补齐关键背景与边界",
                "导出 Markdown 并进入开发协作流程",
            ],
            mvp_goal="让用户在 10 分钟内从产品想法得到一份结构化 PRD。",
            in_scope=[
                "项目创建",
                "澄清问题生成",
                "澄清答案保存",
                "PRD 生成与 Markdown 导出",
            ],
            out_of_scope=[
                "技术架构自动生成",
                "任务拆解自动生成",
                "测试计划自动生成",
            ],
            user_stories=[
                f"作为 {project.target_user}，我希望快速得到一份结构化 PRD，以便继续推进产品落地。",
                "作为项目发起人，我希望导出 Markdown，以便同步到 GitHub 或团队文档平台。",
            ],
            success_metrics=[
                "PRD 生成成功率 > 90%",
                "首版 PRD 输出时间 < 10 分钟",
                "用户无需从零手写 PRD",
            ],
            risks=[
                *answer_summary,
                "如果输入信息过少，PRD 可能偏泛，需要继续迭代补充。",
            ],
        )

    def generate_planning_document(self, project: ProjectRead, prd_document: PRDDocument, answers: list[str]) -> PlanningDocument:
        short_answers = answers[:2] if answers else ["澄清信息有限，规划基于最新 PRD 自动生成。"]
        scope_items = prd_document.in_scope[:4]
        return PlanningDocument(
            objective=f"围绕 {project.name} 的 v0.1 能力，形成一份可执行的开发与验证计划。",
            delivery_strategy="按基础工程、Agent 工作流、前后端联调与交付验证三段推进，每段都要求可运行、可验证、可回滚。",
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
                    goal="将 Clarify、PRD、Planning 三个 Agent 串成可观测工作流，而不是零散函数调用。",
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
                    goal="补齐结果页、导出链路和主流程测试，确保项目适合演示与继续迭代。",
                    tasks=[
                        PlanningTask(
                            title="完成前端结果页",
                            description="实现 PRD/Planning 的查看、状态轮询与导出按钮。",
                            owner_focus="前端体验",
                            acceptance_criteria=["页面可渲染", "生成状态可追踪"],
                        ),
                        PlanningTask(
                            title="补测试与 README",
                            description="覆盖主链路 API 测试，并补充运行与部署说明。",
                            owner_focus="质量保障",
                            acceptance_criteria=["主链路测试存在", "README 可指导他人启动"],
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
                "优先以 mock provider 保证链路完整，再切换真实模型供应商。",
                "演示环境建议使用 PostgreSQL，避免 SQLite 文件状态问题。",
                "Planning 属于扩展能力，需要保持对 v0.1 PRD 主链路的兼容。",
            ],
        )


class AliyunBailianLLMProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.dashscope_api_key:
            raise ValueError("bailian_api_key_required")
        if OpenAI is None:
            raise ValueError("bailian_dependency_missing")

        self.model = _resolve_bailian_model(settings)
        self.api_mode = settings.llm_api_mode
        self.responses_client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_responses_base_url or DEFAULT_BAILIAN_RESPONSES_BASE_URL,
        )
        self.chat_client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_chat_base_url or DEFAULT_BAILIAN_CHAT_BASE_URL,
        )

    def generate_clarification_questions(self, project: ProjectRead) -> list[str]:
        prompt = build_clarification_prompt(project.name, project.idea, project.target_user, project.constraints)
        document = self._generate_structured_document(
            system_prompt=(
                "你是一名资深 AI 产品经理。请只输出 3 到 5 个高信息增益的澄清问题，"
                "问题要直接服务于后续 PRD 生成，避免空泛、重复或一次提多个问题。"
                "输出必须是简体中文，并严格遵循给定结构。"
            ),
            user_prompt=prompt,
            schema=ClarificationQuestionsDocument,
        )
        questions = [item.strip() for item in document.questions if item.strip()]
        if len(questions) < 3:
            raise ValueError("bailian_parse_failed")
        return questions[:5]

    def generate_prd_document(self, project: ProjectRead, answers: list[str]) -> PRDDocument:
        prompt = "\n\n".join(
            [
                build_prd_prompt(project.name, project.idea, project.target_user, answers),
                f"Platform: {project.platform.value}",
                f"Constraints: {project.constraints or 'None'}",
            ]
        )
        return self._generate_structured_document(
            system_prompt=(
                "你是一名资深 AI 产品经理。请基于项目描述和澄清答案输出一份适合 MVP 的结构化 PRD。"
                "要求内容具体、可执行、边界清晰，避免套话，输出必须是简体中文。"
            ),
            user_prompt=prompt,
            schema=PRDDocument,
        )

    def generate_planning_document(self, project: ProjectRead, prd_document: PRDDocument, answers: list[str]) -> PlanningDocument:
        answers_text = " | ".join(answers) if answers else "None"
        prompt = "\n\n".join(
            [
                build_planning_prompt(project.name, prd_document.product_summary),
                f"PRD JSON:\n{prd_document.model_dump_json(indent=2)}",
                f"Clarification Answers: {answers_text}",
            ]
        )
        return self._generate_structured_document(
            system_prompt=(
                "你是一名兼顾交付与质量的技术负责人。请基于 PRD 输出一份 v0.1 实施计划，"
                "明确里程碑、任务、验收标准、测试重点和发布说明。输出必须是简体中文。"
            ),
            user_prompt=prompt,
            schema=PlanningDocument,
        )

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
            response = self.responses_client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": _build_responses_json_prompt(user_prompt, schema),
                    },
                ],
            )
        except (BadRequestError, NotFoundError) as exc:
            raise ValueError("bailian_responses_unavailable") from exc
        except RateLimitError as exc:
            raise _map_rate_limit_error(exc)
        except AuthenticationError as exc:
            raise ValueError("bailian_auth_failed") from exc
        except PermissionDeniedError as exc:
            raise ValueError("bailian_permission_denied") from exc
        except (APIConnectionError, APITimeoutError, OpenAIError) as exc:
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
            completion = self.chat_client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=schema,
            )
        except RateLimitError as exc:
            raise _map_rate_limit_error(exc)
        except AuthenticationError as exc:
            raise ValueError("bailian_auth_failed") from exc
        except PermissionDeniedError as exc:
            raise ValueError("bailian_permission_denied") from exc
        except BadRequestError as exc:
            raise ValueError("bailian_bad_request") from exc
        except (APIConnectionError, APITimeoutError, OpenAIError) as exc:
            raise ValueError("bailian_request_failed") from exc

        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("bailian_empty_response")
        return parsed


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