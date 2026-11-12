"""
Testes de integração do entrevistador dinâmico (app/interview/router.py).
Responsável pelo módulo: Gabriel Sant'Anna Morais dos Santos.

Endpoints: POST /interviews/mock-start e POST /interviews/{session_id}/answer.

Inclui o trio de segurança no mesmo endpoint protegido
(POST /interviews/{id}/answer): sem token -> 401, sessão de outro usuário ->
403, dono da sessão -> 200. Os dois últimos testes cruzam recursos: a sessão
é criada pelo POST /interviews (módulo questions) e respondida aqui, com o
Gemini simulado por ser serviço externo.
"""
import uuid

from app.audit.models import AuditLog
from app.interview.models import InterviewAnswer, InterviewSession
from app.interview.service import QUESTION_BANK
from tests.integration.apoio import (
    iniciar_entrevista_mock,
    montar_entrevista_ia,
    perguntas_geradas,
    responder,
    usuario_autenticado,
)

RESPOSTA_DETALHADA = (
    "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."
)
PERGUNTAS_EMPREGO = QUESTION_BANK["entrevista_de_emprego"]


def _sessao(db, session_id: str) -> InterviewSession:
    db.expire_all()
    return db.query(InterviewSession).filter(InterviewSession.id == uuid.UUID(session_id)).one()


# --- POST /interviews/mock-start ---------------------------------------------


def test_mock_start_com_categoria_academica_deve_retornar_201_com_primeira_pergunta_e_persistir_sessao(api, db):
    # Arrange
    usuario, headers = usuario_autenticado(api, "mockstart")

    # Act
    resposta = api.post("/interviews/mock-start", json={"category": "apresentacao_academica"}, headers=headers)

    # Assert
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["questions"] == [QUESTION_BANK["apresentacao_academica"][0]]
    sessao = _sessao(db, corpo["session_id"])
    assert str(sessao.user_id) == usuario["id"]
    assert sessao.category == "apresentacao_academica"
    assert sessao.current_index == 0
    assert sessao.finished is False
    evento = db.query(AuditLog).filter(
        AuditLog.action == "interview.started", AuditLog.resource_id == corpo["session_id"]
    ).one()
    assert evento.ip_address == "127.0.0.1"


def test_mock_start_com_categoria_desconhecida_deve_retornar_201_usando_entrevista_de_emprego(api, db):
    # Arrange
    _, headers = usuario_autenticado(api, "categoria")

    # Act
    resposta = api.post("/interviews/mock-start", json={"category": "categoria_inventada"}, headers=headers)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["questions"] == [PERGUNTAS_EMPREGO[0]]
    assert _sessao(db, resposta.json()["session_id"]).category == "entrevista_de_emprego"


def test_mock_start_sem_campo_category_deve_retornar_422(api):
    # Arrange
    _, headers = usuario_autenticado(api, "semcategoria")

    # Act
    resposta = api.post("/interviews/mock-start", json={}, headers=headers)

    # Assert
    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["loc"] == ["body", "category"]
    assert erro["type"] == "missing"


def test_mock_start_sem_token_deve_retornar_401(api):
    # Act
    resposta = api.post("/interviews/mock-start", json={"category": "entrevista_de_emprego"})

    # Assert
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Not authenticated"}


# --- POST /interviews/{session_id}/answer: adaptação -------------------------


def test_answer_com_palavra_chave_desafio_deve_retornar_200_com_pergunta_adaptada_e_gravar_resposta(api, db):
    # Arrange
    _, headers = usuario_autenticado(api, "desafio")
    sessao = iniciar_entrevista_mock(api, headers)
    texto = "Meu maior desafio foi migrar um sistema legado sem parar a operação da empresa."

    # Act
    resposta = responder(api, headers, sessao["session_id"], texto)

    # Assert
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["adapted"] is True
    assert corpo["finished"] is False
    assert corpo["order_index"] == 1
    assert corpo["question"] == "Você mencionou uma dificuldade — como exatamente você a superou, passo a passo?"

    gravada = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == uuid.UUID(sessao["session_id"])
    ).one()
    assert gravada.question_text == PERGUNTAS_EMPREGO[0]
    assert gravada.answer_text == texto
    assert _sessao(db, sessao["session_id"]).current_question_text == corpo["question"]


def test_answer_curta_deve_retornar_200_pedindo_mais_detalhes(api):
    # Arrange
    _, headers = usuario_autenticado(api, "curta")
    sessao = iniciar_entrevista_mock(api, headers)

    # Act
    resposta = responder(api, headers, sessao["session_id"], "Sou desenvolvedor.")

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["adapted"] is True
    assert resposta.json()["question"] == (
        "Pode detalhar um pouco mais sua resposta anterior, com um exemplo concreto?"
    )


def test_answer_detalhada_sem_gatilho_deve_retornar_200_com_proxima_pergunta_do_roteiro(api):
    # Arrange
    _, headers = usuario_autenticado(api, "roteiro")
    sessao = iniciar_entrevista_mock(api, headers)

    # Act
    resposta = responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["adapted"] is False
    assert resposta.json()["question"] == PERGUNTAS_EMPREGO[1]


# --- POST /interviews/{session_id}/answer: fim da sessão ---------------------


