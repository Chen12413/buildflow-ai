def build_demo_product_prompt(project_name: str, demo_context: str) -> str:
    return "\n\n".join(
        [
            f"项目名称: {project_name}",
            "你是 Product Strategist Agent，负责定义产品 Demo 的展示目标、价值主张、目标用户和关键指标。",
            "请输出适合求职展示、GitHub 展示和产品经理面试演示的文案。",
            "要求：表达简洁，不复述全部上下文，每个列表控制在 3-5 项。",
            "上下文摘要:",
            demo_context,
        ]
    )


def build_demo_ux_prompt(project_name: str, demo_context: str) -> str:
    return "\n\n".join(
        [
            f"项目名称: {project_name}",
            "你是 UX Prototype Agent，负责把产品能力转成可演示的页面与交互。",
            "请输出 3-4 个 Demo screen，每个 screen 必须包含 purpose、headline、description、highlights、actions。",
            "每个 action 额外输出 result_preview；每个 screen 额外输出 sample_inputs、sample_outputs、success_signal。",
            "要求：优先核心主链路，信息要短、清晰、适合前端直接渲染。",
            "上下文摘要:",
            demo_context,
        ]
    )


def build_demo_narrative_prompt(project_name: str, demo_context: str) -> str:
    return "\n\n".join(
        [
            f"项目名称: {project_name}",
            "你是 Demo Narrative Agent，负责产出演示脚本和用户体验流程。",
            "请输出 3-5 个 flow step，以及一份适合产品经理面试演示的 demo script。",
            "要求：突出讲解节奏、产品价值、多 Agent 协作与交付闭环。",
            "上下文摘要:",
            demo_context,
        ]
    )