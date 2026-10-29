"""
test(admin): testes do painel administrativo e do controle de acesso por papel.

Cada teste cria os próprios usuários (e-mails aleatórios). O administrador é
promovido pela mesma função usada pelo script `promote_admin`, nunca pela API.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.scripts.promote_admin import alterar_papel, main as promote_main

SENHA = "senha-forte-123!"


def email_unico(prefixo: str) -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:8]}@example.com"


def _cadastrar(client: TestClient, prefixo: str, **extra) -> str:
    email = email_unico(prefixo)
    resposta = client.post(
        "/auth/register",
        json={"email": email, "password": SENHA, "name": "Pessoa Teste", "terms_accepted": True, **extra},
    )
    assert resposta.status_code == 201
    return email


def _login(client: TestClient, email: str) -> dict:
    resposta = client.post("/auth/login", json={"email": email, "password": SENHA})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def _admin(client: TestClient) -> dict:
    email = _cadastrar(client, "admin")
    alterar_papel(email)
    return _login(client, email)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


ROTAS_ADMIN = [
    ("get", "/admin/users"),
    ("get", "/admin/audit/logs"),
    ("get", "/admin/metrics"),
    ("patch", f"/admin/users/{uuid.uuid4()}"),
]


def _chamar(client, metodo, rota, **kwargs):
    if metodo == "patch":
        return client.patch(rota, json={"is_active": False}, **kwargs)
    return client.get(rota, **kwargs)


@pytest.mark.parametrize("metodo,rota", ROTAS_ADMIN)
def test_usuario_comum_recebe_403_nas_rotas_admin(client, metodo, rota):
    headers = _login(client, _cadastrar(client, "comum"))
    resposta = _chamar(client, metodo, rota, headers=headers)
    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Acesso restrito a administradores"


@pytest.mark.parametrize("metodo,rota", ROTAS_ADMIN)
def test_sem_token_recebe_401_nas_rotas_admin(client, metodo, rota):
    resposta = _chamar(client, metodo, rota)
    assert resposta.status_code == 401


def test_cadastro_publico_ignora_role_enviado_no_corpo(client):
    email = _cadastrar(client, "espertinho", role="admin")
    headers = _login(client, email)

    assert client.get("/auth/me", headers=headers).json()["role"] == "user"
    assert client.get("/admin/metrics", headers=headers).status_code == 403


def test_me_informa_o_papel_do_admin(client):
    headers = _admin(client)
    assert client.get("/auth/me", headers=headers).json()["role"] == "admin"


def test_admin_lista_usuarios_sem_ver_respostas(client):
    headers = _admin(client)
    email = _cadastrar(client, "listado")

    resposta = client.get("/admin/users", params={"search": email}, headers=headers)

    assert resposta.status_code == 200
    usuarios = resposta.json()
    assert [u["email"] for u in usuarios] == [email]
    assert set(usuarios[0]) == {"id", "email", "name", "role", "is_active", "created_at", "interview_count"}


def test_admin_desativa_conta_que_perde_acesso_na_hora(client):
    headers_admin = _admin(client)
    email = _cadastrar(client, "bloqueado")
    headers_usuario = _login(client, email)
    alvo = client.get("/admin/users", params={"search": email}, headers=headers_admin).json()[0]

    resposta = client.patch(f"/admin/users/{alvo['id']}", json={"is_active": False}, headers=headers_admin)

    assert resposta.status_code == 200
    assert resposta.json()["is_active"] is False
    # O token antigo deixa de valer imediatamente
    assert client.get("/auth/me", headers=headers_usuario).status_code == 401
    # E um novo login é recusado
    login = client.post("/auth/login", json={"email": email, "password": SENHA})
    assert login.status_code == 403


def test_login_bloqueado_e_desbloqueio_ficam_na_auditoria(client):
    headers_admin = _admin(client)
    email = _cadastrar(client, "auditado")
    alvo = client.get("/admin/users", params={"search": email}, headers=headers_admin).json()[0]

    client.patch(f"/admin/users/{alvo['id']}", json={"is_active": False}, headers=headers_admin)
    client.post("/auth/login", json={"email": email, "password": SENHA})
    client.patch(f"/admin/users/{alvo['id']}", json={"is_active": True}, headers=headers_admin)

    logs = client.get("/admin/audit/logs", params={"user_id": alvo["id"]}, headers=headers_admin).json()
    acoes = {log["action"] for log in logs}
    assert "auth.login_blocked" in acoes

    eventos_admin = client.get("/admin/audit/logs", params={"action": "admin.user_blocked"}, headers=headers_admin).json()
    assert any(log["resource_id"] == alvo["id"] for log in eventos_admin)
    # Depois de reativada, a conta volta a logar
    assert client.post("/auth/login", json={"email": email, "password": SENHA}).status_code == 200


def test_login_de_conta_desativada_com_senha_errada_nao_revela_situacao(client):
    headers_admin = _admin(client)
    email = _cadastrar(client, "discreto")
    alvo = client.get("/admin/users", params={"search": email}, headers=headers_admin).json()[0]
    client.patch(f"/admin/users/{alvo['id']}", json={"is_active": False}, headers=headers_admin)

    resposta = client.post("/auth/login", json={"email": email, "password": "senha-errada-1!"})

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha inválidos"


def test_admin_nao_pode_desativar_a_propria_conta(client):
    email = _cadastrar(client, "admin_self")
    alterar_papel(email)
    headers = _login(client, email)
    meu_id = client.get("/auth/me", headers=headers).json()["id"]

    resposta = client.patch(f"/admin/users/{meu_id}", json={"is_active": False}, headers=headers)

    assert resposta.status_code == 400


def test_desativar_usuario_inexistente_retorna_404(client):
    resposta = client.patch(f"/admin/users/{uuid.uuid4()}", json={"is_active": False}, headers=_admin(client))
    assert resposta.status_code == 404


def test_admin_ve_auditoria_de_todos_e_o_acesso_fica_registrado(client):
    headers = _admin(client)
    _cadastrar(client, "outro_usuario")

    logs = client.get("/admin/audit/logs", params={"action": "auth.registered", "limit": 500}, headers=headers).json()
    assert len({log["user_id"] for log in logs}) >= 2

    acessos = client.get("/admin/audit/logs", params={"action": "admin.audit_viewed"}, headers=headers).json()
    assert len(acessos) >= 1


def test_auditoria_recusa_intervalo_de_datas_invertido(client):
    resposta = client.get(
        "/admin/audit/logs",
        params={"date_from": "2026-11-10", "date_to": "2026-11-01"},
        headers=_admin(client),
    )
    assert resposta.status_code == 400


def test_auditoria_filtra_por_periodo(client):
    headers = _admin(client)
    resposta = client.get(
        "/admin/audit/logs",
        params={"date_from": "2000-01-01", "date_to": "2000-01-31"},
        headers=headers,
    )
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_metricas_contam_usuarios_e_entrevistas(client):
    headers = _admin(client)
    antes = client.get("/admin/metrics", headers=headers).json()

    headers_usuario = _login(client, _cadastrar(client, "metricas"))
    sessao = client.post("/interviews/mock-start", json={"category": "entrevista_de_emprego"}, headers=headers_usuario)
    assert sessao.status_code == 201

    depois = client.get("/admin/metrics", headers=headers).json()

    assert depois["total_users"] == antes["total_users"] + 1
    assert depois["total_interviews"] == antes["total_interviews"] + 1
    assert len(depois["interviews_per_day"]) == 30
    assert sum(dia["count"] for dia in depois["interviews_per_day"]) >= 1
    assert 0 <= depois["completion_rate"] <= 1
    assert depois["active_users"] + depois["blocked_users"] == depois["total_users"]


def test_script_promove_e_revoga_admin(client, capsys):
    email = _cadastrar(client, "script")

    assert promote_main([email]) == 0
    assert "admin" in capsys.readouterr().out
    assert client.get("/auth/me", headers=_login(client, email)).json()["role"] == "admin"

    assert promote_main([email, "--revoke"]) == 0
    assert client.get("/auth/me", headers=_login(client, email)).json()["role"] == "user"


def test_script_falha_com_email_inexistente(capsys):
    assert promote_main(["ninguem@example.com"]) == 1
    assert "Nenhuma conta" in capsys.readouterr().err


def test_eventos_de_entrevista_e_consentimento_registram_ip(client):
    headers_admin = _admin(client)
    email = _cadastrar(client, "com_ip")
    headers = _login(client, email)
    sessao = client.post("/interviews/mock-start", json={"category": "entrevista_de_emprego"}, headers=headers).json()
    client.post(f"/interviews/{sessao['session_id']}/answer", json={"answer_text": "Uma resposta com detalhes suficientes para o teste"}, headers=headers)

    alvo = client.get("/admin/users", params={"search": email}, headers=headers_admin).json()[0]
    logs = client.get("/admin/audit/logs", params={"user_id": alvo["id"]}, headers=headers_admin).json()

    por_acao = {log["action"]: log for log in logs}
    for acao in ("lgpd.consent_accepted", "interview.started", "interview.answer_submitted"):
        assert por_acao[acao]["ip_address"], acao
