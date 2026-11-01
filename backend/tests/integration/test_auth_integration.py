"""
Testes de integração do AuthRouter (app/auth/router.py).
Responsável pelo módulo: Letícia Teixeira da Rocha Batista.

Endpoints: POST /auth/register, POST /auth/login, GET /auth/me,
POST /auth/forgot-password e POST /auth/reset-password.

Cada teste faz requisições HTTP reais ao servidor de teste (porta
aleatória). O único componente simulado é o envio de e-mail por SMTP
(serviço externo), na fixture `emails_enviados`.
"""
import uuid
from datetime import datetime, timedelta, timezone

from app.audit.models import AuditLog
from app.auth.models import PasswordResetToken, User
from app.auth.service import gerar_hash_token, verificar_senha

from tests.integration.apoio import SENHA, autenticar, cadastrar, montar_cadastro

NOVA_SENHA = "NovaSenha#2027"
MENSAGEM_ESQUECI_SENHA = "Se esse e-mail estiver cadastrado, você vai receber um link de redefinição."
MENSAGEM_LINK_INVALIDO = "Link inválido ou expirado. Solicite uma nova redefinição."


def _pedir_redefinicao(api, email, emails_enviados) -> str:
    resposta = api.post("/auth/forgot-password", json={"email": email})
    assert resposta.status_code == 200, resposta.text
    return emails_enviados[-1][1]


# --- POST /auth/register -----------------------------------------------------


def test_register_com_dados_validos_deve_retornar_201_e_persistir_usuario_com_senha_criptografada(api, db):
    # Arrange
    cadastro = montar_cadastro("cadastro")
    cadastro["email"] = cadastro["email"].upper()  # e-mail é normalizado

    # Act
    resposta = api.post("/auth/register", json=cadastro)

    # Assert
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert uuid.UUID(corpo["id"])
    assert corpo["email"] == cadastro["email"].lower()
    assert corpo["name"] == "Pessoa de Teste"
    assert corpo["role"] == "user"
    assert set(corpo) == {"id", "email", "name", "role"}  # nunca devolve a senha

    usuario = db.query(User).filter(User.id == uuid.UUID(corpo["id"])).one()
    assert usuario.hashed_password != SENHA
    assert verificar_senha(SENHA, usuario.hashed_password)
    assert usuario.terms_version == "1.0"
    assert usuario.terms_accepted_at is not None  # consentimento LGPD registrado
    assert usuario.is_active is True


def test_register_com_email_ja_cadastrado_deve_retornar_400_sem_duplicar_conta(api, db):
    # Arrange
    existente = cadastrar(api, "duplicado")
    repetido = montar_cadastro()
    repetido["email"] = existente["email"].upper()

    # Act
    resposta = api.post("/auth/register", json=repetido)

    # Assert
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": "E-mail já cadastrado"}
    assert db.query(User).filter(User.email == existente["email"]).count() == 1


def test_register_com_senha_sem_caractere_especial_deve_retornar_422_e_nao_criar_conta(api, db):
    # Arrange
    cadastro = montar_cadastro("senhafraca", password="SemEspecial2026")

    # Act
    resposta = api.post("/auth/register", json=cadastro)

    # Assert
    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["loc"] == ["body", "password"]
    assert "caractere especial" in erro["msg"]
    assert db.query(User).filter(User.email == cadastro["email"]).count() == 0


def test_register_sem_aceitar_termos_deve_retornar_422_com_mensagem_de_consentimento(api, db):
    # Arrange
    cadastro = montar_cadastro("semtermos", terms_accepted=False)

    # Act
    resposta = api.post("/auth/register", json=cadastro)

    # Assert
    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["loc"] == ["body", "terms_accepted"]
    assert "aceitar o Termo de Uso" in erro["msg"]
    assert db.query(User).filter(User.email == cadastro["email"]).count() == 0


def test_register_enviando_role_admin_deve_retornar_201_com_papel_user(api, db):
    # Arrange — tentativa de escalar privilégio pelo cadastro público
    cadastro = montar_cadastro("escalada", role="admin")

    # Act
    resposta = api.post("/auth/register", json=cadastro)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["role"] == "user"
    assert db.query(User).filter(User.email == cadastro["email"]).one().role == "user"


# --- POST /auth/login --------------------------------------------------------


def test_login_com_credenciais_validas_deve_retornar_200_com_token_bearer_e_auditar(api, db):
    # Arrange
    usuario = cadastrar(api, "login")

    # Act — e-mail em maiúsculas também deve funcionar
    resposta = api.post("/auth/login", json={"email": usuario["email"].upper(), "password": SENHA})

    # Assert
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"].count(".") == 2  # formato JWT
    acoes = {
        log.action
        for log in db.query(AuditLog).filter(AuditLog.user_id == uuid.UUID(usuario["id"])).all()
    }
    assert "auth.login" in acoes


def test_login_com_senha_errada_ou_email_inexistente_deve_retornar_401_identico(api, db):
    # Arrange
    usuario = cadastrar(api, "loginerrado")

    # Act
    senha_errada = api.post("/auth/login", json={"email": usuario["email"], "password": "Errada#2026"})
    inexistente = api.post(
        "/auth/login", json={"email": f"ninguem_{uuid.uuid4().hex}@example.com", "password": SENHA}
    )

    # Assert — mesma resposta: não dá para descobrir quais e-mails têm conta
    assert senha_errada.status_code == 401
    assert inexistente.status_code == 401
    assert senha_errada.json() == {"detail": "E-mail ou senha inválidos"}
    assert inexistente.json() == senha_errada.json()
    falhas = db.query(AuditLog).filter(
        AuditLog.user_id == uuid.UUID(usuario["id"]), AuditLog.action == "auth.login_failed"
    )
    assert falhas.count() == 1


