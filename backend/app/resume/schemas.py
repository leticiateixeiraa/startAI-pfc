from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ResumeCriterionOut(BaseModel):
    key: str
    label: str
    score: float


class ResumeImprovementOut(BaseModel):
    title: str
    suggestion: str


class ResumeAnalysisOut(BaseModel):
    file_name: str
    file_type: Literal["pdf", "docx"]
    target_role: str | None
    overall_score: float
    summary: str
    criteria: list[ResumeCriterionOut]
    strengths: list[str]
    improvements: list[ResumeImprovementOut]
    skills_found: list[str]
    skills_missing: list[str]
    suggested_job_title: str | None
    analyzed_at: datetime
