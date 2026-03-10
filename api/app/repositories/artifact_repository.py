from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.artifact import Artifact


class ArtifactRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, project_id: str, run_id: str, artifact_type: str, content_json: dict, content_markdown: str) -> Artifact:
        next_version = self.get_next_version(project_id, artifact_type)
        artifact = Artifact(
            project_id=project_id,
            run_id=run_id,
            type=artifact_type,
            content_json=content_json,
            content_markdown=content_markdown,
            version=next_version,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def get_latest(self, project_id: str, artifact_type: str) -> Artifact | None:
        stmt = (
            select(Artifact)
            .where(Artifact.project_id == project_id, Artifact.type == artifact_type)
            .order_by(desc(Artifact.version))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_next_version(self, project_id: str, artifact_type: str) -> int:
        stmt = select(func.max(Artifact.version)).where(Artifact.project_id == project_id, Artifact.type == artifact_type)
        current_version = self.db.scalar(stmt)
        return (current_version or 0) + 1
