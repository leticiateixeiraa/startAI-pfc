"""
Configuração central do SQLAlchemy: engine, sessão e Base declarativa.
Compartilhado por todos os módulos (auth, questions, interview).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config

DATABASE_URL = config.database_url()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não configurada. Rode `python scripts/configurar_env.py` "
        "na raiz do projeto (ou copie .env.example para .env)."
    )

# lc_messages=C deixa as mensagens de erro do PostgreSQL em inglês, sem
# acentos quebrados no Windows. A opção só existe no PostgreSQL.
connect_args = {"options": "-c lc_messages=C"} if DATABASE_URL.startswith("postgresql") else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    # Testa a conexão antes de usar: bancos gerenciados (Render) derrubam
    # conexões paradas, e sem isso a primeira requisição após um tempo falha.
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency do FastAPI para injetar uma sessão de banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
