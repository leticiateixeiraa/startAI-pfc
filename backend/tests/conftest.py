"""
Configuração compartilhada de toda a suíte de testes (pytest carrega este
arquivo sozinho, antes de qualquer teste).

O que ele garante:

1. BANCO DE TESTE DESCARTÁVEL — a aplicação inteira passa a usar um SQLite em
   memória no lugar do PostgreSQL de desenvolvimento. É o equivalente, em
   Python, ao perfil "test" com H2 do Spring: o banco nasce vazio quando o
   pytest começa e some quando ele termina. Nenhum teste lê ou grava no banco
   de desenvolvimento, e não é preciso ter PostgreSQL nem `.env` para rodar.

2. NENHUM SERVIÇO EXTERNO REAL — Gemini e SMTP ficam bloqueados por padrão.
   O teste que precisa deles troca explicitamente por um mock.

Nada aqui altera o código de produção: a troca do banco é feita apenas em
tempo de teste, substituindo o `engine` do SQLAlchemy antes de a aplicação
ser importada.
"""
import os
from datetime import datetime, timezone

# As variáveis precisam existir ANTES de importar a aplicação, porque
# `app.models.base` e `app.auth.service` se recusam a carregar sem elas.
# Usamos atribuição direta (e não setdefault) para que um `.env` real da
# máquina nunca seja usado pelos testes.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "chave-exclusiva-dos-testes-automatizados"

import pytest  # noqa: E402
from sqlalchemy import DateTime, create_engine, event, inspect  # noqa: E402
from sqlalchemy.dialects.sqlite.base import DATETIME as SQLITE_DATETIME  # noqa: E402
from sqlalchemy.orm.attributes import set_committed_value  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models.base as base  # noqa: E402


engine_de_teste = create_engine(
    "sqlite://",
    # StaticPool mantém UMA conexão viva: é ela que guarda o banco em memória.
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)


# --- Datas com fuso horário no SQLite ---------------------------------------
# O PostgreSQL devolve colunas `DateTime(timezone=True)` já com fuso (UTC).
# O SQLite guarda a data sem o fuso. A função abaixo recoloca o UTC toda vez
# que um registro é lido do banco, para o banco de teste se comportar como o
# de produção. Sem isso, comparações como
# `expires_at < datetime.now(timezone.utc)` (validade do token de redefinição
# de senha) quebrariam só no banco de teste.
def _devolver_datas_com_fuso(registro, *_):
    for atributo in inspect(type(registro)).column_attrs:
        tipo = atributo.columns[0].type
        if not (isinstance(tipo, DateTime) and tipo.timezone):
            continue
        valor = registro.__dict__.get(atributo.key)
        if isinstance(valor, datetime) and valor.tzinfo is None:
            set_committed_value(
                registro, atributo.key, valor.replace(tzinfo=timezone.utc)
            )


event.listen(base.Base, "load", _devolver_datas_com_fuso, propagate=True)
event.listen(base.Base, "refresh", _devolver_datas_com_fuso, propagate=True)


# O listener acima só cobre objetos carregados inteiros (db.query(Model)).
# Consultas que pedem só a coluna (db.query(Model.created_at)), como as
# métricas do painel administrativo, recebem a data direto do driver e
# continuavam sem fuso. Em uma máquina com fuso de Brasília, depois das 21h
# (quando em UTC já é o dia seguinte), isso jogava a entrevista para o dia
# errado e fazia o teste de métricas falhar só no banco de teste. Aqui o
# próprio tipo DATETIME do SQLite passa a devolver as colunas
# `DateTime(timezone=True)` com UTC, igual ao PostgreSQL.
_processador_original = SQLITE_DATETIME.result_processor


def _processador_com_fuso(self, dialect, coltype):
    processar = _processador_original(self, dialect, coltype)
    if not self.timezone:
        return processar

    def _processar(valor):
        valor = processar(valor) if processar else valor
        if isinstance(valor, datetime) and valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor

    return _processar


SQLITE_DATETIME.result_processor = _processador_com_fuso

# Troca o banco usado pela aplicação inteira. Como isso acontece antes de
# `app.main` ser importado, o `from app.models.base import engine` de lá já
# recebe o engine de teste.
base.engine = engine_de_teste
base.SessionLocal.configure(bind=engine_de_teste)

from app.main import app  # noqa: E402,F401  (registra todos os models)


def _servico_externo_bloqueado(*args, **kwargs):
    raise AssertionError(
        "Um teste tentou acessar um serviço externo real (Gemini ou SMTP). "
        "Substitua a dependência por um mock."
    )


@pytest.fixture(autouse=True)
def sem_servicos_externos(monkeypatch):
    """Rede de segurança aplicada a TODOS os testes."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("smtplib.SMTP", _servico_externo_bloqueado)
    monkeypatch.setattr(
        "app.questions.llm_service.genai.Client", _servico_externo_bloqueado
    )
