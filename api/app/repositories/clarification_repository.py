from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.clarification import ClarificationAnswer, ClarificationQuestion


class ClarificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def replace_questions(self, project_id: str, questions: list[str]) -> list[ClarificationQuestion]:
        self.db.execute(delete(ClarificationQuestion).where(ClarificationQuestion.project_id == project_id))
        question_rows = [
            ClarificationQuestion(project_id=project_id, question=question, order_index=index)
            for index, question in enumerate(questions, start=1)
        ]
        self.db.add_all(question_rows)
        self.db.commit()
        for row in question_rows:
            self.db.refresh(row)
        return question_rows

    def list_questions(self, project_id: str) -> list[ClarificationQuestion]:
        stmt = select(ClarificationQuestion).where(ClarificationQuestion.project_id == project_id).order_by(ClarificationQuestion.order_index.asc())
        return list(self.db.scalars(stmt).all())

    def replace_answers(self, project_id: str, answers: list[dict[str, str]]) -> list[ClarificationAnswer]:
        self.db.execute(delete(ClarificationAnswer).where(ClarificationAnswer.project_id == project_id))
        answer_rows = [
            ClarificationAnswer(project_id=project_id, question_id=item["question_id"], answer=item["answer"])
            for item in answers
        ]
        self.db.add_all(answer_rows)
        self.db.commit()
        for row in answer_rows:
            self.db.refresh(row)
        return answer_rows

    def list_answers(self, project_id: str) -> list[ClarificationAnswer]:
        stmt = select(ClarificationAnswer).where(ClarificationAnswer.project_id == project_id)
        return list(self.db.scalars(stmt).all())
