import uuid
from datetime import datetime

from pydantic import BaseModel

from app.behavioral.schemas import BehavioralProfileOut


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
    mistakes: list[str] = []
    suggested_answer: str | None = None


class InterviewEvaluationOut(BaseModel):
    session_id: uuid.UUID
    presentation_type: str | None = None
    seniority: str | None = None
    overall_score: float
    summary: str
    highlights: list[str] = []
    next_steps: list[str] = []
    created_at: datetime | None
    answers: list[AnswerEvaluationOut]
    # Só nas entrevistas comportamentais.
    behavioral_profile: BehavioralProfileOut | None = None
