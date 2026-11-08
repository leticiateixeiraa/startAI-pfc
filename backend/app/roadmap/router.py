import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import get_current_user
from app.interview.models import InterviewSession
from app.models.base import get_db
from app.questions.llm_service import LLMGenerationError
from app.roadmap import service
from app.roadmap.models import LearningRoadmap, LearningRoadmapItem
from app.roadmap.schemas import RoadmapCreate, RoadmapItemStatusIn, RoadmapOut

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])
# feat(roadmap-ia): trilha gerada a partir da avaliação de uma entrevista.
interview_router = APIRouter(prefix="/interviews", tags=["roadmaps"])


def _to_response(db: Session, roadmap: LearningRoadmap) -> RoadmapOut:
    return RoadmapOut.model_validate(service.montar_roadmap(db, roadmap))


@router.post("", response_model=RoadmapOut, status_code=status.HTTP_201_CREATED)
def create_roadmap(
    payload: RoadmapCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roadmap = LearningRoadmap(user_id=uuid.UUID(user_id), title=payload.title, objective=payload.objective)
    db.add(roadmap)
    db.flush()
    db.add_all(LearningRoadmapItem(roadmap_id=roadmap.id, order_index=index,
        title=item.title, description=item.description) for index, item in enumerate(payload.items))
    record_event(db, "roadmap.created", uuid.UUID(user_id), "roadmap", str(roadmap.id))
    db.commit()
    db.refresh(roadmap)
    return _to_response(db, roadmap)


@router.get("", response_model=list[RoadmapOut])
def list_roadmaps(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    roadmaps = db.query(LearningRoadmap).filter(
        LearningRoadmap.user_id == uuid.UUID(user_id)
    ).order_by(LearningRoadmap.created_at.desc()).all()
    return [_to_response(db, roadmap) for roadmap in roadmaps]


@router.patch("/{roadmap_id}/items/{item_id}", response_model=RoadmapOut)
def update_item_status(
    roadmap_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: RoadmapItemStatusIn,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roadmap = db.query(LearningRoadmap).filter(
        LearningRoadmap.id == roadmap_id, LearningRoadmap.user_id == uuid.UUID(user_id)
    ).first()
    item = db.query(LearningRoadmapItem).filter(
        LearningRoadmapItem.id == item_id, LearningRoadmapItem.roadmap_id == roadmap_id
    ).first()
    if not roadmap or not item:
        raise HTTPException(status_code=404, detail="Roadmap ou etapa não encontrada")
    item.status = payload.status
    record_event(db, "roadmap.item_updated", uuid.UUID(user_id), "roadmap_item", str(item.id), {"status": payload.status})
    db.commit()
    db.refresh(roadmap)
    return _to_response(db, roadmap)


def _sessao_do_usuario(db: Session, session_id: uuid.UUID, user_id: str) -> InterviewSession:
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão de entrevista não encontrada")
    if str(session.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Essa sessão não pertence ao usuário autenticado")
    return session


@interview_router.get("/{session_id}/roadmap", response_model=RoadmapOut)
def consultar_trilha(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _sessao_do_usuario(db, session_id, user_id)
    roadmap = service.buscar_por_sessao(db, session.id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Essa entrevista ainda não tem trilha de estudos")
    return _to_response(db, roadmap)


@interview_router.post("/{session_id}/roadmap", response_model=RoadmapOut)
def gerar_trilha(
    session_id: uuid.UUID,
    request: Request,
    response: Response,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _sessao_do_usuario(db, session_id, user_id)
    try:
        roadmap, criada = service.gerar_trilha_da_entrevista(db, session)
    except service.TrilhaIndisponivel as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LLMGenerationError as error:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(error)) from error

    if criada:
        response.status_code = status.HTTP_201_CREATED
        record_event(
            db,
            "roadmap.generated",
            uuid.UUID(user_id),
            "roadmap",
            str(roadmap.id),
            {"session_id": str(session.id)},
            ip_address=request.client.host if request.client else None,
        )
        try:
            db.commit()
        except IntegrityError:
            # Duas requisições ao mesmo tempo: fica a que gravou primeiro.
            db.rollback()
            roadmap = service.buscar_por_sessao(db, session.id)
            response.status_code = status.HTTP_200_OK
        else:
            db.refresh(roadmap)
    return _to_response(db, roadmap)
