"""
Regras de negócio da avaliação das respostas (funcionalidade 9).

RN01 - Só entrevistas finalizadas e com ao menos uma resposta são avaliadas.
RN02 - Cada entrevista é avaliada uma única vez; depois a avaliação salva é
       reaproveitada (não chama o Gemini de novo nem muda a nota).
RN03 - A nota de cada resposta é a média dos 4 critérios, e a nota geral é a
       média das notas das respostas, ambas com uma casa decimal. Quem
       calcula é o backend, não a IA.
RN04 - Se o Gemini falhar, nada é gravado: o aluno pode tentar de novo.
"""
import json
import uuid

from sqlalchemy.orm import Session

from app.evaluation.llm_avaliacao import CRITERIOS, avaliar_respostas
from app.evaluation.models import AnswerEvaluation, InterviewEvaluation
from app.interview.models import InterviewAnswer, InterviewSession


class AvaliacaoIndisponivel(Exception):
    """A entrevista ainda não pode ser avaliada (RN01)."""


def calcular_nota_resposta(notas: dict) -> float:
    return round(sum(notas[criterio] for criterio in CRITERIOS) / len(CRITERIOS), 1)


def calcular_nota_geral(notas_das_respostas: list[float]) -> float:
    return round(sum(notas_das_respostas) / len(notas_das_respostas), 1)


def buscar_avaliacao(db: Session, session_id: uuid.UUID) -> InterviewEvaluation | None:
    return (
        db.query(InterviewEvaluation)
        .filter(InterviewEvaluation.session_id == session_id)
        .first()
    )


def _respostas_da_sessao(db: Session, session_id: uuid.UUID) -> list[InterviewAnswer]:
    return (
        db.query(InterviewAnswer)
        .filter(InterviewAnswer.session_id == session_id)
        .order_by(InterviewAnswer.order_index)
        .all()
    )


def gerar_avaliacao(db: Session, session: InterviewSession) -> tuple[InterviewEvaluation, bool]:
    """Devolve (avaliacao, foi_criada_agora). Pode levantar
    AvaliacaoIndisponivel ou LLMGenerationError."""
    existente = buscar_avaliacao(db, session.id)
    if existente:
        return existente, False

    if not session.finished:
        raise AvaliacaoIndisponivel("Finalize a entrevista para ver a avaliação")
    respostas = _respostas_da_sessao(db, session.id)
    if not respostas:
        raise AvaliacaoIndisponivel("Essa entrevista não tem respostas para avaliar")

    resultado = avaliar_respostas(
        [(resposta.question_text, resposta.answer_text) for resposta in respostas],
        session.presentation_type,
    )

    notas = [calcular_nota_resposta(item) for item in resultado["answers"]]
    avaliacao = InterviewEvaluation(
        session_id=session.id,
        user_id=session.user_id,
        overall_score=calcular_nota_geral(notas),
        summary=resultado["summary"],
    )
    db.add(avaliacao)
    db.flush()  # gera o id usado pelas avaliações de cada resposta

    for resposta, item, nota in zip(respostas, resultado["answers"], notas):
        db.add(
            AnswerEvaluation(
                evaluation_id=avaliacao.id,
                answer_id=resposta.id,
                order_index=resposta.order_index,
                relevance=item["relevance"],
                coherence=item["coherence"],
                completeness=item["completeness"],
                adequacy=item["adequacy"],
                score=nota,
                feedback=item["feedback"],
                strengths=json.dumps(item["strengths"], ensure_ascii=False),
                improvements=json.dumps(item["improvements"], ensure_ascii=False),
            )
        )
    return avaliacao, True


def montar_resposta(db: Session, avaliacao: InterviewEvaluation) -> dict:
    """Junta a avaliação com o texto das perguntas e respostas para a tela."""
    itens = (
        db.query(AnswerEvaluation, InterviewAnswer)
        .join(InterviewAnswer, AnswerEvaluation.answer_id == InterviewAnswer.id)
        .filter(AnswerEvaluation.evaluation_id == avaliacao.id)
        .order_by(AnswerEvaluation.order_index)
        .all()
    )
    return {
        "session_id": avaliacao.session_id,
        "overall_score": avaliacao.overall_score,
        "summary": avaliacao.summary,
        "created_at": avaliacao.created_at,
        "answers": [
            {
                "order_index": item.order_index,
                "question": resposta.question_text,
                "answer": resposta.answer_text,
                "score": item.score,
                "criteria": {criterio: getattr(item, criterio) for criterio in CRITERIOS},
                "feedback": item.feedback,
                "strengths": json.loads(item.strengths or "[]"),
                "improvements": json.loads(item.improvements or "[]"),
            }
            for item, resposta in itens
        ],
    }
