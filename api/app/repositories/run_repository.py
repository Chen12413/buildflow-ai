from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.run import Run
from app.schemas.run import RunStatus, RunType


class RunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, project_id: str, run_type: RunType, status: RunStatus = RunStatus.PENDING) -> Run:
        run = Run(project_id=project_id, type=run_type.value, status=status.value)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: str) -> Run | None:
        return self.db.get(Run, run_id)

    def update_status(self, run: Run, status: RunStatus, error_message: str | None = None) -> Run:
        run.status = status.value
        run.error_message = error_message
        if status in {RunStatus.COMPLETED, RunStatus.FAILED}:
            run.completed_at = datetime.now(timezone.utc)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
