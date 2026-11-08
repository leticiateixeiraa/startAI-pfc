"""
Regras de negócio do questionário de primeiro acesso.

RN01 - Todas as perguntas precisam ser respondidas, com uma alternativa que
       exista. Resposta inválida não grava nada.
RN02 - A afinidade com cada área é a porcentagem dos pontos que ela recebeu
       sobre o total de pontos das alternativas escolhidas. A área
       recomendada é a de maior afinidade; empate: vale a ordem de AREAS.
       O cálculo é do backend e não usa IA: o mesmo conjunto de respostas
       sempre dá o mesmo resultado.
RN03 - O aluno pode refazer o questionário quando quiser; vale o último.
RN04 - Pular o questionário só é registrado se ele ainda não foi respondido
       (pular não apaga um resultado que já existe).
"""
import json
import uuid

from sqlalchemy.orm import Session

from app.onboarding.models import CareerOnboarding
from app.onboarding.questionario import AREAS, PERGUNTAS


class RespostasInvalidas(Exception):
    """O questionário não foi respondido por completo ou corretamente (RN01)."""


def listar_perguntas() -> list[dict]:
    """Perguntas sem os pesos das alternativas."""
    return [
        {
            "id": pergunta["id"],
            "text": pergunta["text"],
            "options": [{"id": opcao["id"], "text": opcao["text"]} for opcao in pergunta["options"]],
        }
        for pergunta in PERGUNTAS
    ]


def calcular_pontos(respostas: dict[str, str]) -> dict[str, int]:
    pontos = dict.fromkeys(AREAS, 0)
    for pergunta in PERGUNTAS:
        escolhida = respostas.get(pergunta["id"])
        if escolhida is None:
            raise RespostasInvalidas("Responda todas as perguntas do questionário")
        opcao = next((opcao for opcao in pergunta["options"] if opcao["id"] == escolhida), None)
        if opcao is None:
            raise RespostasInvalidas(f"Alternativa inválida na pergunta '{pergunta['id']}'")
        for area, peso in opcao["weights"].items():
            pontos[area] += peso
    return pontos


def area_recomendada(pontos: dict[str, int]) -> str:
    return max(AREAS, key=lambda area: (pontos[area], -list(AREAS).index(area)))


def ranking(pontos: dict[str, int]) -> list[dict]:
    total = sum(pontos.values()) or 1
    ordem = sorted(AREAS, key=lambda area: (-pontos.get(area, 0), list(AREAS).index(area)))
    return [
        {"key": area, "name": AREAS[area]["name"], "percent": round(pontos.get(area, 0) * 100 / total)}
        for area in ordem
    ]


def buscar(db: Session, user_id: uuid.UUID) -> CareerOnboarding | None:
    return db.query(CareerOnboarding).filter(CareerOnboarding.user_id == user_id).first()


def salvar_respostas(db: Session, user_id: uuid.UUID, respostas: dict[str, str]) -> CareerOnboarding:
    """Valida, calcula e grava (sem commit). Pode levantar RespostasInvalidas."""
    pontos = calcular_pontos(respostas)
    perguntas = {pergunta["id"] for pergunta in PERGUNTAS}
    registro = buscar(db, user_id) or CareerOnboarding(user_id=user_id)
    registro.skipped = False
    # Guarda só as perguntas conhecidas, ignorando chaves extras.
    registro.answers = json.dumps({chave: valor for chave, valor in respostas.items() if chave in perguntas})
    registro.scores = json.dumps(pontos)
    registro.recommended_area = area_recomendada(pontos)
    db.add(registro)
    return registro


def pular(db: Session, user_id: uuid.UUID) -> tuple[CareerOnboarding, bool]:
    """Devolve (registro, foi_criado_agora). Não altera um registro existente (RN04)."""
    registro = buscar(db, user_id)
    if registro is not None:
        return registro, False
    registro = CareerOnboarding(user_id=user_id, skipped=True)
    db.add(registro)
    return registro, True


def montar_resultado(registro: CareerOnboarding) -> dict | None:
    if registro.skipped or not registro.recommended_area:
        return None
    area = registro.recommended_area
    return {
        "recommended_area": {"key": area, **AREAS[area]},
        "ranking": ranking(json.loads(registro.scores or "{}")),
        "completed_at": registro.updated_at,
    }


def montar_status(registro: CareerOnboarding | None) -> dict:
    if registro is None:
        return {"status": "pending", "result": None}
    resultado = montar_resultado(registro)
    return {"status": "completed" if resultado else "skipped", "result": resultado}
