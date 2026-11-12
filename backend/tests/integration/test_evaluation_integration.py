"""
Testes de integração da avaliação das respostas por IA (app/evaluation/router.py).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista.

Endpoints: POST e GET /interviews/{session_id}/evaluation.

A entrevista é feita de ponta a ponta pela API (mock-start + respostas) e só
o Gemini é simulado. Inclui o trio de segurança: sem token -> 401, sessão de
outro usuário -> 403, dono da sessão -> 201/200.
"""
import uuid

from app.audit.models import AuditLog
from app.evaluation.models import AnswerEvaluation, InterviewEvaluation
from app.interview.service import QUESTION_BANK
from tests.integration.apoio import iniciar_entrevista_mock, responder, usuario_autenticado

RESPOSTA_DETALHADA = (
    "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."
)
QUANTIDADE_DE_PERGUNTAS = len(QUESTION_BANK["entrevista_de_emprego"])


def _entrevista_finalizada(api, headers) -> str:
    sessao = iniciar_entrevista_mock(api, headers)
    for _ in range(QUANTIDADE_DE_PERGUNTAS):
        resposta = responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)
        assert resposta.status_code == 200, resposta.text
    assert resposta.json()["finished"] is True
    return sessao["session_id"]


def _avaliacao_do_gemini(quantidade: int, nota: int = 8) -> dict:
    return {
        "summary": "Você foi claro e objetivo.",
        "answers": [
            {
                "index": numero,
                "relevance": nota,
                "coherence": nota,
                "completeness": nota - 2,
                "adequacy": nota,
                "feedback": f"Boa resposta {numero}.",
                "strengths": ["Clareza"],
                "improvements": ["Cite números"],
            }
            for numero in range(1, quantidade + 1)
        ],
    }


def _url(session_id: str) -> str:
    return f"/interviews/{session_id}/evaluation"


# --- POST /interviews/{id}/evaluation -------------------------------------------


def test_post_deve_gerar_avaliacao_com_notas_calculadas_e_retornar_201(api, db, gemini_falso):
    # Arrange
    _, headers = usuario_autenticado(api, "avaliacao")
    session_id = _entrevista_finalizada(api, headers)
    gemini_falso.responder(_avaliacao_do_gemini(QUANTIDADE_DE_PERGUNTAS))

    # Act
    resposta = api.post(_url(session_id), headers=headers)

    # Assert
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["overall_score"] == 7.5  # (8 + 8 + 6 + 8) / 4
    assert corpo["summary"] == "Você foi claro e objetivo."
    assert len(corpo["answers"]) == QUANTIDADE_DE_PERGUNTAS
    primeira = corpo["answers"][0]
    assert primeira["question"] == QUESTION_BANK["entrevista_de_emprego"][0]
    assert primeira["answer"] == RESPOSTA_DETALHADA
    assert primeira["criteria"] == {"relevance": 8, "coherence": 8, "completeness": 6, "adequacy": 8}
    assert primeira["strengths"] == ["Clareza"]

    db.expire_all()
    avaliacao = db.query(InterviewEvaluation).filter_by(session_id=uuid.UUID(session_id)).one()
    assert db.query(AnswerEvaluation).filter_by(evaluation_id=avaliacao.id).count() == QUANTIDADE_DE_PERGUNTAS


def test_post_repetido_deve_reaproveitar_avaliacao_sem_chamar_o_gemini_de_novo(api, gemini_falso):
    _, headers = usuario_autenticado(api, "repetida")
    session_id = _entrevista_finalizada(api, headers)
    gemini_falso.responder(_avaliacao_do_gemini(QUANTIDADE_DE_PERGUNTAS))
    primeira = api.post(_url(session_id), headers=headers)

    # Nenhuma resposta nova foi enfileirada: se chamasse o Gemini, o falso falharia.
    segunda = api.post(_url(session_id), headers=headers)

    assert primeira.status_code == 201
    assert segunda.status_code == 200
    assert segunda.json()["overall_score"] == primeira.json()["overall_score"]
    assert len(gemini_falso.prompts) == 1


