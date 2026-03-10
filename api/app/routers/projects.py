from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import raise_http_error
from app.db.session import get_db
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import success_response
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    service = ProjectService(ProjectRepository(db))
    project = service.create_project(payload)
    return success_response(ProjectRead.model_validate(project).model_dump(mode="json"))


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(ProjectRepository(db))
    project = service.get_project(project_id)
    if project is None:
        raise_http_error("project_not_found")
    return success_response(ProjectRead.model_validate(project).model_dump(mode="json"))
