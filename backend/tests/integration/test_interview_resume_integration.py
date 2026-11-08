"""
Testes de integração da retomada de entrevista (GET /interviews/{session_id}).

O aluno responde parte da entrevista, "sai", e depois consulta o estado para
continuar exatamente da pergunta pendente. Só o Gemini é simulado.
"""
import uuid

from app.interview.service import QUESTION_BANK

from tests.integration.apoio import (
    iniciar_entrevista_mock,
    montar_entrevista_ia,
    perguntas_geradas,
    responder,
    usuario_autenticado,
)

RESPOSTA = "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."


def _entrevista_ia(api, gemini_falso, headers) -> str:
    gemini_falso.responder({"questions": perguntas_geradas()})
    criada = api.post("/interviews", json=montar_entrevista_ia("tecnica", seniority="junior"), headers=headers)
    assert criada.status_code == 201, criada.text
    return criada.json()["session_id"]


def test_estado_deve_trazer_a_pergunta_pendente_e_o_progresso_depois_de_sair(api, gemini_falso):
    _, headers = usuario_autenticado(api, "retoma")
    session_id = _entrevista_ia(api, gemini_falso, headers)
    gemini_falso.responder({"question": "Pergunta adaptada 1?"})
    gemini_falso.responder({"question": "Pergunta adaptada 2?"})
    responder(api, headers, session_id, RESPOSTA)
    responder(api, headers, session_id, RESPOSTA)

    # O aluno "saiu" e voltou: nada além do id é necessário para continuar.
    estado = api.get(f"/interviews/{session_id}", headers=headers)

    assert estado.status_code == 200, estado.text
    corpo = estado.json()
    assert corpo["current_question"] == "Pergunta adaptada 2?"
    assert corpo["answered_count"] == 2
    assert corpo["total_questions"] == 5
    assert corpo["finished"] is False
    assert corpo["job_title"] == montar_entrevista_ia()["job_title"]
    assert corpo["seniority"] == "junior"


def test_estado_logo_apos_criar_deve_trazer_a_primeira_pergunta(api, gemini_falso):
    _, headers = usuario_autenticado(api, "inicio")
    session_id = _entrevista_ia(api, gemini_falso, headers)

    corpo = api.get(f"/interviews/{session_id}", headers=headers).json()

    assert corpo["current_question"] == perguntas_geradas()[0]
    assert corpo["answered_count"] == 0


def test_estado_de_entrevista_finalizada_nao_tem_pergunta_pendente(api):
    _, headers = usuario_autenticado(api, "finalizada")
    sessao = iniciar_entrevista_mock(api, headers)
    for _ in QUESTION_BANK["entrevista_de_emprego"]:
        responder(api, headers, sessao["session_id"], RESPOSTA)

    corpo = api.get(f"/interviews/{sessao['session_id']}", headers=headers).json()

    assert corpo["finished"] is True
    assert corpo["current_question"] is None
    assert corpo["answered_count"] == corpo["total_questions"] == len(QUESTION_BANK["entrevista_de_emprego"])


def test_historico_deve_trazer_o_cargo(api, gemini_falso):
    _, headers = usuario_autenticado(api, "cargo")
    session_id = _entrevista_ia(api, gemini_falso, headers)

    historico = {item["session_id"]: item for item in api.get("/interviews/history", headers=headers).json()}

    assert historico[session_id]["job_title"] == montar_entrevista_ia()["job_title"]


def test_estado_de_sessao_de_outro_usuario_deve_retornar_403(api):
    _, headers_dono = usuario_autenticado(api, "donoestado")
    _, headers_outro = usuario_autenticado(api, "intrusoestado")
    sessao = iniciar_entrevista_mock(api, headers_dono)

    assert api.get(f"/interviews/{sessao['session_id']}", headers=headers_outro).status_code == 403


def test_estado_de_sessao_inexistente_deve_retornar_404(api):
    _, headers = usuario_autenticado(api, "semsessao")

    assert api.get(f"/interviews/{uuid.uuid4()}", headers=headers).status_code == 404


def test_estado_sem_token_deve_retornar_401(api):
    assert api.get(f"/interviews/{uuid.uuid4()}").status_code == 401
