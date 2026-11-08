"""
Testes de integração do feedback detalhado e do perfil comportamental.

Endpoints: POST /interviews/{id}/evaluation (com os campos novos) e
GET /profile/behavioral.

A entrevista é feita de ponta a ponta pela API (POST /interviews com a
modalidade + respostas), com o Gemini simulado gerando as perguntas, as
perguntas adaptadas e a avaliação. Nada é gravado direto no banco: com o
SQLite de teste (uma conexão só), uma escrita direta logo depois de uma
requisição podia ser desfeita pelo fechamento da sessão do servidor.
"""
import uuid

from app.behavioral.models import BehavioralProfile

from tests.integration.apoio import (
    SENHA,
    montar_entrevista_ia,
    perguntas_geradas,
    responder,
    usuario_autenticado,
)

RESPOSTA = "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."
QUANTIDADE = len(perguntas_geradas())


def _entrevista_finalizada(api, gemini_falso, headers, presentation_type: str = "tecnica") -> str:
    gemini_falso.responder({"questions": perguntas_geradas()})
    criada = api.post("/interviews", json=montar_entrevista_ia(presentation_type), headers=headers)
    assert criada.status_code == 201, criada.text
    session_id = criada.json()["session_id"]
    for numero in range(1, QUANTIDADE + 1):
        if numero < QUANTIDADE:  # a última resposta encerra sem pedir nova pergunta
            gemini_falso.responder({"question": f"Pergunta adaptada {numero}?"})
        resposta = responder(api, headers, session_id, RESPOSTA)
        assert resposta.status_code == 200, resposta.text
    assert resposta.json()["finished"] is True
    gemini_falso.prompts.clear()  # o teste confere só o prompt da avaliação
    return session_id


def _avaliacao(competencias: dict | None = None, star: dict | None = None) -> dict:
    conteudo = {
        "summary": "Boa entrevista.",
        "highlights": ["Exemplos reais"],
        "next_steps": ["Feche cada resposta com o resultado"],
        "answers": [
            {
                "index": numero,
                "relevance": 8,
                "coherence": 8,
                "completeness": 6,
                "adequacy": 8,
                "feedback": "Boa resposta.",
                "strengths": ["Clareza"],
                "improvements": ["Cite números"],
                "mistakes": ['"entreguei tudo sozinho": evite contradizer o trabalho em equipe.'],
                "suggested_answer": "No projeto X, eu [ação] e o resultado foi [número].",
            }
            for numero in range(1, QUANTIDADE + 1)
        ],
    }
    if competencias is not None:
        conteudo["behavioral_profile"] = {
            "competencies": competencias,
            "star": star or {"situation": 8, "task": 7, "action": 9, "result": 4},
            "description": "Você mostra espírito de equipe.",
        }
    return conteudo


def _competencias(**alteradas) -> dict:
    return {
        "comunicacao": 6,
        "trabalho_em_equipe": 6,
        "lideranca": 6,
        "resolucao_de_problemas": 6,
        "adaptabilidade": 6,
        "inteligencia_emocional": 6,
        **alteradas,
    }


def _avaliar(api, headers, session_id):
    return api.post(f"/interviews/{session_id}/evaluation", headers=headers)


def test_avaliacao_deve_trazer_erros_resposta_sugerida_e_destaques(api, db, gemini_falso):
    _, headers = usuario_autenticado(api, "feedback")
    session_id = _entrevista_finalizada(api, gemini_falso, headers, "tecnica")
    gemini_falso.responder(_avaliacao())

    corpo = _avaliar(api, headers, session_id).json()

    assert corpo["presentation_type"] == "tecnica"
    assert corpo["highlights"] == ["Exemplos reais"]
    assert corpo["next_steps"] == ["Feche cada resposta com o resultado"]
    assert corpo["answers"][0]["mistakes"][0].startswith('"entreguei tudo sozinho"')
    assert "[número]" in corpo["answers"][0]["suggested_answer"]
    assert corpo["behavioral_profile"] is None
    # E continua igual quando a avaliação salva é consultada depois.
    salvo = api.get(f"/interviews/{session_id}/evaluation", headers=headers).json()
    assert salvo["answers"][0]["mistakes"] == corpo["answers"][0]["mistakes"]


