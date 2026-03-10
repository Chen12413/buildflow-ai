def build_prd_prompt(project_name: str, idea: str, target_user: str, answers: list[str]) -> str:
    return (
        f"Project: {project_name}\n"
        f"Idea: {idea}\n"
        f"Target User: {target_user}\n"
        f"Clarifications: {' | '.join(answers) if answers else 'None'}\n"
        "Return a structured PRD document as JSON."
    )
