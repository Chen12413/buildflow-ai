from abc import ABC, abstractmethod

from app.schemas.planning import PlanningDocument
from app.schemas.prd import PRDDocument
from app.schemas.project import ProjectRead


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
