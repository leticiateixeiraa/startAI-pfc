"""
Testes de integração da exclusão de conta (LGPD, Art. 18, VI).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista.

Endpoints: DELETE /auth/me (o titular) e DELETE /admin/users/{id} (o admin).

Cada teste monta um usuário "completo" pela própria API (entrevista
finalizada, avaliação da IA, trilha de estudo e pedido de redefinição de
senha) e confere no banco que tudo foi apagado e que a auditoria foi
anonimizada, e não apagada.
"""
import uuid

from app.audit.models import AuditLog
from app.auth.models import PasswordResetToken, User
from app.evaluation.models import AnswerEvaluation, InterviewEvaluation
from app.interview.models import InterviewAnswer, InterviewQuestion, InterviewSession
from app.interview.service import QUESTION_BANK
from app.roadmap.models import LearningRoadmap, LearningRoadmapItem
from tests.integration.apoio import (
    SENHA,
    admin_autenticado,
    criar_roadmap,
    iniciar_entrevista_mock,
    montar_entrevista_ia,
    perguntas_geradas,
    responder,
    usuario_autenticado,
)

RESPOSTA = "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."
QUANTIDADE = len(QUESTION_BANK["entrevista_de_emprego"])


def _avaliacao_falsa() -> dict:
    return {
        "summary": "Boa entrevista.",
        "answers": [
            {
                "index": numero,
                "relevance": 8,
                "coherence": 8,
                "completeness": 7,
                "adequacy": 8,
                "feedback": "Boa resposta.",
                "strengths": ["Clareza"],
                "improvements": ["Cite números"],
            }
            for numero in range(1, QUANTIDADE + 1)
        ],
    }


def _usuario_com_dados(api, gemini_falso, emails_enviados, prefixo="titular"):
    """Cria um usuário com dados em todas as tabelas ligadas a ele."""
    usuario, headers = usuario_autenticado(api, prefixo)
    sessao = iniciar_entrevista_mock(api, headers)
    for _ in range(QUANTIDADE):
        responder(api, headers, sessao["session_id"], RESPOSTA)
    gemini_falso.responder(_avaliacao_falsa())
    assert api.post(f"/interviews/{sessao['session_id']}/evaluation", headers=headers).status_code == 201
    # Uma segunda entrevista, gerada "pela IA": é a que grava interview_questions.
    gemini_falso.responder({"questions": perguntas_geradas()})
    gerada = api.post("/interviews", json=montar_entrevista_ia(), headers=headers)
    assert gerada.status_code == 201, gerada.text
    criar_roadmap(api, headers)
    api.post("/auth/forgot-password", json={"email": usuario["email"]})
    return usuario, headers, [sessao["session_id"], gerada.json()["session_id"]]


def _excluir_minha_conta(api, headers, senha=SENHA):
    return api.request("DELETE", "/auth/me", json={"password": senha}, headers=headers)


def _contagens(db, user_id: uuid.UUID, session_ids: list[str]) -> dict:
    """Conta por ids conhecidos (e não por subconsulta no usuário), para
    pegar registros "órfãos" que sobrariam se a exclusão esquecesse algo."""
    db.expire_all()
    sessoes = [uuid.UUID(session_id) for session_id in session_ids]
    avaliacoes = db.query(InterviewEvaluation.id).filter(InterviewEvaluation.user_id == user_id)
    trilhas = db.query(LearningRoadmap.id).filter(LearningRoadmap.user_id == user_id)
    return {
        "usuario": db.query(User).filter_by(id=user_id).count(),
        "sessoes": db.query(InterviewSession).filter(InterviewSession.id.in_(sessoes)).count(),
        "perguntas": db.query(InterviewQuestion).filter(InterviewQuestion.session_id.in_(sessoes)).count(),
        "respostas": db.query(InterviewAnswer).filter(InterviewAnswer.session_id.in_(sessoes)).count(),
        "avaliacoes": db.query(InterviewEvaluation).filter_by(user_id=user_id).count(),
        "avaliacoes_respostas": db.query(AnswerEvaluation)
        .filter(AnswerEvaluation.evaluation_id.in_(avaliacoes))
        .count(),
        "trilhas": db.query(LearningRoadmap).filter_by(user_id=user_id).count(),
        "etapas": db.query(LearningRoadmapItem)
        .filter(LearningRoadmapItem.roadmap_id.in_(trilhas))
        .count(),
        "tokens": db.query(PasswordResetToken).filter_by(user_id=user_id).count(),
        "logs_vinculados": db.query(AuditLog).filter_by(user_id=user_id).count(),
    }


# --- DELETE /auth/me (o próprio titular) -------------------------------------


def test_titular_deve_excluir_a_conta_e_todos_os_dados_pessoais(api, db, gemini_falso, emails_enviados):
    # Arrange
    usuario, headers, session_ids = _usuario_com_dados(api, gemini_falso, emails_enviados)
    user_id = uuid.UUID(usuario["id"])
    antes = _contagens(db, user_id, session_ids)
    assert all(valor > 0 for valor in antes.values()), antes  # o cenário tem dado em tudo

    # Act
    resposta = _excluir_minha_conta(api, headers)

    # Assert
    assert resposta.status_code == 200, resposta.text
    assert all(valor == 0 for valor in _contagens(db, user_id, session_ids).values())


