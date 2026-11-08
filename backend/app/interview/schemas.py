import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StartInterviewIn(BaseModel):
    # Enquanto o módulo `questions` não existe, quem escolhe a categoria
    # é o próprio corpo da requisição em vez de vir de um catálogo real.
    category: str


class StartInterviewOut(BaseModel):
    session_id: uuid.UUID
    questions: list[str]


class AnswerIn(BaseModel):
    answer_text: str
    # feat(speech): resposta falada. Omitidos = resposta digitada (compatível).
    input_mode: Literal["text", "voice"] = "text"
    audio_duration_seconds: float | None = Field(default=None, gt=0, le=300)


class NextQuestionOut(BaseModel):
    session_id: uuid.UUID
    question: str | None
    order_index: int
    finished: bool

    # Indica se ESSA pergunta foi ajustada com base na resposta anterior —
    # é o que comprova o critério de aceitação da feature 3: "ao menos uma
    # pergunta subsequente é ajustada com base na resposta dada".
    adapted: bool


class InterviewStateOut(BaseModel):
    """Situação atual da entrevista, para o aluno retomar de onde parou."""

    session_id: uuid.UUID
    job_title: str | None
    presentation_type: str | None
    seniority: str | None
    finished: bool
    # Pergunta pendente de resposta (None quando finalizada).
    current_question: str | None
    answered_count: int
    total_questions: int


class InterviewHistoryOut(BaseModel):
    session_id: uuid.UUID
    category: str
    job_title: str | None = None
    presentation_type: str | None
    seniority: str | None = None
    finished: bool
    answered_count: int
    created_at: datetime
    # Nota geral da avaliação por IA (feature 9); None enquanto não avaliada.
    overall_score: float | None = None
