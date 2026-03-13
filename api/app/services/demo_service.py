from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.schemas.run import RunStatus, RunType
from app.workflows.demo_workflow import DemoWorkflow


class DemoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.project_repository = ProjectRepository(db)
        self.run_repository = RunRepository(db)

    def start_generation(self, project_id: str, background_tasks: BackgroundTasks):
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise ValueError("project_not_found")
        run = self.run_repository.create(project_id=project_id, run_type=RunType.DEMO_GENERATION, status=RunStatus.PENDING)
        background_tasks.add_task(run_demo_generation_task, run.id, project_id)
        return run


def run_demo_generation_task(run_id: str, project_id: str) -> None:
    db = SessionLocal()
    try:
        workflow = DemoWorkflow(
            project_repository=ProjectRepository(db),
            clarification_repository=ClarificationRepository(db),
            artifact_repository=ArtifactRepository(db),
            run_repository=RunRepository(db),
        )
        workflow.run(run_id=run_id, project_id=project_id)
    finally:
        db.close()
