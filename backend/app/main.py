"""
Entrypoint da API. Cada integrante registra o próprio router aqui
(um `include_router` por módulo) — evita conflito de merge nos outros arquivos.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.models.base import Base, engine
from app.auth.router import router as auth_router
from app.interview.router import router as interview_router
from app.questions.router import router as questions_router
from app.audit.router import router as audit_router
from app.roadmap.router import router as roadmap_router
from app.admin.router import router as admin_router


app = FastAPI(title="StartAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # URLs do Vite em dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(interview_router)
app.include_router(questions_router)
app.include_router(audit_router)
app.include_router(roadmap_router)
app.include_router(admin_router)


@app.on_event("startup")
def on_startup():
    # Cria as tabelas que ainda não existirem (uso simples em dev;
    # em produção prefira Alembic para migrações versionadas).
    Base.metadata.create_all(bind=engine)
    # Compatibilidade com bancos criados antes da persistência da modalidade.
    columns = {column["name"] for column in inspect(engine).get_columns("interview_sessions")}
    if "presentation_type" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE interview_sessions ADD COLUMN presentation_type VARCHAR")
            )

    # feat(lgpd): compatibilidade com bancos criados antes do registro de consentimento.
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.begin() as connection:
        if "terms_accepted_at" not in user_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN terms_accepted_at TIMESTAMPTZ")
            )
        if "terms_version" not in user_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN terms_version VARCHAR(20)")
            )
        # feat(admin): compatibilidade com bancos criados antes dos papéis.
        if "role" not in user_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
            )
        if "is_active" not in user_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE")
            )


@app.get("/health")
def health_check():
    return {"status": "ok"}