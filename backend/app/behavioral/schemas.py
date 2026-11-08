import uuid
from datetime import datetime

from pydantic import BaseModel


class ArchetypeOut(BaseModel):
    key: str
    name: str
    description: str


class ScoreOut(BaseModel):
    key: str
    label: str
    score: float


class BehavioralProfileOut(BaseModel):
    """Perfil de UMA entrevista (vai junto com a avaliação)."""

    archetype: ArchetypeOut
    description: str
    competencies: list[ScoreOut]
    star: list[ScoreOut]


class ProfileHistoryItemOut(BaseModel):
    session_id: uuid.UUID
    created_at: datetime | None
    overall_score: float | None
    competencies: dict[str, int]


class ConsolidatedProfileOut(BaseModel):
    """Perfil do aluno: média de todas as entrevistas comportamentais."""

    interviews_count: int
    archetype: ArchetypeOut | None
    latest_description: str | None
    strongest: str | None
    weakest: str | None
    competencies: list[ScoreOut]
    star: list[ScoreOut]
    history: list[ProfileHistoryItemOut]
