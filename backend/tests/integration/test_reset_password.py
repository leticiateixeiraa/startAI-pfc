"""
test(auth-backend): testa o fluxo de recuperação de senha (esqueci minha senha)

Rode com: pytest
Requer o mesmo banco de teste usado pelos demais testes (ver test_auth.py).

Como o envio de e-mail depende de SMTP configurado, esses testes usam
monkeypatch para substituir o envio real por uma função "muda" — assim os
testes rodam em qualquer máquina, mesmo sem .env de e-mail configurado.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.auth.models import PasswordResetToken
from app.auth.service import gerar_token_redefinicao
from app.main import app
from app.models.base import SessionLocal

SENHA_VALIDA = "senha-forte-123!"


def email_unico(prefixo: str) -> str:
    return f"{prefixo}_{uuid.uuid4().hex[:8]}@example.com"


def _cadastrar_usuario(client: TestClient, prefixo: str) -> str:
    email = email_unico(prefixo)
    client.post(
        "/auth/register",
        json={"email": email, "password": SENHA_VALIDA, "terms_accepted": True},
    )
    return email


def _criar_token_valido_no_banco(email: str) -> str:
    with SessionLocal() as db:
        from app.auth.models import User
        user = db.query(User).filter(User.email == email).one()
        token_bruto, hash_token = gerar_token_redefinicao()
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        ))
        db.commit()
    return token_bruto


def test_esqueci_senha_nao_revela_se_email_existe(monkeypatch):
    # Substitui o envio real de e-mail por uma função que não faz nada,
    # já que este teste não depende de SMTP configurado.
    monkeypatch.setattr(
        "app.auth.router.enviar_email_redefinicao_senha", lambda *a, **k: None
    )
    with TestClient(app) as client:
        email = _cadastrar_usuario(client, "esqueci_existe")

        resposta_existente = client.post("/auth/forgot-password", json={"email": email})
        resposta_inexistente = client.post(
            "/auth/forgot-password", json={"email": email_unico("esqueci_nao_existe")}
        )

        assert resposta_existente.status_code == 200
        assert resposta_inexistente.status_code == 200
        assert resposta_existente.json() == resposta_inexistente.json()


def test_redefinir_senha_com_token_valido_funciona():
    with TestClient(app) as client:
        email = _cadastrar_usuario(client, "redefinir_valido")
        token = _criar_token_valido_no_banco(email)

        resposta = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "nova-senha-456!"},
        )
        assert resposta.status_code == 200

        # Confirma que a senha nova realmente funciona no login.
        resposta_login = client.post(
            "/auth/login", json={"email": email, "password": "nova-senha-456!"}
        )
        assert resposta_login.status_code == 200


def test_redefinir_senha_com_token_invalido_falha():
    with TestClient(app) as client:
        resposta = client.post(
            "/auth/reset-password",
            json={"token": "token-que-nao-existe", "new_password": "nova-senha-456!"},
        )
        assert resposta.status_code == 400


def test_redefinir_senha_com_token_expirado_falha():
    with TestClient(app) as client:
        email = _cadastrar_usuario(client, "redefinir_expirado")
        with SessionLocal() as db:
            from app.auth.models import User
            user = db.query(User).filter(User.email == email).one()
            token_bruto, hash_token = gerar_token_redefinicao()
            db.add(PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token,
                # Token já nasce expirado, para o teste não depender de tempo real.
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            ))
            db.commit()

        resposta = client.post(
            "/auth/reset-password",
            json={"token": token_bruto, "new_password": "nova-senha-456!"},
        )
        assert resposta.status_code == 400


def test_redefinir_senha_com_token_ja_usado_falha():
    with TestClient(app) as client:
        email = _cadastrar_usuario(client, "redefinir_usado")
        token = _criar_token_valido_no_banco(email)

        primeira_tentativa = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "nova-senha-456!"},
        )
        assert primeira_tentativa.status_code == 200

        segunda_tentativa = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "outra-senha-789!"},
        )
        assert segunda_tentativa.status_code == 400