def test_exclusao_deve_anonimizar_a_auditoria_em_vez_de_apagar(api, db, gemini_falso, emails_enviados):
    usuario, headers, _ = _usuario_com_dados(api, gemini_falso, emails_enviados, "anonimizado")
    db.expire_all()
    logs_antes = db.query(AuditLog).filter_by(user_id=uuid.UUID(usuario["id"])).count()
    total_antes = db.query(AuditLog).count()

    _excluir_minha_conta(api, headers)

    db.expire_all()
    # Nenhum evento sumiu (+1 do próprio registro da exclusão)...
    assert db.query(AuditLog).count() == total_antes + 1
    # ...mas nenhum continua ligado à pessoa, nem por id de recurso.
    assert db.query(AuditLog).filter(AuditLog.resource_id == usuario["id"]).count() == 0
    evento = db.query(AuditLog).filter_by(action="lgpd.account_deleted").order_by(AuditLog.created_at.desc()).first()
    assert evento.user_id is None and evento.ip_address is None
    assert usuario["email"] not in (evento.details or "")
    assert logs_antes > 0


def test_depois_da_exclusao_o_token_deixa_de_valer_e_o_email_fica_livre(api, gemini_falso, emails_enviados):
    usuario, headers, _ = _usuario_com_dados(api, gemini_falso, emails_enviados, "livre")

    _excluir_minha_conta(api, headers)

    assert api.get("/auth/me", headers=headers).status_code == 401
    novo_cadastro = api.post(
        "/auth/register",
        json={"email": usuario["email"], "password": SENHA, "name": "De novo", "terms_accepted": True},
    )
    assert novo_cadastro.status_code == 201


def test_senha_errada_deve_retornar_400_e_nao_apagar_nada(api, db, gemini_falso, emails_enviados):
    usuario, headers, session_ids = _usuario_com_dados(api, gemini_falso, emails_enviados, "senhaerrada")
    antes = _contagens(db, uuid.UUID(usuario["id"]), session_ids)

    resposta = _excluir_minha_conta(api, headers, senha="Errada#2026")

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Senha incorreta"
    assert _contagens(db, uuid.UUID(usuario["id"]), session_ids) == antes


def test_exclusao_nao_deve_mexer_nos_dados_de_outro_usuario(api, db, gemini_falso, emails_enviados):
    _, headers_saindo, _ = _usuario_com_dados(api, gemini_falso, emails_enviados, "saindo")
    fica, _, sessao_fica = _usuario_com_dados(api, gemini_falso, emails_enviados, "fica")
    antes = _contagens(db, uuid.UUID(fica["id"]), sessao_fica)

    _excluir_minha_conta(api, headers_saindo)

    assert _contagens(db, uuid.UUID(fica["id"]), sessao_fica) == antes


def test_excluir_conta_sem_token_deve_retornar_401(api):
    assert api.request("DELETE", "/auth/me", json={"password": SENHA}).status_code == 401


def test_unico_admin_nao_pode_excluir_a_propria_conta(api, db):
    # Os testes compartilham o banco: rebaixa temporariamente os outros admins
    # para este ser o único administrador ativo.
    admin, headers = admin_autenticado(api)
    db.expire_all()
    outros = db.query(User).filter(User.role == "admin", User.id != uuid.UUID(admin["id"])).all()
    for outro in outros:
        outro.role = "user"
    db.commit()
    try:
        resposta = _excluir_minha_conta(api, headers)
    finally:
        for outro in outros:
            outro.role = "admin"
        db.commit()

    assert resposta.status_code == 400
    assert "única conta de administrador" in resposta.json()["detail"]


# --- DELETE /admin/users/{id} (pedido atendido pelo administrador) -----------


def test_admin_deve_excluir_usuario_e_ficar_registrado_na_auditoria(api, db, gemini_falso, emails_enviados):
    admin, headers_admin = admin_autenticado(api)
    usuario, _, session_ids = _usuario_com_dados(api, gemini_falso, emails_enviados, "pedido")
    # Um evento em que o usuário é o "alvo" de uma ação do admin.
    api.patch(f"/admin/users/{usuario['id']}", json={"is_active": False}, headers=headers_admin)

    resposta = api.delete(f"/admin/users/{usuario['id']}", headers=headers_admin)

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["deleted"]["interview_sessions"] == 2
    assert all(valor == 0 for valor in _contagens(db, uuid.UUID(usuario["id"]), session_ids).values())
    db.expire_all()
    evento = db.query(AuditLog).filter_by(action="admin.user_deleted", user_id=uuid.UUID(admin["id"])).one()
    assert evento.resource_id is None
    bloqueio = db.query(AuditLog).filter_by(action="admin.user_blocked", user_id=uuid.UUID(admin["id"])).one()
    assert bloqueio.resource_id is None  # o admin continua identificado, o alvo não


def test_admin_nao_pode_excluir_a_si_mesmo_nem_outro_admin(api):
    admin, headers = admin_autenticado(api)
    outro_admin, _ = admin_autenticado(api)

    a_si_mesmo = api.delete(f"/admin/users/{admin['id']}", headers=headers)
    outro = api.delete(f"/admin/users/{outro_admin['id']}", headers=headers)

    assert a_si_mesmo.status_code == 400
    assert outro.status_code == 400
    assert "administrador" in outro.json()["detail"]


def test_admin_excluindo_usuario_inexistente_deve_retornar_404(api):
    _, headers = admin_autenticado(api)

    assert api.delete(f"/admin/users/{uuid.uuid4()}", headers=headers).status_code == 404


def test_usuario_comum_nao_pode_usar_a_exclusao_do_admin(api):
    vitima, _ = usuario_autenticado(api, "vitima")
    _, headers_comum = usuario_autenticado(api, "comum")

    resposta = api.delete(f"/admin/users/{vitima['id']}", headers=headers_comum)

    assert resposta.status_code == 403