def test_answer_na_ultima_pergunta_deve_retornar_200_finalizada_e_marcar_sessao_no_banco(api, db):
    # Arrange — responde as 3 primeiras das 4 perguntas do roteiro
    _, headers = usuario_autenticado(api, "finaliza")
    sessao = iniciar_entrevista_mock(api, headers)
    for _ in range(3):
        responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)

    # Act
    resposta = responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["finished"] is True
    assert resposta.json()["question"] is None
    gravada = _sessao(db, sessao["session_id"])
    assert gravada.finished is True
    assert gravada.current_question_text is None
    respostas = db.query(InterviewAnswer).filter(InterviewAnswer.session_id == gravada.id)
    assert [r.order_index for r in respostas.order_by(InterviewAnswer.order_index)] == [0, 1, 2, 3]


def test_answer_em_sessao_ja_finalizada_deve_retornar_400_sem_gravar_nova_resposta(api, db):
    # Arrange
    _, headers = usuario_autenticado(api, "jafinalizada")
    sessao = iniciar_entrevista_mock(api, headers)
    for _ in range(4):
        responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)

    # Act
    resposta = responder(api, headers, sessao["session_id"], "Mais uma resposta depois do fim.")

    # Assert
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": "Essa sessão de entrevista já foi finalizada"}
    total = db.query(InterviewAnswer).filter(InterviewAnswer.session_id == uuid.UUID(sessao["session_id"]))
    assert total.count() == 4


def test_answer_em_sessao_inexistente_deve_retornar_404(api):
    # Arrange
    _, headers = usuario_autenticado(api, "inexistente")

    # Act
    resposta = responder(api, headers, str(uuid.uuid4()), RESPOSTA_DETALHADA)

    # Assert
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Sessão de entrevista não encontrada"}


def test_answer_com_id_que_nao_e_uuid_deve_retornar_422(api):
    # Arrange
    _, headers = usuario_autenticado(api, "idinvalido")

    # Act
    resposta = responder(api, headers, "123", RESPOSTA_DETALHADA)

    # Assert
    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["path", "session_id"]


# --- POST /interviews/{session_id}/answer: segurança -------------------------


def test_answer_sem_token_deve_retornar_401(api):
    # Arrange
    _, headers = usuario_autenticado(api, "dono401")
    sessao = iniciar_entrevista_mock(api, headers)

    # Act
    resposta = api.post(f"/interviews/{sessao['session_id']}/answer", json={"answer_text": RESPOSTA_DETALHADA})

    # Assert
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Not authenticated"}


def test_answer_em_sessao_de_outro_usuario_deve_retornar_403_sem_gravar_resposta(api, db):
    # Arrange
    _, headers_dono = usuario_autenticado(api, "dono")
    _, headers_intruso = usuario_autenticado(api, "intruso")
    sessao = iniciar_entrevista_mock(api, headers_dono)

    # Act
    resposta = responder(api, headers_intruso, sessao["session_id"], RESPOSTA_DETALHADA)

    # Assert
    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "Essa sessão não pertence ao usuário autenticado"}
    total = db.query(InterviewAnswer).filter(InterviewAnswer.session_id == uuid.UUID(sessao["session_id"]))
    assert total.count() == 0


# --- Fluxo entre recursos: sessão criada pelo POST /interviews ---------------


def test_answer_em_sessao_criada_pela_ia_deve_retornar_200_com_pergunta_adaptada_pelo_gemini(
    api, db, gemini_falso
):
    # Arrange — cria a sessão pelo endpoint do módulo questions
    _, headers = usuario_autenticado(api, "fluxoia")
    gemini_falso.responder({"questions": perguntas_geradas()})
    sessao = api.post("/interviews", json=montar_entrevista_ia("comportamental"), headers=headers).json()
    gemini_falso.responder({"question": "Qual foi o resultado concreto dessa decisão?"})
    texto = "Liderei a revisão do processo de deploy e reduzimos as falhas em produção."

    # Act
    resposta = responder(api, headers, sessao["session_id"], texto)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["adapted"] is True
    assert resposta.json()["question"] == "Qual foi o resultado concreto dessa decisão?"
    prompt_adaptacao = gemini_falso.prompts[-1]
    assert "Pergunta 1 sobre a vaga?" in prompt_adaptacao
    assert texto in prompt_adaptacao
    gravada = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == uuid.UUID(sessao["session_id"])
    ).one()
    assert gravada.question_text == "Pergunta 1 sobre a vaga?"


def test_answer_em_sessao_da_ia_com_gemini_fora_do_ar_deve_retornar_200_com_proxima_pergunta_gerada(
    api, gemini_falso
):
    # Arrange — a adaptação falha (nenhuma resposta preparada para o Gemini)
    _, headers = usuario_autenticado(api, "fallback")
    gemini_falso.responder({"questions": perguntas_geradas()})
    sessao = api.post("/interviews", json=montar_entrevista_ia(), headers=headers).json()

    # Act
    resposta = responder(api, headers, sessao["session_id"], RESPOSTA_DETALHADA)

    # Assert — a entrevista continua com a 2ª pergunta já gerada para a sessão
    assert resposta.status_code == 200
    assert resposta.json()["adapted"] is False
    assert resposta.json()["question"] == "Pergunta 2 sobre a vaga?"
    assert resposta.json()["finished"] is False
