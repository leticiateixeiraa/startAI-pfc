"""
Regras de negócio do perfil comportamental.

RN01 - Só entrevistas do tipo "comportamental" geram perfil, e ele nasce
       junto com a avaliação da entrevista (uma chamada só ao Gemini).
RN02 - O tipo de perfil é a competência com a maior nota (backend decide,
       não a IA). Empate: vale a ordem de COMPETENCIAS.
RN03 - O perfil consolidado é a média, com uma casa decimal, de todas as
       entrevistas comportamentais avaliadas do aluno. O tipo de perfil
       consolidado é calculado sobre essas médias.
"""
import uuid

from sqlalchemy.orm import Session

from app.behavioral.competencias import (
    ARQUETIPOS,
    COMPETENCIAS,
    STAR,
    competencia_mais_forte,
    competencia_mais_fraca,
    definir_arquetipo,
)
from app.behavioral.models import BehavioralProfile
from app.evaluation.models import InterviewEvaluation


def salvar_perfil(db: Session, avaliacao: InterviewEvaluation, perfil: dict) -> BehavioralProfile:
    """Grava o perfil validado por llm_avaliacao (sem commit)."""
    registro = BehavioralProfile(
        evaluation_id=avaliacao.id,
        session_id=avaliacao.session_id,
        user_id=avaliacao.user_id,
        **perfil["competencies"],
        **{f"star_{chave}": nota for chave, nota in perfil["star"].items()},
        archetype=definir_arquetipo(perfil["competencies"])["key"],
        description=perfil["description"],
    )
    db.add(registro)
    return registro


def buscar_perfil(db: Session, evaluation_id: uuid.UUID) -> BehavioralProfile | None:
    return (
        db.query(BehavioralProfile)
        .filter(BehavioralProfile.evaluation_id == evaluation_id)
        .first()
    )


def _notas_competencias(registro: BehavioralProfile) -> dict[str, int]:
    return {chave: getattr(registro, chave) for chave in COMPETENCIAS}


def _notas_star(registro: BehavioralProfile) -> dict[str, int]:
    return {chave: getattr(registro, f"star_{chave}") for chave in STAR}


def _lista_competencias(notas: dict) -> list[dict]:
    return [
        {"key": chave, "label": dados["label"], "score": notas[chave]}
        for chave, dados in COMPETENCIAS.items()
    ]


def _lista_star(notas: dict) -> list[dict]:
    return [{"key": chave, "label": label, "score": notas[chave]} for chave, label in STAR.items()]


def montar_perfil(registro: BehavioralProfile) -> dict:
    return {
        "archetype": {"key": registro.archetype, **ARQUETIPOS[registro.archetype]},
        "description": registro.description,
        "competencies": _lista_competencias(_notas_competencias(registro)),
        "star": _lista_star(_notas_star(registro)),
    }


def _media(valores: list[int]) -> float:
    return round(sum(valores) / len(valores), 1)


def perfil_consolidado(db: Session, user_id: uuid.UUID) -> dict:
    linhas = (
        db.query(BehavioralProfile, InterviewEvaluation.overall_score)
        .join(InterviewEvaluation, BehavioralProfile.evaluation_id == InterviewEvaluation.id)
        .filter(BehavioralProfile.user_id == user_id)
        .order_by(BehavioralProfile.created_at)
        .all()
    )
    if not linhas:
        return {
            "interviews_count": 0,
            "archetype": None,
            "latest_description": None,
            "strongest": None,
            "weakest": None,
            "competencies": [],
            "star": [],
            "history": [],
        }

    registros = [registro for registro, _ in linhas]
    medias = {
        chave: _media([getattr(registro, chave) for registro in registros]) for chave in COMPETENCIAS
    }
    medias_star = {
        chave: _media([getattr(registro, f"star_{chave}") for registro in registros]) for chave in STAR
    }
    return {
        "interviews_count": len(registros),
        "archetype": definir_arquetipo(medias),
        "latest_description": registros[-1].description,
        "strongest": competencia_mais_forte(medias),
        "weakest": competencia_mais_fraca(medias),
        "competencies": _lista_competencias(medias),
        "star": _lista_star(medias_star),
        "history": [
            {
                "session_id": registro.session_id,
                "created_at": registro.created_at,
                "overall_score": nota_geral,
                "competencies": _notas_competencias(registro),
            }
            for registro, nota_geral in linhas
        ],
    }
