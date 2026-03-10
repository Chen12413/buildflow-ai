from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    def create_project(self, payload: ProjectCreate):
        return self.repository.create(payload)

    def get_project(self, project_id: str):
        return self.repository.get_by_id(project_id)
