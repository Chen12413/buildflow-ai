from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.workflows.clarification_workflow import ClarificationWorkflow


class ClarificationService:
    def __init__(self, project_repository: ProjectRepository, clarification_repository: ClarificationRepository, run_repository: RunRepository) -> None:
        self.project_repository = project_repository
        self.clarification_repository = clarification_repository
        self.run_repository = run_repository

    def generate_questions(self, project_id: str):
        workflow = ClarificationWorkflow(
            project_repository=self.project_repository,
            clarification_repository=self.clarification_repository,
            run_repository=self.run_repository,
        )
        return workflow.run(project_id)

    def save_answers(self, project_id: str, answers: list[dict[str, str]]):
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise ValueError("project_not_found")
        return self.clarification_repository.replace_answers(project_id, answers)
