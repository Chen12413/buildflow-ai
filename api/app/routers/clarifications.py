from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import raise_http_error
from app.db.session import get_db
from app.repositories.clarification_repository import ClarificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.run_repository import RunRepository
from app.schemas.clarification import ClarificationAnswersSaveRequest, ClarificationQuestionRead
from app.schemas.common import success_response
from app.schemas.run import RunRead
from app.services.clarification_service import ClarificationService

router = APIRouter(prefix="/projects/{project_id}/clarifications", tags=["clarifications"])


@router.post("/generate")
def generate_clarification_questions(project_id: str, db: Session = Depends(get_db)):
    service = ClarificationService(ProjectRepository(db), ClarificationRepository(db), RunRepository(db))
    try:
        run, questions = service.generate_questions(project_id)
    except ValueError as exc:
        raise_http_error(str(exc))
    return success_response(
        {
            "run": RunRead.model_validate(run).model_dump(mode="json"),
            "questions": [ClarificationQuestionRead.model_validate(item).model_dump(mode="json") for item in questions],
        }
    )


@router.put("/answers")
def save_clarification_answers(project_id: str, payload: ClarificationAnswersSaveRequest, db: Session = Depends(get_db)):
    service = ClarificationService(ProjectRepository(db), ClarificationRepository(db), RunRepository(db))
    try:
        saved_rows = service.save_answers(project_id, [item.model_dump() for item in payload.answers])
    except ValueError as exc:
        raise_http_error(str(exc))
    return success_response({"project_id": project_id, "saved_count": len(saved_rows)})
