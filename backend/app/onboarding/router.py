"""
feat(onboarding): questionário de primeiro acesso para indicar a área da
tecnologia com mais afinidade.

GET  /onboarding/questions -> perguntas e alternativas (sem os pesos)
GET  /onboarding/me        -> situação do aluno: pending, completed ou skipped
POST /onboarding           -> envia as respostas e devolve o resultado
POST /onboarding/skip      -> pula o questionário (pode responder depois)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import get_current_user
from app.models.base import get_db
from app.onboarding import service
from app.onboarding.schemas import (
    OnboardingAnswersIn,
    OnboardingResultOut,
    OnboardingStatusOut,
    QuestionOut,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/questions", response_model=list[QuestionOut])
def perguntas(_: str = Depends(get_current_user)):
    return service.listar_perguntas()


@router.get("/me", response_model=OnboardingStatusOut)
def minha_situacao(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.montar_status(service.buscar(db, uuid.UUID(user_id)))


@router.post("", response_model=OnboardingResultOut)
def responder(
    payload: OnboardingAnswersIn,
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        registro = service.salvar_respostas(db, uuid.UUID(user_id), payload.answers)
    except service.RespostasInvalidas as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    # Na auditoria vai só a área recomendada, não as respostas.
    record_event(
        db,
        "onboarding.completed",
        uuid.UUID(user_id),
        "career_onboarding",
        None,
        {"recommended_area": registro.recommended_area},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(registro)
    return service.montar_resultado(registro)


@router.post("/skip", response_model=OnboardingStatusOut)
def pular(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registro, criado = service.pular(db, uuid.UUID(user_id))
    if criado:
        record_event(
            db,
            "onboarding.skipped",
            uuid.UUID(user_id),
            "career_onboarding",
            None,
            ip_address=request.client.host if request.client else None,
        )
    db.commit()
    db.refresh(registro)
    return service.montar_status(registro)
