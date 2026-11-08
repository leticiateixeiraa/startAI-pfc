import uuid

from sqlalchemy.orm import Session

from app.interview.models import InterviewQuestion, InterviewSession
from app.questions.llm_service import SENIORITY_LEVELS, generate_questions

PRESENTATION_TYPES = {
    "comportamental",
    "tecnica",
    "mista",
    "apresentacao_pessoal",
}


CATEGORIES = [
    {
        "id": "entrevista_de_emprego",
        "name": "Entrevista de emprego",
        "description": "Pratique respostas para processos seletivos e primeiras conversas com recrutadores.",
    },
    {
        "id": "apresentacao_academica",
        "name": "Apresentação acadêmica",
        "description": "Organize e apresente seu trabalho com clareza, segurança e objetividade.",
    },
]


def list_categories() -> list[dict[str, str]]:
    return CATEGORIES


def start_interview(
    db: Session,
    user_id: uuid.UUID,
    category: str,
    job_title: str,
    presentation_type: str,
    job_description: str | None,
    seniority: str | None = None,
) -> InterviewSession:
    valid_ids = {item["id"] for item in CATEGORIES}
    if category not in valid_ids:
        raise ValueError("Categoria de entrevista inválida")
    if presentation_type not in PRESENTATION_TYPES:
        raise ValueError("Tipo de entrevista inválido")
    if seniority is not None and seniority not in SENIORITY_LEVELS:
        raise ValueError("Nível da vaga inválido")
    questions = generate_questions(job_title, presentation_type, job_description, seniority)
    session = InterviewSession(
        user_id=user_id,
        category=category,
        presentation_type=presentation_type,
        seniority=seniority,
        job_title=job_title.strip()[:160],
        current_index=0,
        current_question_text=questions[0],
        finished=False,
    )
    db.add(session)
    db.flush()
    db.add_all(
        InterviewQuestion(session_id=session.id, order_index=index, text=question)
        for index, question in enumerate(questions)
    )
    db.commit()
    db.refresh(session)
    return session