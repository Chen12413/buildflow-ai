def build_task_breakdown_architect_prompt(project_name: str, prd_json: str, planning_json: str, answers_text: str) -> str:
    return "\n\n".join(
        [
            f"项目名称: {project_name}",
            "你是 Solution Architect Agent，负责把 PRD 与开发规划转换成模块边界清晰的任务地图。",
            "请输出 3-6 个模块，每个模块都要包含目标、用户价值和 2-4 个任务。",
            "任务要关注可交付性，不要输出空泛建议。",
            f"PRD JSON:\n{prd_json}",
            f"Planning JSON:\n{planning_json}",
            f"澄清问答摘要: {answers_text}",
        ]
    )


def build_task_breakdown_delivery_prompt(project_name: str, prd_json: str, planning_json: str, answers_text: str) -> str:
    return "\n\n".join(
        [
            f"项目名称: {project_name}",
            "你是 Delivery Manager Agent，负责输出排期策略、跨模块风险和发布检查清单。",
            "请站在一天内做出高质量 MVP 的角度，强调先后顺序、回归验证和发布把控。",
            f"PRD JSON:\n{prd_json}",
            f"Planning JSON:\n{planning_json}",
            f"澄清问答摘要: {answers_text}",
        ]
    )


def build_task_breakdown_qa_prompt(project_name: str, prd_json: str, planning_json: str, answers_text: str) -> str:
    return "\n\n".join(
        [
            f"项目名称: {project_name}",
            "你是 QA Lead Agent，负责为模块任务补齐验收标准与测试点。",
            "请给出面向主链路的验收标准和测试用例，优先覆盖创建项目、生成产物、导出、异常提示。",
            f"PRD JSON:\n{prd_json}",
            f"Planning JSON:\n{planning_json}",
            f"澄清问答摘要: {answers_text}",
        ]
    )
