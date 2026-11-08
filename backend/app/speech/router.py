"""
feat(speech): POST /interviews/{session_id}/transcribe

Recebe o áudio da resposta (multipart), devolve o texto transcrito para o
usuário revisar e só então enviar por POST /interviews/{id}/answer. O áudio
não é armazenado.
"""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.audit.service import record_event
from app.auth.dependencies import get_current_user
from app.interview.models import InterviewSession
from app.models.base import get_db
from app.questions.llm_service import LLMGenerationError
from app.speech import service
from app.speech.schemas import TranscriptionOut

router = APIRouter(prefix="/interviews", tags=["speech"])


@router.post("/{session_id}/transcribe", response_model=TranscriptionOut)
async def transcribe(
    session_id: uuid.UUID,
    request: Request,
    audio: UploadFile = File(...),
    duration_seconds: float | None = Form(None),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão de entrevista não encontrada")
    if str(session.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Essa sessão não pertence ao usuário autenticado")
    if session.finished:
        raise HTTPException(status_code=400, detail="Essa sessão de entrevista já foi finalizada")

    # Lê no máximo o limite + 1 byte: um arquivo enorme é rejeitado sem
    # carregar tudo na memória.
    data = await audio.read(service.MAX_AUDIO_BYTES + 1)
    try:
        mime_type = service.validate_audio(data, audio.content_type)
    except service.AudioValidationError as error:
        code = 413 if len(data) > service.MAX_AUDIO_BYTES else 415 if "Formato" in str(error) else 400
        raise HTTPException(status_code=code, detail=str(error)) from error

    # Duração: a do cabeçalho do WAV é a confiável; a do navegador é plano B.
    duration = service.wav_duration_seconds(data)
    if duration is None:
        duration = duration_seconds
    if duration is not None and not 0 < duration <= service.MAX_AUDIO_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"A resposta deve ter no máximo {service.MAX_AUDIO_SECONDS // 60} minutos.",
        )

    try:
        transcript = service.transcribe_audio(data, mime_type)
    except service.EmptyTranscriptError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except LLMGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    words = service.count_words(transcript)
    # Auditoria sem o conteúdo da fala: só metadados.
    record_event(
        db,
        "interview.audio_transcribed",
        uuid.UUID(user_id),
        "interview_session",
        str(session.id),
        {"duration_seconds": duration, "word_count": words},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return TranscriptionOut(transcript=transcript, duration_seconds=duration, word_count=words)
