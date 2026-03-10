from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.errors import raise_http_error
from app.db.session import get_db
from app.schemas.common import success_response
from app.schemas.run import RunRead
from app.services.planning_service import PlanningService

router = APIRouter(prefix="/projects/{project_id}/planning", tags=["planning"])


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_planning(project_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    service = PlanningService(db)
    try:
        run = service.start_generation(project_id, background_tasks)
    except ValueError as exc:
        raise_http_error(str(exc))
    return success_response({"run": RunRead.model_validate(run).model_dump(mode="json")})
