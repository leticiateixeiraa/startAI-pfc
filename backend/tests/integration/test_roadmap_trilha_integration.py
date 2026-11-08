"""
Testes de integração da trilha de estudos gerada a partir da avaliação.

Endpoints: POST e GET /interviews/{session_id}/roadmap, além de GET /roadmaps
e PATCH /roadmaps/{id}/items/{item_id} usados com a trilha gerada.
A entrevista é feita de ponta a ponta pela API; só o Gemini é simulado.
"""
import uuid

from app.audit.models import AuditLog
from app.roadmap.models import LearningRoadmap, LearningRoadmapItem
from app.roadmap.recursos import RECURSOS

from tests.integration.apoio import (
    SENHA,
    montar_entrevista_ia,
    perguntas_geradas,
    responder,
    usuario_autenticado,
)

RESPOSTA = "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."
QUANTIDADE = len(perguntas_geradas())


def _entrevista_finalizada(api, gemini_falso, headers) -> str:
    gemini_falso.responder({"questions": perguntas_geradas()})
    criada = api.post("/interviews", json=montar_entrevista_ia("tecnica", seniority="junior"), headers=headers)
    assert criada.status_code == 201, criada.text
    session_id = criada.json()["session_id"]
    for numero in range(1, QUANTIDADE + 1):
        if numero < QUANTIDADE:
            gemini_falso.responder({"question": f"Pergunta adaptada {numero}?"})
        assert responder(api, headers, session_id, RESPOSTA).status_code == 200
    return session_id


def _avaliar(api, gemini_falso, headers, session_id) -> None:
    gemini_falso.responder({
        "summary": "Faltou profundidade técnica.",
        "next_steps": ["Revisar HTTP"],
        "answers": [
            {
                "index": numero,
                "relevance": 7,
                "coherence": 7,
                "completeness": 4,
                "adequacy": 6,
                "feedback": "Resposta vaga.",
                "improvements": ["Cite resultados"],
                "mistakes": ['"REST é um protocolo": REST é um estilo de arquitetura.'],
            }
            for numero in range(1, QUANTIDADE + 1)
        ],
    })
    assert api.post(f"/interviews/{session_id}/evaluation", headers=headers).status_code == 201


def _trilha_do_gemini() -> dict:
    return {
        "title": "Rumo à vaga de back-end",
        "objective": "Conquistar a vaga júnior",
        "summary": "Comece pelos fundamentos de HTTP.",
        "steps": [
            {
                "title": f"Etapa {numero}",
                "focus": "Ponto fraco da entrevista.",
                "description": "Estude e pratique.",
                "estimated_time": "1 semana",
                "tips": ["Faça anotações"],
                "practice": "Crie uma API de tarefas.",
                "resources": [
                    {"id": "fastapi_docs"},
                    {"type": "video", "title": "REST na prática", "search": "o que é API REST"},
                ],
            }
            for numero in range(1, 6)
        ],
    }


def _preparar(api, gemini_falso, prefixo):
    usuario, headers = usuario_autenticado(api, prefixo)
    session_id = _entrevista_finalizada(api, gemini_falso, headers)
    _avaliar(api, gemini_falso, headers, session_id)
    gemini_falso.prompts.clear()
    return usuario, headers, session_id


def _url(session_id: str) -> str:
    return f"/interviews/{session_id}/roadmap"


def test_post_deve_gerar_trilha_a_partir_da_avaliacao_e_retornar_201(api, db, gemini_falso):
    usuario, headers, session_id = _preparar(api, gemini_falso, "trilha")
    gemini_falso.responder(_trilha_do_gemini())

    resposta = api.post(_url(session_id), headers=headers)

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["session_id"] == session_id
    assert corpo["summary"] == "Comece pelos fundamentos de HTTP."
    assert len(corpo["items"]) == 5
    etapa = corpo["items"][0]
    assert etapa["status"] == "pending"
    assert etapa["tips"] == ["Faça anotações"]
    assert etapa["practice"] == "Crie uma API de tarefas."
    assert etapa["resources"][0]["url"] == RECURSOS["fastapi_docs"]["url"]
    assert etapa["resources"][1]["type"] == "video"
    assert "youtube.com/results" in etapa["resources"][1]["url"]
    # O prompt usa os erros da avaliação e o nível da vaga.
    assert "REST é um estilo de arquitetura" in gemini_falso.prompts[0]
    assert "Nível da vaga: Júnior" in gemini_falso.prompts[0]
    db.expire_all()
    assert db.query(AuditLog).filter_by(action="roadmap.generated", user_id=uuid.UUID(usuario["id"])).count() == 1


