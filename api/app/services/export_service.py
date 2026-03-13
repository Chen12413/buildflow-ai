from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.artifact import ArtifactType


class ExportService:
    def __init__(self, project_repository: ProjectRepository, artifact_repository: ArtifactRepository) -> None:
        self.project_repository = project_repository
        self.artifact_repository = artifact_repository

    def get_latest_prd(self, project_id: str):
        return self.get_latest_artifact(project_id, ArtifactType.PRD)

    def get_latest_planning(self, project_id: str):
        return self.get_latest_artifact(project_id, ArtifactType.PLANNING)

    def get_latest_task_breakdown(self, project_id: str):
        return self.get_latest_artifact(project_id, ArtifactType.TASK_BREAKDOWN)

    def get_latest_demo(self, project_id: str):
        return self.get_latest_artifact(project_id, ArtifactType.DEMO)

    def get_latest_artifact(self, project_id: str, artifact_type: ArtifactType):
        project = self.project_repository.get_by_id(project_id)
        if project is None:
            raise ValueError("project_not_found")
        artifact = self.artifact_repository.get_latest(project_id, artifact_type.value)
        if artifact is None:
            raise ValueError("artifact_not_found")
        return artifact
