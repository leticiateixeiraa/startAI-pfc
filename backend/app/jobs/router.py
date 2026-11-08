"""
feat(jobs): GET /jobs/recommendations — vagas reais compatíveis com o perfil.

?refresh=true ignora a lista salva e busca de novo na Jooble (botão
"Atualizar vagas"). Regras em app/jobs/service.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import get_current_user
from app.jobs import service
from app.jobs.jooble import VagasIndisponiveis
from app.jobs.schemas import JobRecommendationsOut
from app.models.base import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/recommendations", response_model=JobRecommendationsOut)
def recomendar_vagas(
    request: Request,
    refresh: bool = False,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    usuario = uuid.UUID(user_id)
    try:
        resultado = service.recomendar(db, usuario, atualizar=refresh)
    except service.SemPerfil as error:
        return {"profile": None, "jobs": [], "fetched_at": None, "from_cache": False, "message": str(error)}
    except VagasIndisponiveis as error:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(error)) from error

    if not resultado["from_cache"]:
        # Só registra quando a API foi consultada; o cargo buscado não é dado
        # pessoal sensível, mas não precisa ir para a auditoria.
        record_event(
            db,
            "jobs.recommended",
            usuario,
            "job_recommendation",
            None,
            {"count": len(resultado["jobs"]), "refresh": refresh},
            ip_address=request.client.host if request.client else None,
        )
    db.commit()
    return resultado
