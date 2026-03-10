from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.errors import raise_http_error
from app.db.session import get_db
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.artifact import PRDArtifactRead, PlanningArtifactRead
from app.schemas.common import success_response
from app.services.export_service import ExportService

router = APIRouter(prefix="/projects/{project_id}", tags=["exports"])


@router.get("/artifacts/prd/latest")
def get_latest_prd(project_id: str, db: Session = Depends(get_db)):
    service = ExportService(ProjectRepository(db), ArtifactRepository(db))
    try:
        artifact = service.get_latest_prd(project_id)
    except ValueError as exc:
        raise_http_error(str(exc))
    return success_response(PRDArtifactRead.model_validate(artifact).model_dump(mode="json"))


@router.get("/artifacts/planning/latest")
def get_latest_planning(project_id: str, db: Session = Depends(get_db)):
    service = ExportService(ProjectRepository(db), ArtifactRepository(db))
    try:
        artifact = service.get_latest_planning(project_id)
    except ValueError as exc:
        raise_http_error(str(exc))
    return success_response(PlanningArtifactRead.model_validate(artifact).model_dump(mode="json"))


@router.get("/export/markdown")
def export_prd_markdown(project_id: str, db: Session = Depends(get_db)):
    service = ExportService(ProjectRepository(db), ArtifactRepository(db))
    try:
        artifact = service.get_latest_prd(project_id)
    except ValueError as exc:
        raise_http_error(str(exc))
    filename = f"{project_id}-prd-v{artifact.version}.md"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=artifact.content_markdown, media_type="text/markdown; charset=utf-8", headers=headers)


@router.get("/export/planning/markdown")
def export_planning_markdown(project_id: str, db: Session = Depends(get_db)):
    service = ExportService(ProjectRepository(db), ArtifactRepository(db))
    try:
        artifact = service.get_latest_planning(project_id)
    except ValueError as exc:
        raise_http_error(str(exc))
    filename = f"{project_id}-planning-v{artifact.version}.md"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=artifact.content_markdown, media_type="text/markdown; charset=utf-8", headers=headers)
