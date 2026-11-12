"""
Testes de integração do AdminRouter (app/admin/router.py).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista.

Endpoints: GET /admin/users, PATCH /admin/users/{user_id},
GET /admin/audit/logs e GET /admin/metrics.

Inclui o trio de segurança exigido no enunciado no mesmo endpoint protegido
(GET /admin/users): sem token -> 401, usuário comum -> 403, admin -> 200.
"""
import uuid
from datetime import date, timedelta

from app.audit.models import AuditLog
from app.auth.models import User
from tests.integration.apoio import (
    SENHA,
    admin_autenticado,
    iniciar_entrevista_mock,
    responder,
    usuario_autenticado,
)

# --- Segurança: mesmo endpoint protegido, três perfis -----------------------


def test_listar_usuarios_sem_token_deve_retornar_401(api):
    # Act
    resposta = api.get("/admin/users")

    # Assert
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Not authenticated"}


def test_listar_usuarios_como_usuario_comum_deve_retornar_403(api):
    # Arrange
    _, headers_usuario = usuario_autenticado(api, "comum")

    # Act
    resposta = api.get("/admin/users", headers=headers_usuario)

    # Assert
    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "Acesso restrito a administradores"}


def test_listar_usuarios_como_admin_deve_retornar_200_com_contagem_de_entrevistas_sem_respostas(api):
    # Arrange — um aluno com uma entrevista respondida
    _, headers_admin = admin_autenticado(api)
    aluno, headers_aluno = usuario_autenticado(api, "listado")
    sessao = iniciar_entrevista_mock(api, headers_aluno)
    responder(api, headers_aluno, sessao["session_id"], "Resposta confidencial do aluno sobre a vaga.")

    # Act — a busca usa o e-mail único do aluno
    resposta = api.get("/admin/users", params={"search": aluno["email"]}, headers=headers_admin)

    # Assert
    assert resposta.status_code == 200
    usuarios = resposta.json()
    assert len(usuarios) == 1
    encontrado = usuarios[0]
    assert encontrado["id"] == aluno["id"]
    assert encontrado["role"] == "user"
    assert encontrado["is_active"] is True
    assert encontrado["interview_count"] == 1
    # LGPD: o admin vê só a quantidade, nunca o conteúdo das respostas
    assert "Resposta confidencial" not in resposta.text


# --- PATCH /admin/users/{user_id} -------------------------------------------


def test_atualizar_status_desativando_usuario_deve_retornar_200_e_bloquear_acesso_na_hora(api, db):
    # Arrange
    _, headers_admin = admin_autenticado(api)
    aluno, headers_aluno = usuario_autenticado(api, "desativado")

    # Act
    resposta = api.patch(f"/admin/users/{aluno['id']}", json={"is_active": False}, headers=headers_admin)

    # Assert — resposta, banco e efeito nos outros endpoints
    assert resposta.status_code == 200
    assert resposta.json()["id"] == aluno["id"]
    assert resposta.json()["is_active"] is False
    assert db.query(User).filter(User.id == uuid.UUID(aluno["id"])).one().is_active is False

    token_antigo = api.get("/auth/me", headers=headers_aluno)
    assert token_antigo.status_code == 401
    assert token_antigo.json() == {"detail": "Conta inexistente ou desativada"}

    novo_login = api.post("/auth/login", json={"email": aluno["email"], "password": SENHA})
    assert novo_login.status_code == 403
    assert novo_login.json() == {"detail": "Esta conta está desativada. Entre em contato com o suporte."}


def test_atualizar_status_reativando_usuario_deve_retornar_200_e_registrar_auditoria(api, db):
    # Arrange
    admin, headers_admin = admin_autenticado(api)
    aluno, _ = usuario_autenticado(api, "reativado")
    api.patch(f"/admin/users/{aluno['id']}", json={"is_active": False}, headers=headers_admin)

    # Act
    resposta = api.patch(f"/admin/users/{aluno['id']}", json={"is_active": True}, headers=headers_admin)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["is_active"] is True
    assert api.post("/auth/login", json={"email": aluno["email"], "password": SENHA}).status_code == 200
    acoes = [
        log.action
        for log in db.query(AuditLog).filter(
            AuditLog.resource_id == aluno["id"], AuditLog.user_id == uuid.UUID(admin["id"])
        )
    ]
    assert sorted(acoes) == ["admin.user_blocked", "admin.user_unblocked"]


