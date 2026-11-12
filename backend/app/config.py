import os  
"""
Carregamento das variáveis de ambiente, em um lugar só.

O projeto usa UM arquivo .env na raiz do repositório, compartilhado pelo
backend e pelo frontend (ver .env.example). Para não quebrar a máquina de
quem ainda tem o antigo backend/.env, ele também é lido, mas sem sobrescrever
o que veio da raiz.

Em produção (Render) não existe arquivo .env: as variáveis vêm do painel do
serviço, e o load_dotenv simplesmente não encontra nada para carregar.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PASTA_BACKEND = Path(__file__).resolve().parent.parent
PASTA_RAIZ = PASTA_BACKEND.parent

# override=False: variável que já existe no ambiente (painel do Render,
# testes automatizados) sempre ganha do arquivo.
load_dotenv(PASTA_RAIZ / ".env", override=False)
load_dotenv(PASTA_BACKEND / ".env", override=False)


def database_url() -> str | None:
    url = os.getenv("DATABASE_URL")
    # Render e Heroku entregam a URL como "postgres://", que o SQLAlchemy 2
    # não aceita mais. Só o nome do esquema muda.
    if url and url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def cors_origins() -> list[str]:
    valor = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origem.strip().rstrip("/") for origem in valor.split(",") if origem.strip()]
