"""
feat(evaluation): endpoints da avaliação das respostas por IA.

POST /interviews/{session_id}/evaluation -> gera a avaliação (ou devolve a
                                             que já existe, RN02)
GET  /interviews/{session_id}/evaluation -> só consulta; 404 se ainda não
                                             foi gerada

Só o dono da entrevista acessa. O administrador não tem rota aqui: a
avaliação contém o texto das respostas (minimização de dados, LGPD).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import get_current_user
from app.evaluation import service
from app.evaluation.schemas import InterviewEvaluationOut
from app.interview.models import InterviewSession
from app.models.base import get_db
from app.questions.llm_service import LLMGenerationError

router = APIRouter(prefix="/interviews", tags=["evaluation"])


def _sessao_do_usuario(db: Session, session_id: uuid.UUID, user_id: str) -> InterviewSession:
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão de entrevista não encontrada")
    if str(session.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Essa sessão não pertence ao usuário autenticado")
    return session


@router.get("/{session_id}/evaluation", response_model=InterviewEvaluationOut)
def consultar_avaliacao(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _sessao_do_usuario(db, session_id, user_id)
    avaliacao = service.buscar_avaliacao(db, session.id)
    if not avaliacao:
        raise HTTPException(status_code=404, detail="Essa entrevista ainda não foi avaliada")
    return service.montar_resposta(db, avaliacao)


@router.post("/{session_id}/evaluation", response_model=InterviewEvaluationOut)
def gerar_avaliacao(
    session_id: uuid.UUID,
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _sessao_do_usuario(db, session_id, user_id)
    try:
        avaliacao, criada = service.gerar_avaliacao(db, session)
    except service.AvaliacaoIndisponivel as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LLMGenerationError as error:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(error)) from error

    if criada:
        response.status_code = status.HTTP_201_CREATED
        # Na auditoria vai só a nota geral, nunca o texto das respostas.
        record_event(
            db,
            "interview.evaluated",
            uuid.UUID(user_id),
            "interview_session",
            str(session.id),
            {"overall_score": avaliacao.overall_score},
            ip_address=request.client.host if request.client else None,
        )
        try:
            db.commit()
        except IntegrityError:
            # Duas requisições ao mesmo tempo (ex.: duplo clique): a outra
            # gravou primeiro. Descarta esta e devolve a que ficou salva.
            db.rollback()
            avaliacao = service.buscar_avaliacao(db, session.id)
            response.status_code = status.HTTP_200_OK
        else:
            db.refresh(avaliacao)
    return service.montar_resposta(db, avaliacao)
