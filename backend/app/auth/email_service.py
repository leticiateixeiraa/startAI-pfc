"""
Envio de e-mails transacionais (recuperação de senha).

Usa smtplib puro, sem lib extra no requirements.txt. Se as variáveis de
SMTP não estiverem configuradas, levanta um erro claro em vez de falhar
silenciosamente ou travar o cadastro/login de todo mundo.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app import config  # noqa: F401  (carrega o .env)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class ErroEnvioEmail(Exception):
    pass


def enviar_email_redefinicao_senha(email_destino: str, token: str) -> None:
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        raise ErroEnvioEmail(
            "SMTP não configurado. Preencha SMTP_HOST, SMTP_USER e SMTP_PASSWORD no .env."
        )

    link_redefinicao = f"{FRONTEND_URL}/reset-password?token={token}"

    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = "StartAI — Redefinição de senha"
    mensagem["From"] = SMTP_FROM
    mensagem["To"] = email_destino

    corpo = (
        "Recebemos uma solicitação para redefinir sua senha no StartAI.\n\n"
        f"Clique no link abaixo para criar uma nova senha (válido por 30 minutos):\n{link_redefinicao}\n\n"
        "Se você não pediu essa redefinição, pode ignorar este e-mail."
    )
    mensagem.attach(MIMEText(corpo, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.starttls()
        servidor.login(SMTP_USER, SMTP_PASSWORD)
        servidor.sendmail(SMTP_FROM, email_destino, mensagem.as_string())