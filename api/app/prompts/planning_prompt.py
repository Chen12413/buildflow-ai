def build_planning_prompt(project_name: str, prd_summary: str) -> str:
    return (
        f"Project: {project_name}\n"
        f"PRD Summary: {prd_summary}\n"
        "Return a structured execution planning document as JSON."
    )
