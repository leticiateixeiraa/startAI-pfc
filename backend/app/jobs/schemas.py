import uuid
from datetime import datetime

from pydantic import BaseModel


class JobProfileOut(BaseModel):
    job_title: str
    source: str  # "entrevistas" ou "questionario"
    area: str | None
    practiced_seniority: str
    recommended_seniority: str
    recommended_seniority_label: str
    level_reason: str
    average_score: float | None
    interviews_count: int
    skills: list[str]


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    company: str | None
    location: str | None
    salary_min: float | None
    salary_max: float | None
    url: str
    description: str | None
    posted_at: datetime | None
    compatibility: int
    reasons: list[str]


class JobRecommendationsOut(BaseModel):
    # profile = None quando o aluno ainda não tem dados (RN01); a tela
    # mostra o convite para fazer uma entrevista ou o questionário.
    profile: JobProfileOut | None
    jobs: list[JobOut]
    fetched_at: datetime | None
    from_cache: bool
    warning: str | None = None
    message: str | None = None
