"""
Entrypoint da API. Cada integrante registra o próprio router aqui
(um `include_router` por módulo) — evita conflito de merge nos outros arquivos.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app import config
from app.models.base import Base, engine
from app.auth.router import router as auth_router
from app.interview.router import router as interview_router
from app.questions.router import router as questions_router
from app.audit.router import router as audit_router
from app.roadmap.router import interview_router as roadmap_interview_router
from app.roadmap.router import router as roadmap_router
from app.admin.router import router as admin_router
from app.evaluation.router import router as evaluation_router
from app.behavioral.router import router as behavioral_router
from app.onboarding.router import router as onboarding_router
from app.speech.router import router as speech_router
from app.jobs.router import router as jobs_router


app = FastAPI(title="StartAI API")

app.add_middleware(
    CORSMiddleware,
    # Em dev: o Vite (localhost:5173). Em produção: a URL da Vercel,
    # cadastrada em CORS_ORIGINS no painel do Render.
    allow_origins=config.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(interview_router)
app.include_router(questions_router)
app.include_router(audit_router)
app.include_router(roadmap_router)
app.include_router(roadmap_interview_router)
app.include_router(admin_router)
app.include_router(evaluation_router)
app.include_router(behavioral_router)
app.include_router(onboarding_router)
app.include_router(speech_router)
app.include_router(jobs_router)


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

    # feat(speech): compatibilidade com bancos criados antes das respostas por voz.
    answer_columns = {column["name"] for column in inspect(engine).get_columns("interview_answers")}
    with engine.begin() as connection:
        if "input_mode" not in answer_columns:
            connection.execute(
                text("ALTER TABLE interview_answers ADD COLUMN input_mode VARCHAR(10) NOT NULL DEFAULT 'text'")
            )
        if "audio_duration_seconds" not in answer_columns:
            connection.execute(
                text("ALTER TABLE interview_answers ADD COLUMN audio_duration_seconds DOUBLE PRECISION")
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

    # feat(feedback): compatibilidade com avaliações gravadas antes dos erros
    # apontados, da resposta sugerida e dos destaques gerais, e com sessões
    # criadas antes do nível da vaga.
    novas_colunas = {
        "interview_sessions": {
            "seniority": "VARCHAR(20)",
            "job_title": "VARCHAR(160)",
        },
        "interview_evaluations": {
            "highlights": "TEXT NOT NULL DEFAULT '[]'",
            "next_steps": "TEXT NOT NULL DEFAULT '[]'",
        },
        "answer_evaluations": {
            "mistakes": "TEXT NOT NULL DEFAULT '[]'",
            "suggested_answer": "TEXT",
        },
        # feat(roadmap-ia): trilha gerada a partir da avaliação da entrevista.
        "learning_roadmaps": {
            "session_id": "UUID UNIQUE REFERENCES interview_sessions(id)",
            "summary": "TEXT",
        },
        "learning_roadmap_items": {
            "focus": "TEXT",
            "estimated_time": "VARCHAR(60)",
            "practice": "TEXT",
            "tips": "TEXT NOT NULL DEFAULT '[]'",
            "resources": "TEXT NOT NULL DEFAULT '[]'",
        },
    }
    with engine.begin() as connection:
        for tabela, colunas in novas_colunas.items():
            existentes = {column["name"] for column in inspect(engine).get_columns(tabela)}
            for coluna, definicao in colunas.items():
                if coluna not in existentes:
                    connection.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"))


@app.get("/health")
def health_check():
    return {"status": "ok"}