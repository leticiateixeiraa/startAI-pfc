import uuid
from datetime import datetime

from pydantic import BaseModel


class CriteriaOut(BaseModel):
    relevance: int
    coherence: int
    completeness: int
    adequacy: int


class AnswerEvaluationOut(BaseModel):
    order_index: int
    question: str
    answer: str
    score: float
    criteria: CriteriaOut
    feedback: str
    strengths: list[str]
    improvements: list[str]


class InterviewEvaluationOut(BaseModel):
    session_id: uuid.UUID
    overall_score: float
    summary: str
    created_at: datetime | None
    answers: list[AnswerEvaluationOut]
