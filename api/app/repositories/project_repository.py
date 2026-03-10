from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: ProjectCreate) -> Project:
        project = Project(**payload.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)
