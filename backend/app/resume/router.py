"""
feat(resume): análise de currículo por IA, na página "Meu perfil".

POST   /resume/analyze -> envia o currículo (PDF ou DOCX) e recebe a análise
GET    /resume/me      -> a última análise do usuário (ou null)
DELETE /resume/me      -> apaga a análise

O arquivo é lido em memória e descartado: só o resultado da análise é salvo.
Na auditoria vão apenas metadados (tipo do arquivo e nota), nunca o conteúdo.
"""
import os
import re
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import get_current_user
from app.models.base import get_db
from app.onboarding import service as onboarding_service
from app.onboarding.questionario import AREAS
from app.questions.llm_service import LLMGenerationError
from app.resume import extracao, service
from app.resume.llm_curriculo import NaoEhCurriculo, analisar_curriculo
from app.resume.schemas import ResumeAnalysisOut

router = APIRouter(prefix="/resume", tags=["resume"])


def _nome_do_arquivo(nome: str | None) -> str:
    # Só o nome, sem pasta, e sem caracteres de controle.
    base = os.path.basename((nome or "").replace("\\", "/"))
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return (base or "curriculo")[:255]


@router.post("/analyze", response_model=ResumeAnalysisOut)
async def analisar(
    request: Request,
    file: UploadFile = File(...),
    target_role: str | None = Form(None, max_length=120),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Lê no máximo o limite + 1 byte: arquivo enorme é recusado sem ir todo para a memória.
    dados = await file.read(extracao.MAX_BYTES + 1)
    try:
        tipo = extracao.detectar_tipo(dados)
        texto = extracao.extrair_texto_docx(dados) if tipo == "docx" else None
    except extracao.ArquivoInvalido as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error

    cargo = " ".join((target_role or "").split()) or None
    usuario = uuid.UUID(user_id)

    # A área do questionário de primeiro acesso (se ele respondeu) ajuda a IA a
    # ajustar as sugestões quando a vaga alvo não é informada.
    registro_area = onboarding_service.buscar(db, usuario)
    area = None
    if registro_area and registro_area.recommended_area in AREAS:
        area = AREAS[registro_area.recommended_area]["name"]

    try:
        resultado = analisar_curriculo(
            tipo=tipo, dados=dados, texto=texto, cargo_alvo=cargo, area_interesse=area
        )
    except NaoEhCurriculo as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LLMGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    registro = service.salvar(db, usuario, _nome_do_arquivo(file.filename), tipo, cargo, resultado)
    record_event(
        db,
        "resume.analyzed",
        usuario,
        "resume",
        str(registro.id),
        {"file_type": tipo, "score": resultado["overall_score"]},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(registro)
    return service.montar_saida(registro)


@router.get("/me", response_model=ResumeAnalysisOut | None)
def minha_analise(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    registro = service.buscar(db, uuid.UUID(user_id))
    return service.montar_saida(registro) if registro else None


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def excluir_analise(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    registro = service.buscar(db, uuid.UUID(user_id))
    if registro is not None:
        db.delete(registro)
        record_event(
            db,
            "resume.deleted",
            uuid.UUID(user_id),
            "resume",
            str(registro.id),
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
