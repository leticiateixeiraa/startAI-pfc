import uuid

from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: str
    name: str
    description: str


class StartInterviewIn(BaseModel):
    job_title: str
    presentation_type: str
    job_description: str = Field(min_length=20)
    # Nível da vaga (estagio, junior, pleno, senior). Opcional para não
    # quebrar clientes antigos; o formulário do front-end sempre envia.
    seniority: str | None = None


class InterviewSessionOut(BaseModel):
    session_id: uuid.UUID
    questions: list[str]
