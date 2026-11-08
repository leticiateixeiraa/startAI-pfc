from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class OptionOut(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    id: str
    text: str
    options: list[OptionOut]


class OnboardingAnswersIn(BaseModel):
    # {id da pergunta: id da alternativa}
    answers: dict[str, str]


class AreaOut(BaseModel):
    key: str
    name: str
    description: str
    roles: list[str]
    skills: list[str]
    suggested_job_title: str


class AreaScoreOut(BaseModel):
    key: str
    name: str
    percent: int


class OnboardingResultOut(BaseModel):
    recommended_area: AreaOut
    ranking: list[AreaScoreOut]
    completed_at: datetime | None


class OnboardingStatusOut(BaseModel):
    status: Literal["pending", "completed", "skipped"]
    result: OnboardingResultOut | None = None