# --- GET /auth/me ------------------------------------------------------------


def test_me_com_token_valido_deve_retornar_200_com_dados_do_usuario(api):
    # Arrange
    usuario = cadastrar(api, "me")
    headers = autenticar(api, usuario["email"])

    # Act
    resposta = api.get("/auth/me", headers=headers)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json() == {
        "id": usuario["id"],
        "email": usuario["email"],
        "name": "Pessoa de Teste",
        "role": "user",
    }


def test_me_sem_token_deve_retornar_401_com_header_www_authenticate_bearer(api):
    # Act
    resposta = api.get("/auth/me")

    # Assert
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Not authenticated"}
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


def test_me_com_token_adulterado_deve_retornar_401_token_invalido(api):
    # Arrange
    usuario = cadastrar(api, "adulterado")
    token = autenticar(api, usuario["email"])["Authorization"]

    # Act — troca a assinatura do JWT
    resposta = api.get("/auth/me", headers={"Authorization": token[:-4] + "abcd"})

    # Assert
    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Token inválido ou expirado"}
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


# --- POST /auth/forgot-password ---------------------------------------------


def test_forgot_password_com_email_cadastrado_deve_retornar_200_enviar_link_e_gravar_token_com_hash(
    api, db, emails_enviados
):
    # Arrange
    usuario = cadastrar(api, "esqueci")

    # Act
    resposta = api.post("/auth/forgot-password", json={"email": usuario["email"]})

    # Assert
    assert resposta.status_code == 200
    assert resposta.json() == {"message": MENSAGEM_ESQUECI_SENHA}
    assert len(emails_enviados) == 1
    destinatario, token_bruto = emails_enviados[0]
    assert destinatario == usuario["email"]

    registro = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == uuid.UUID(usuario["id"])
    ).one()
    assert registro.token_hash == gerar_hash_token(token_bruto)
    assert registro.token_hash != token_bruto  # banco nunca guarda o token puro
    assert registro.used_at is None
    assert registro.expires_at > datetime.now(timezone.utc)


def test_forgot_password_com_email_desconhecido_deve_retornar_200_com_mesma_mensagem_sem_enviar(
    api, emails_enviados
):
    # Act
    resposta = api.post("/auth/forgot-password", json={"email": f"fantasma_{uuid.uuid4().hex}@example.com"})

    # Assert — não revela se o e-mail existe
    assert resposta.status_code == 200
    assert resposta.json() == {"message": MENSAGEM_ESQUECI_SENHA}
    assert emails_enviados == []


def test_forgot_password_com_smtp_nao_configurado_deve_retornar_502(api):
    # Arrange — sem a fixture emails_enviados, o serviço real de e-mail é
    # usado e falha por falta das variáveis SMTP (nenhuma conexão é aberta).
    usuario = cadastrar(api, "semsmtp")

    # Act
    resposta = api.post("/auth/forgot-password", json={"email": usuario["email"]})

    # Assert
    assert resposta.status_code == 502
    assert resposta.json() == {
        "detail": "Não foi possível enviar o e-mail agora. Tente de novo mais tarde."
    }


# --- POST /auth/reset-password ----------------------------------------------


def test_reset_password_com_token_valido_deve_retornar_200_e_trocar_a_senha_no_banco(
    api, db, emails_enviados
):
    # Arrange
    usuario = cadastrar(api, "reset")
    token = _pedir_redefinicao(api, usuario["email"], emails_enviados)

    # Act
    resposta = api.post("/auth/reset-password", json={"token": token, "new_password": NOVA_SENHA})

    # Assert
    assert resposta.status_code == 200
    assert resposta.json() == {"message": "Senha redefinida com sucesso."}
    login_nova = api.post("/auth/login", json={"email": usuario["email"], "password": NOVA_SENHA})
    login_antiga = api.post("/auth/login", json={"email": usuario["email"], "password": SENHA})
    assert login_nova.status_code == 200
    assert login_antiga.status_code == 401
    registro = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == uuid.UUID(usuario["id"])
    ).one()
    assert registro.used_at is not None


def test_reset_password_com_token_ja_usado_deve_retornar_400(api, emails_enviados):
    # Arrange
    usuario = cadastrar(api, "reuso")
    token = _pedir_redefinicao(api, usuario["email"], emails_enviados)
    primeira = api.post("/auth/reset-password", json={"token": token, "new_password": NOVA_SENHA})
    assert primeira.status_code == 200

    # Act
    segunda = api.post("/auth/reset-password", json={"token": token, "new_password": "Outra#Senha99"})

    # Assert
    assert segunda.status_code == 400
    assert segunda.json() == {"detail": MENSAGEM_LINK_INVALIDO}


def test_reset_password_com_token_expirado_deve_retornar_400_e_manter_senha_antiga(
    api, db, emails_enviados
):
    # Arrange — não há endpoint para envelhecer o link, então a validade é
    # vencida direto no banco de teste.
    usuario = cadastrar(api, "expirado")
    token = _pedir_redefinicao(api, usuario["email"], emails_enviados)
    registro = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == gerar_hash_token(token)
    ).one()
    registro.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    # Act
    resposta = api.post("/auth/reset-password", json={"token": token, "new_password": NOVA_SENHA})

    # Assert
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": MENSAGEM_LINK_INVALIDO}
    assert api.post("/auth/login", json={"email": usuario["email"], "password": SENHA}).status_code == 200


def test_reset_password_com_token_inexistente_deve_retornar_400(api):
    # Act
    resposta = api.post(
        "/auth/reset-password", json={"token": "token-que-nunca-foi-emitido", "new_password": NOVA_SENHA}
    )

    # Assert
    assert resposta.status_code == 400
    assert resposta.json() == {"detail": MENSAGEM_LINK_INVALIDO}
