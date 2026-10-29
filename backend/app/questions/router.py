import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.interview.models import InterviewQuestion
from app.models.base import get_db
from app.questions import service
from app.questions.llm_service import LLMGenerationError
from app.questions.schemas import CategoryOut, InterviewSessionOut, StartInterviewIn
from app.audit.service import record_event


router = APIRouter(tags=["questions"])


@router.get("/questions/categories", response_model=list[CategoryOut])
def categories():
    return service.list_categories()


@router.post("/interviews", response_model=InterviewSessionOut, status_code=status.HTTP_201_CREATED)
def start_interview(
    payload: StartInterviewIn,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = (
        "apresentacao_academica"
        if payload.presentation_type == "apresentacao_academica"
        else "entrevista_de_emprego"
    )
    try:
        session = service.start_interview(
            db,
            uuid.UUID(user_id),
            category,
            payload.job_title,
            payload.presentation_type,
            payload.job_description,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LLMGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session.id)
        .order_by(InterviewQuestion.order_index)
        .all()
    )
    record_event(
        db,
        "interview.started",
        uuid.UUID(user_id),
        "interview_session",
        str(session.id),
        {"presentation_type": payload.presentation_type, "category": category},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return InterviewSessionOut(
        session_id=session.id,
        questions=[question.text for question in questions],
    )