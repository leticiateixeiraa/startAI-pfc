"""
test(auth-backend): adiciona testes de registro, login e /auth/me

Rode com: pytest
Requer um banco de teste configurado via variável de ambiente DATABASE_URL
(ou ajuste para usar SQLite em memória, se preferir isolar de vez os testes).

Cada teste abre seu próprio `with TestClient(app) as client:` para garantir
que o evento de startup (criação das tabelas) rode antes das chamadas —
sem isso, os testes dependem da ordem de execução e falham quando rodados
isoladamente.

Os e-mails usados em cada teste são gerados com um sufixo aleatório (uuid)
para que rodar `pytest` várias vezes seguidas contra o mesmo banco (sem
resetá-lo) nunca esbarre em "E-mail já cadastrado" de uma execução anterior.
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app


def email_unico(prefixo: str) -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:8]}@example.com"


def test_register_and_login():
    with TestClient(app) as client:
        payload = {
            "email": email_unico("teste_leticia"),
            "password": "senha-forte-123",
            "name": "Usuária de Teste",
            "terms_accepted": True,
        }

        register_response = client.post("/auth/register", json=payload)
        assert register_response.status_code == 201
        assert register_response.json()["email"] == payload["email"]

        login_response = client.post(
            "/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


def test_login_com_senha_errada_falha():
    with TestClient(app) as client:
        email = email_unico("outra_leticia")
        client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "senha-forte-123",
                "terms_accepted": True,
            },
        )
        response = client.post(
            "/auth/login",
            json={"email": email, "password": "senha-errada"},
        )
        assert response.status_code == 401


def test_me_retorna_usuario_autenticado():
    with TestClient(app) as client:
        payload = {
            "email": email_unico("teste_leticia"),
            "password": "senha-forte-123",
            "name": "Usuária de Teste",
            "terms_accepted": True,
        }
        client.post("/auth/register", json=payload)
        login_response = client.post(
            "/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        token = login_response.json()["access_token"]

        me_response = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == payload["email"]


def test_me_sem_token_falha():
    with TestClient(app) as client:
        response = client.get("/auth/me")
        assert response.status_code == 401