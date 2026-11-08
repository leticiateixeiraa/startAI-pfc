"""
feat(behavioral): perfil comportamental consolidado do aluno.

GET /profile/behavioral -> média das competências e do método STAR em todas
                           as entrevistas comportamentais avaliadas, com o
                           histórico para o gráfico de evolução.

O perfil de UMA entrevista vem junto com a avaliação
(GET /interviews/{id}/evaluation). Só o próprio aluno vê o seu perfil.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.behavioral import service
from app.behavioral.schemas import ConsolidatedProfileOut
from app.models.base import get_db

router = APIRouter(prefix="/profile", tags=["behavioral"])


@router.get("/behavioral", response_model=ConsolidatedProfileOut)
def perfil_comportamental(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.perfil_consolidado(db, uuid.UUID(user_id))
