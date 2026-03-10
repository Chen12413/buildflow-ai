from datetime import datetime

from pydantic import BaseModel, Field


class ClarificationQuestionRead(BaseModel):
    id: str
    project_id: str
    question: str
    order_index: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ClarificationGenerateResult(BaseModel):
    run: dict
    questions: list[ClarificationQuestionRead]


class ClarificationAnswerInput(BaseModel):
    question_id: str
    answer: str = Field(min_length=1, max_length=2000)


class ClarificationAnswersSaveRequest(BaseModel):
    answers: list[ClarificationAnswerInput]


class ClarificationAnswersSaveResponse(BaseModel):
    project_id: str
    saved_count: int
