from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import raise_http_error
from app.db.session import get_db
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.run_repository import RunRepository
from app.schemas.artifact import ArtifactType
from app.schemas.common import success_response
from app.schemas.run import RunRead

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = RunRepository(db).get_by_id(run_id)
    if run is None:
        raise_http_error("run_not_found")

    artifact_ready = False
    if run.status == "completed":
        artifact_type_by_run = {
            "prd_generation": ArtifactType.PRD.value,
            "planning_generation": ArtifactType.PLANNING.value,
        }
        artifact_type = artifact_type_by_run.get(run.type)
        if artifact_type is not None:
            artifact_ready = ArtifactRepository(db).get_latest(run.project_id, artifact_type) is not None

    return success_response(RunRead.model_validate(run).model_dump(mode="json"), meta={"artifact_ready": artifact_ready})
