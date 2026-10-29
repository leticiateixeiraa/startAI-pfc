"""
feat(interview-backend): implementa endpoint POST /interviews/{id}/answer
feat(interview-backend): implementa endpoint temporário POST /interviews/mock-start

O endpoint `/interviews/mock-start` é TEMPORÁRIO: existe só pra permitir
testar e demonstrar o entrevistador dinâmico enquanto o módulo `questions`
(Leonardo) ainda não expõe o POST /interviews real. Quando esse endpoint
existir, remover este mock e passar a consumir sessões criadas por lá —
o resto do módulo (POST /interviews/{id}/answer) não deve precisar mudar.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.interview import service
from app.interview.models import InterviewAnswer, InterviewSession
from app.interview.schemas import (
    AnswerIn,
    InterviewHistoryOut,
    NextQuestionOut,
    StartInterviewIn,
    StartInterviewOut,
)
from app.models.base import get_db
from app.audit.service import record_event

router = APIRouter(prefix="/interviews", tags=["interview"])


@router.get("/history", response_model=list[InterviewHistoryOut])
def history(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == uuid.UUID(user_id))
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    return [
        InterviewHistoryOut(
            session_id=session.id,
            category=session.category,
            presentation_type=session.presentation_type,
            finished=session.finished,
            answered_count=db.query(InterviewAnswer)
            .filter(InterviewAnswer.session_id == session.id)
            .count(),
            created_at=session.created_at,
        )
        for session in sessions
    ]


@router.post("/mock-start", response_model=StartInterviewOut, status_code=status.HTTP_201_CREATED)
def mock_start(
    payload: StartInterviewIn,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = service.start_mock_session(db, uuid.UUID(user_id), payload.category)
    record_event(
        db,
        "interview.started",
        uuid.UUID(user_id),
        "interview_session",
        str(session.id),
        {"category": session.category},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return StartInterviewOut(session_id=session.id, questions=[session.current_question_text])


@router.post("/{session_id}/answer", response_model=NextQuestionOut)
def answer(
    session_id: uuid.UUID,
    payload: AnswerIn,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão de entrevista não encontrada")
    if str(session.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Essa sessão não pertence ao usuário autenticado")
    if session.finished:
        raise HTTPException(status_code=400, detail="Essa sessão de entrevista já foi finalizada")

    next_question, adapted, finished = service.register_answer_and_get_next(
        db, session, payload.answer_text
    )
    record_event(
        db,
        "interview.answer_submitted",
        uuid.UUID(user_id),
        "interview_session",
        str(session.id),
        {"adapted": adapted, "finished": finished},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    return NextQuestionOut(
        session_id=session.id,
        question=next_question,
        order_index=session.current_index,
        finished=finished,
        adapted=adapted,
    )