def test_post_repetido_deve_reaproveitar_a_trilha_sem_chamar_o_gemini(api, gemini_falso):
    _, headers, session_id = _preparar(api, gemini_falso, "trilharep")
    gemini_falso.responder(_trilha_do_gemini())
    primeira = api.post(_url(session_id), headers=headers)

    segunda = api.post(_url(session_id), headers=headers)

    assert segunda.status_code == 200
    assert segunda.json()["id"] == primeira.json()["id"]
    assert len(gemini_falso.prompts) == 1


def test_post_antes_da_avaliacao_deve_retornar_400(api, gemini_falso):
    _, headers = usuario_autenticado(api, "semavaliacao")
    session_id = _entrevista_finalizada(api, gemini_falso, headers)

    resposta = api.post(_url(session_id), headers=headers)

    assert resposta.status_code == 400
    assert "avaliação" in resposta.json()["detail"]


def test_post_com_falha_do_gemini_deve_retornar_502_e_nao_gravar(api, db, gemini_falso):
    _, headers, session_id = _preparar(api, gemini_falso, "trilhafalha")
    gemini_falso.responder({"title": "T", "steps": []})

    resposta = api.post(_url(session_id), headers=headers)

    assert resposta.status_code == 502
    db.expire_all()
    assert db.query(LearningRoadmap).filter_by(session_id=uuid.UUID(session_id)).count() == 0


def test_get_deve_retornar_404_antes_e_a_trilha_depois(api, gemini_falso):
    _, headers, session_id = _preparar(api, gemini_falso, "trilhaget")

    antes = api.get(_url(session_id), headers=headers)
    gemini_falso.responder(_trilha_do_gemini())
    api.post(_url(session_id), headers=headers)
    depois = api.get(_url(session_id), headers=headers)

    assert antes.status_code == 404
    assert depois.status_code == 200
    assert depois.json()["title"] == "Rumo à vaga de back-end"


def test_progresso_da_trilha_gerada_e_listagem(api, gemini_falso):
    _, headers, session_id = _preparar(api, gemini_falso, "trilhaprog")
    gemini_falso.responder(_trilha_do_gemini())
    trilha = api.post(_url(session_id), headers=headers).json()
    etapa = trilha["items"][0]

    atualizada = api.patch(
        f"/roadmaps/{trilha['id']}/items/{etapa['id']}", json={"status": "completed"}, headers=headers
    )
    lista = api.get("/roadmaps", headers=headers).json()

    assert atualizada.status_code == 200
    assert atualizada.json()["items"][0]["status"] == "completed"
    assert atualizada.json()["items"][0]["resources"]  # campos da IA continuam vindo
    assert lista[0]["session_id"] == session_id


def test_trilha_de_entrevista_de_outro_usuario_deve_retornar_403(api, gemini_falso):
    _, _, session_id = _preparar(api, gemini_falso, "donotrilha")
    _, headers_outro = usuario_autenticado(api, "intrusotrilha")

    assert api.post(_url(session_id), headers=headers_outro).status_code == 403
    assert api.get(_url(session_id), headers=headers_outro).status_code == 403


def test_trilha_sem_token_deve_retornar_401(api):
    assert api.post(_url(str(uuid.uuid4()))).status_code == 401


def test_exclusao_de_conta_deve_apagar_a_trilha_gerada(api, db, gemini_falso):
    usuario, headers, session_id = _preparar(api, gemini_falso, "lgpdtrilha")
    gemini_falso.responder(_trilha_do_gemini())
    trilha_id = api.post(_url(session_id), headers=headers).json()["id"]

    resposta = api.request("DELETE", "/auth/me", json={"password": SENHA}, headers=headers)

    assert resposta.status_code in (200, 204), resposta.text
    db.expire_all()
    assert db.query(LearningRoadmap).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 0
    assert db.query(LearningRoadmapItem).filter_by(roadmap_id=uuid.UUID(trilha_id)).count() == 0
