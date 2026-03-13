from app.repositories.project_repository import ProjectRepository
import re

from app.schemas.project import ProjectCreate

TRAILING_TIMESTAMP_SUFFIX_REGEX = re.compile(r"\s+\d{8,}$")


def normalize_project_name(name: str) -> str:
    normalized = TRAILING_TIMESTAMP_SUFFIX_REGEX.sub("", name).strip()
    return normalized or name.strip()


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    def create_project(self, payload: ProjectCreate):
        normalized_payload = payload.model_copy(update={"name": normalize_project_name(payload.name)})
        return self.repository.create(normalized_payload)

    def get_project(self, project_id: str):
        return self.repository.get_by_id(project_id)
