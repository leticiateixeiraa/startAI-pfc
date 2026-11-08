"""Testes unitários da leitura das variáveis de ambiente (app/config.py)."""
from app import config


def test_deve_converter_url_postgres_do_render_para_o_formato_do_sqlalchemy(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://usuario:senha@host:5432/startai")

    assert config.database_url() == "postgresql://usuario:senha@host:5432/startai"


def test_deve_manter_url_que_ja_esta_no_formato_certo(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:senha@localhost:5432/entrevistaia")

    assert config.database_url() == "postgresql://postgres:senha@localhost:5432/entrevistaia"


def test_cors_deve_separar_por_virgula_e_ignorar_espacos_e_barra_final(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://startai.vercel.app/ ,")

    assert config.cors_origins() == ["http://localhost:5173", "https://startai.vercel.app"]


def test_cors_sem_variavel_deve_liberar_so_o_vite_local(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert config.cors_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]