def test_entrevista_comportamental_deve_gravar_e_devolver_o_perfil(api, db, gemini_falso):
    _, headers = usuario_autenticado(api, "perfil")
    session_id = _entrevista_finalizada(api, gemini_falso, headers, "comportamental")
    gemini_falso.responder(_avaliacao(_competencias(trabalho_em_equipe=9)))

    resposta = _avaliar(api, headers, session_id)

    assert resposta.status_code == 201, resposta.text
    perfil = resposta.json()["behavioral_profile"]
    assert perfil["archetype"]["key"] == "trabalho_em_equipe"
    assert perfil["archetype"]["name"] == "Perfil Colaborativo"
    assert {item["key"]: item["score"] for item in perfil["star"]}["result"] == 4
    assert "behavioral_profile" in gemini_falso.prompts[0]
    db.expire_all()
    assert db.query(BehavioralProfile).filter_by(session_id=uuid.UUID(session_id)).count() == 1


def test_comportamental_sem_perfil_deve_retornar_502_e_nao_gravar_nada(api, db, gemini_falso):
    _, headers = usuario_autenticado(api, "semperfil")
    session_id = _entrevista_finalizada(api, gemini_falso, headers, "comportamental")
    gemini_falso.responder(_avaliacao())  # sem behavioral_profile

    resposta = _avaliar(api, headers, session_id)

    assert resposta.status_code == 502
    assert api.get(f"/interviews/{session_id}/evaluation", headers=headers).status_code == 404


def test_perfil_consolidado_deve_ser_a_media_das_entrevistas_comportamentais(api, db, gemini_falso):
    _, headers = usuario_autenticado(api, "consolidado")
    primeira = _entrevista_finalizada(api, gemini_falso, headers, "comportamental")
    segunda = _entrevista_finalizada(api, gemini_falso, headers, "comportamental")
    tecnica = _entrevista_finalizada(api, gemini_falso, headers, "tecnica")
    gemini_falso.responder(_avaliacao(_competencias(lideranca=9, comunicacao=2)))
    _avaliar(api, headers, primeira)
    gemini_falso.responder(_avaliacao(_competencias(lideranca=6, comunicacao=3, adaptabilidade=10)))
    _avaliar(api, headers, segunda)
    gemini_falso.responder(_avaliacao())
    _avaliar(api, headers, tecnica)

    corpo = api.get("/profile/behavioral", headers=headers).json()

    assert corpo["interviews_count"] == 2
    medias = {item["key"]: item["score"] for item in corpo["competencies"]}
    assert medias["lideranca"] == 7.5
    assert medias["adaptabilidade"] == 8.0
    assert medias["comunicacao"] == 2.5
    assert corpo["archetype"]["key"] == "adaptabilidade"
    assert corpo["strongest"] == "adaptabilidade"
    assert corpo["weakest"] == "comunicacao"
    assert {item["session_id"] for item in corpo["history"]} == {primeira, segunda}
    assert corpo["history"][0]["overall_score"] == 7.5


def test_perfil_sem_entrevista_comportamental_deve_vir_vazio(api):
    _, headers = usuario_autenticado(api, "vazio")

    corpo = api.get("/profile/behavioral", headers=headers).json()

    assert corpo["interviews_count"] == 0
    assert corpo["archetype"] is None
    assert corpo["competencies"] == []


def test_perfil_nao_deve_misturar_usuarios(api, db, gemini_falso):
    _, headers_dono = usuario_autenticado(api, "donoperfil")
    _, headers_outro = usuario_autenticado(api, "outroperfil")
    session_id = _entrevista_finalizada(api, gemini_falso, headers_dono, "comportamental")
    gemini_falso.responder(_avaliacao(_competencias()))
    _avaliar(api, headers_dono, session_id)

    assert api.get("/profile/behavioral", headers=headers_outro).json()["interviews_count"] == 0


def test_exclusao_de_conta_deve_apagar_o_perfil_comportamental(api, db, gemini_falso):
    usuario, headers = usuario_autenticado(api, "lgpdperfil")
    session_id = _entrevista_finalizada(api, gemini_falso, headers, "comportamental")
    gemini_falso.responder(_avaliacao(_competencias()))
    _avaliar(api, headers, session_id)

    resposta = api.request("DELETE", "/auth/me", json={"password": SENHA}, headers=headers)

    assert resposta.status_code in (200, 204), resposta.text
    db.expire_all()
    assert db.query(BehavioralProfile).filter_by(user_id=uuid.UUID(usuario["id"])).count() == 0


def test_perfil_sem_token_deve_retornar_401(api):
    assert api.get("/profile/behavioral").status_code == 401