def test_atualizar_status_da_propria_conta_deve_retornar_400_e_manter_admin_ativo(api, db):
    # Arrange
    admin, headers_admin = admin_autenticado(api)

    # Act
    resposta = api.patch(f"/admin/users/{admin['id']}", json={"is_active": False}, headers=headers_admin)

    # Assert
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": "Você não pode desativar a sua própria conta"}
    assert db.query(User).filter(User.id == uuid.UUID(admin["id"])).one().is_active is True


def test_atualizar_status_de_usuario_inexistente_deve_retornar_404(api):
    # Arrange
    _, headers_admin = admin_autenticado(api)

    # Act
    resposta = api.patch(f"/admin/users/{uuid.uuid4()}", json={"is_active": False}, headers=headers_admin)

    # Assert
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Usuário não encontrado"}


# --- GET /admin/audit/logs ---------------------------------------------------


def test_listar_auditoria_filtrando_por_usuario_deve_retornar_200_e_registrar_o_proprio_acesso(api, db):
    # Arrange
    admin, headers_admin = admin_autenticado(api)
    aluno, _ = usuario_autenticado(api, "auditado")

    # Act
    resposta = api.get("/admin/audit/logs", params={"user_id": aluno["id"]}, headers=headers_admin)

    # Assert
    assert resposta.status_code == 200
    eventos = resposta.json()
    assert {evento["user_id"] for evento in eventos} == {aluno["id"]}
    assert {"auth.registered", "lgpd.consent_accepted", "auth.login"} <= {e["action"] for e in eventos}
    acesso = db.query(AuditLog).filter(
        AuditLog.user_id == uuid.UUID(admin["id"]), AuditLog.action == "admin.audit_viewed"
    )
    assert acesso.count() == 1
    assert aluno["id"] in acesso.one().details

    filtrados = api.get(
        "/admin/audit/logs",
        params={"user_id": aluno["id"], "action": "auth.registered", "limit": 1},
        headers=headers_admin,
    )
    assert filtrados.status_code == 200
    assert len(filtrados.json()) == 1
    assert filtrados.json()[0]["action"] == "auth.registered"


def test_listar_auditoria_com_data_inicial_depois_da_final_deve_retornar_400(api):
    # Arrange
    _, headers_admin = admin_autenticado(api)
    hoje = date.today()

    # Act
    resposta = api.get(
        "/admin/audit/logs",
        params={"date_from": hoje.isoformat(), "date_to": (hoje - timedelta(days=1)).isoformat()},
        headers=headers_admin,
    )

    # Assert
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": "A data inicial não pode ser depois da final"}


# --- GET /admin/metrics ------------------------------------------------------


def test_metricas_apos_nova_entrevista_finalizada_deve_retornar_200_com_totais_atualizados(api):
    # Arrange
    _, headers_admin = admin_autenticado(api)
    antes = api.get("/admin/metrics", headers=headers_admin).json()
    _, headers_aluno = usuario_autenticado(api, "metricas")
    sessao = iniciar_entrevista_mock(api, headers_aluno)
    resposta_longa = "Organizei as tarefas por impacto, conversei com o cliente e entreguei a solução combinada."
    for _ in range(4):  # o banco mock tem 4 perguntas
        responder(api, headers_aluno, sessao["session_id"], resposta_longa)

    # Act
    resposta = api.get("/admin/metrics", headers=headers_admin)

    # Assert
    assert resposta.status_code == 200
    depois = resposta.json()
    assert depois["total_users"] == antes["total_users"] + 1
    assert depois["total_interviews"] == antes["total_interviews"] + 1
    assert depois["finished_interviews"] == antes["finished_interviews"] + 1
    assert depois["total_answers"] == antes["total_answers"] + 4
    assert depois["active_users"] + depois["blocked_users"] == depois["total_users"]
    assert len(depois["interviews_per_day"]) == 30
    assert depois["interviews_per_day"][-1]["count"] >= 1  # hoje
