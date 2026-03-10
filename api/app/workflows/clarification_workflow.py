from app.llm.provider import get_llm_provider
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.schemas.project import ProjectRead
from app.schemas.run import RunStatus, RunType


class ClarificationWorkflow:
    def __init__(self, project_repository: ProjectRepository, clarification_repository: ClarificationRepository, run_repository: RunRepository) -> None:
        self.project_repository = project_repository
        self.clarification_repository = clarification_repository
        self.run_repository = run_repository

    def run(self, project_id: str):
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise ValueError("project_not_found")

        existing_questions = self.clarification_repository.list_questions(project_id)
        if existing_questions:
            run = self.run_repository.create(
                project_id=project_id,
                run_type=RunType.CLARIFICATION_GENERATION,
                status=RunStatus.COMPLETED,
            )
            return run, existing_questions

        run = self.run_repository.create(project_id=project_id, run_type=RunType.CLARIFICATION_GENERATION, status=RunStatus.RUNNING)
        try:
            project_read = ProjectRead.model_validate(project)
            provider = get_llm_provider()
            questions = provider.generate_clarification_questions(project_read)
            rows = self.clarification_repository.replace_questions(project_id, questions)
            run = self.run_repository.update_status(run, RunStatus.COMPLETED)
            return run, rows
        except Exception as exc:
            self.run_repository.update_status(run, RunStatus.FAILED, str(exc))
            raise
