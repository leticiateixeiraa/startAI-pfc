"""
Regras de negócio das trilhas de estudo (funcionalidade 8).

RN01 - A trilha automática nasce da AVALIAÇÃO da entrevista: só entrevistas
       já avaliadas geram trilha.
RN02 - Uma trilha por entrevista: depois de gerada, ela é reaproveitada
       (não chama o Gemini de novo) e o aluno vai marcando o progresso das
       etapas (PATCH /roadmaps/{id}/items/{item_id}).
RN03 - Os links vêm do catálogo do backend (recursos.py) ou são buscas no
       YouTube; a IA nunca escreve um link.
RN04 - Se o Gemini falhar, nada é gravado: o aluno pode tentar de novo.
"""
import json
import uuid

from sqlalchemy.orm import Session

from app.behavioral.competencias import COMPETENCIAS, competencia_mais_fraca
from app.behavioral.models import BehavioralProfile
from app.evaluation.llm_avaliacao import CRITERIOS
from app.evaluation.models import AnswerEvaluation, InterviewEvaluation
from app.interview.models import InterviewSession
from app.onboarding.models import CareerOnboarding
from app.onboarding.questionario import AREAS
from app.roadmap.llm_trilha import gerar_trilha
from app.roadmap.models import LearningRoadmap, LearningRoadmapItem

MAX_PONTOS_NO_PROMPT = 10


class TrilhaIndisponivel(Exception):
    """A entrevista ainda não pode gerar trilha (RN01)."""


def buscar_por_sessao(db: Session, session_id: uuid.UUID) -> LearningRoadmap | None:
    return db.query(LearningRoadmap).filter(LearningRoadmap.session_id == session_id).first()


def _montar_contexto(db: Session, session: InterviewSession, avaliacao: InterviewEvaluation) -> dict:
    respostas = (
        db.query(AnswerEvaluation)
        .filter(AnswerEvaluation.evaluation_id == avaliacao.id)
        .order_by(AnswerEvaluation.order_index)
        .all()
    )
    pontos = {"improvements": [], "mistakes": []}
    for resposta in respostas:
        for chave in pontos:
            pontos[chave].extend(json.loads(getattr(resposta, chave) or "[]"))

    perfil = (
        db.query(BehavioralProfile).filter(BehavioralProfile.evaluation_id == avaliacao.id).first()
    )
    questionario = (
        db.query(CareerOnboarding).filter(CareerOnboarding.user_id == session.user_id).first()
    )
    area = questionario.recommended_area if questionario and not questionario.skipped else None

    return {
        "job_title": session.job_title,
        "presentation_type": session.presentation_type,
        "seniority": session.seniority,
        "career_area": AREAS[area]["name"] if area in AREAS else None,
        "overall_score": avaliacao.overall_score,
        "criteria": {
            criterio: round(sum(getattr(r, criterio) for r in respostas) / len(respostas), 1)
            for criterio in CRITERIOS
        }
        if respostas
        else {},
        "summary": avaliacao.summary,
        "next_steps": json.loads(avaliacao.next_steps or "[]"),
        "improvements": pontos["improvements"][:MAX_PONTOS_NO_PROMPT],
        "mistakes": pontos["mistakes"][:MAX_PONTOS_NO_PROMPT],
        "weakest_competency": (
            COMPETENCIAS[
                competencia_mais_fraca({chave: getattr(perfil, chave) for chave in COMPETENCIAS})
            ]["label"]
            if perfil
            else None
        ),
    }


def gerar_trilha_da_entrevista(db: Session, session: InterviewSession) -> tuple[LearningRoadmap, bool]:
    """Devolve (trilha, foi_criada_agora). Pode levantar TrilhaIndisponivel
    ou LLMGenerationError. Não faz commit."""
    existente = buscar_por_sessao(db, session.id)
    if existente:
        return existente, False

    avaliacao = (
        db.query(InterviewEvaluation).filter(InterviewEvaluation.session_id == session.id).first()
    )
    if not avaliacao:
        raise TrilhaIndisponivel("Veja a avaliação da entrevista antes de gerar a trilha de estudos")

    trilha = gerar_trilha(_montar_contexto(db, session, avaliacao))
    roadmap = LearningRoadmap(
        user_id=session.user_id,
        session_id=session.id,
        title=trilha["title"],
        objective=trilha["objective"],
        summary=trilha["summary"],
    )
    db.add(roadmap)
    db.flush()
    db.add_all(
        LearningRoadmapItem(
            roadmap_id=roadmap.id,
            order_index=indice,
            title=etapa["title"],
            description=etapa["description"],
            focus=etapa["focus"],
            estimated_time=etapa["estimated_time"],
            practice=etapa["practice"],
            tips=json.dumps(etapa["tips"], ensure_ascii=False),
            resources=json.dumps(etapa["resources"], ensure_ascii=False),
        )
        for indice, etapa in enumerate(trilha["steps"])
    )
    return roadmap, True


def montar_roadmap(db: Session, roadmap: LearningRoadmap) -> dict:
    itens = (
        db.query(LearningRoadmapItem)
        .filter(LearningRoadmapItem.roadmap_id == roadmap.id)
        .order_by(LearningRoadmapItem.order_index)
        .all()
    )
    return {
        "id": roadmap.id,
        "session_id": roadmap.session_id,
        "title": roadmap.title,
        "objective": roadmap.objective,
        "summary": roadmap.summary,
        "created_at": roadmap.created_at,
        "updated_at": roadmap.updated_at,
        "items": [
            {
                "id": item.id,
                "order_index": item.order_index,
                "title": item.title,
                "description": item.description,
                "status": item.status,
                "focus": item.focus,
                "estimated_time": item.estimated_time,
                "practice": item.practice,
                "tips": json.loads(item.tips or "[]"),
                "resources": json.loads(item.resources or "[]"),
            }
            for item in itens
        ],
    }