def test_post_deve_registrar_auditoria_somente_com_a_nota(api, db, gemini_falso):
    usuario, headers = usuario_autenticado(api, "auditada")
    session_id = _entrevista_finalizada(api, headers)
    gemini_falso.responder(_avaliacao_do_gemini(QUANTIDADE_DE_PERGUNTAS))

    api.post(_url(session_id), headers=headers)

    db.expire_all()
    evento = (
        db.query(AuditLog)
        .filter_by(action="interview.evaluated", user_id=uuid.UUID(usuario["id"]))
        .one()
    )
    assert evento.resource_id == session_id
    assert "overall_score" in evento.details
    assert RESPOSTA_DETALHADA not in evento.details  # LGPD: sem o texto das respostas


def test_post_em_entrevista_nao_finalizada_deve_retornar_400(api):
    _, headers = usuario_autenticado(api, "andamento")
    sessao = iniciar_entrevista_mock(api, headers)
    responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)

    resposta = api.post(_url(sessao["session_id"]), headers=headers)

    assert resposta.status_code == 400
    assert "Finalize" in resposta.json()["detail"]


def test_post_com_falha_do_gemini_deve_retornar_502_e_nao_gravar_nada(api, db, gemini_falso):
    _, headers = usuario_autenticado(api, "falha")
    session_id = _entrevista_finalizada(api, headers)
    gemini_falso.responder("resposta que não é json")

    resposta = api.post(_url(session_id), headers=headers)

    assert resposta.status_code == 502
    db.expire_all()
    assert db.query(InterviewEvaluation).filter_by(session_id=uuid.UUID(session_id)).count() == 0


def test_post_de_sessao_inexistente_deve_retornar_404(api):
    _, headers = usuario_autenticado(api, "inexistente")

    resposta = api.post(_url(str(uuid.uuid4())), headers=headers)

    assert resposta.status_code == 404


# --- Trio de segurança ----------------------------------------------------------


def test_post_sem_token_deve_retornar_401(api):
    resposta = api.post(_url(str(uuid.uuid4())))

    assert resposta.status_code == 401


def test_post_e_get_de_sessao_de_outro_usuario_devem_retornar_403(api):
    _, headers_dono = usuario_autenticado(api, "dono")
    _, headers_outro = usuario_autenticado(api, "intruso")
    session_id = _entrevista_finalizada(api, headers_dono)

    assert api.post(_url(session_id), headers=headers_outro).status_code == 403
    assert api.get(_url(session_id), headers=headers_outro).status_code == 403


# --- GET /interviews/{id}/evaluation --------------------------------------------


def test_get_antes_de_gerar_deve_retornar_404_e_depois_a_avaliacao_salva(api, gemini_falso):
    _, headers = usuario_autenticado(api, "consulta")
    session_id = _entrevista_finalizada(api, headers)

    antes = api.get(_url(session_id), headers=headers)
    gemini_falso.responder(_avaliacao_do_gemini(QUANTIDADE_DE_PERGUNTAS, nota=6))
    api.post(_url(session_id), headers=headers)
    depois = api.get(_url(session_id), headers=headers)

    assert antes.status_code == 404
    assert depois.status_code == 200
    assert depois.json()["overall_score"] == 5.5


def test_historico_deve_trazer_a_nota_geral_da_entrevista_avaliada(api, gemini_falso):
    _, headers = usuario_autenticado(api, "historico")
    avaliada = _entrevista_finalizada(api, headers)
    sem_avaliacao = _entrevista_finalizada(api, headers)
    gemini_falso.responder(_avaliacao_do_gemini(QUANTIDADE_DE_PERGUNTAS))
    api.post(_url(avaliada), headers=headers)

    historico = {item["session_id"]: item for item in api.get("/interviews/history", headers=headers).json()}

    assert historico[avaliada]["overall_score"] == 7.5
    assert historico[sem_avaliacao]["overall_score"] is None
