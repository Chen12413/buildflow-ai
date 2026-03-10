def build_clarification_prompt(project_name: str, idea: str, target_user: str, constraints: str | None) -> str:
    return (
        f"Project: {project_name}\n"
        f"Idea: {idea}\n"
        f"Target User: {target_user}\n"
        f"Constraints: {constraints or 'None'}\n"
        "Return 3 to 5 high-value clarification questions as JSON."
    )
