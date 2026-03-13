from abc import ABC, abstractmethod

from app.schemas.demo import DemoBlueprintDocument
from app.schemas.planning import PlanningDocument
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead
from app.schemas.task_breakdown import TaskBreakdownDocument


class LLMProvider(ABC):
    @abstractmethod
    def generate_clarification_questions(self, project: ProjectRead) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def generate_prd_document(self, project: ProjectRead, answers: list[str]) -> PRDDocument:
        raise NotImplementedError

    @abstractmethod
    def generate_planning_document(self, project: ProjectRead, prd_document: PRDDocument, answers: list[str]) -> PlanningDocument:
        raise NotImplementedError

    @abstractmethod
    def generate_task_breakdown_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        answers: list[str],
    ) -> TaskBreakdownDocument:
        raise NotImplementedError

    @abstractmethod
    def generate_demo_blueprint_document(
        self,
        project: ProjectRead,
        prd_document: PRDDocument,
        planning_document: PlanningDocument,
        task_breakdown_document: TaskBreakdownDocument,
        answers: list[str],
    ) -> DemoBlueprintDocument:
        raise NotImplementedError
