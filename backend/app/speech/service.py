"""
feat(speech): transcrição das respostas por voz (Speech-to-Text) com o Gemini.

O áudio é lido só em memória e descartado logo após a transcrição: nada é
gravado em disco nem no banco (compromisso de LGPD descrito no README). O que
fica salvo é apenas o texto e a duração, que a resposta usa depois.

A transcrição é LITERAL de propósito: hesitações e vícios de linguagem
("é...", "né", "tipo") são mantidos, porque o analisador de oratória (#5)
precisa deles para contar repetições e palavras por minuto.
"""
import io
import json
import logging
import os
import wave

from google import genai
from google.genai import types

from app.questions.llm_service import (
    LLMGenerationError,
    _generate_content,
    _generation_error_message,
)

logger = logging.getLogger(__name__)

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # ~5 min de WAV 16 kHz mono
MAX_AUDIO_SECONDS = 300

# Formatos de áudio aceitos pelo Gemini. O front converte tudo para WAV antes
# de enviar (MediaRecorder gera webm no Chrome e mp4 no Safari).
ALLOWED_MIME_TYPES = {
    "audio/wav": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/wave": "audio/wav",
    "audio/mp3": "audio/mp3",
    "audio/mpeg": "audio/mp3",
    "audio/aac": "audio/aac",
    "audio/ogg": "audio/ogg",
    "audio/flac": "audio/flac",
    "audio/aiff": "audio/aiff",
}


class AudioValidationError(ValueError):
    pass


class EmptyTranscriptError(RuntimeError):
    pass


def normalize_mime_type(content_type: str | None) -> str:
    base = (content_type or "").split(";")[0].strip().lower()
    mime = ALLOWED_MIME_TYPES.get(base)
    if not mime:
        raise AudioValidationError(
            "Formato de áudio não suportado. Envie um arquivo WAV, MP3, AAC, OGG, FLAC ou AIFF."
        )
    return mime


def validate_audio(data: bytes, content_type: str | None) -> str:
    """Valida tamanho e formato; devolve o MIME normalizado."""
    if not data:
        raise AudioValidationError("O áudio enviado está vazio.")
    if len(data) > MAX_AUDIO_BYTES:
        raise AudioValidationError("O áudio é grande demais (limite de 10 MB). Grave uma resposta mais curta.")
    return normalize_mime_type(content_type)


def wav_duration_seconds(data: bytes) -> float | None:
    """Duração real de um WAV, lida do cabeçalho. None se não for WAV legível.

    Preferimos esse valor ao informado pelo navegador, porque a duração
    alimenta o cálculo de palavras por minuto.
    """
    try:
        with wave.open(io.BytesIO(data)) as arquivo:
            frames, taxa = arquivo.getnframes(), arquivo.getframerate()
            return frames / float(taxa) if taxa else None
    except (wave.Error, EOFError):
        return None


def count_words(text: str) -> int:
    return len(text.split())


def transcribe_audio(data: bytes, mime_type: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMGenerationError(
            "GEMINI_API_KEY não configurada. Adicione uma chave do Gemini no arquivo .env da raiz do projeto."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    prompt = (
        "Transcreva o áudio em português do Brasil, de forma literal. "
        "Mantenha hesitações, repetições e vícios de linguagem (como 'é', 'né', "
        "'tipo', 'então') exatamente como foram falados. Não corrija a gramática, "
        "não resuma e não acrescente nada que não tenha sido dito. "
        "Se não houver fala audível, devolva a transcrição vazia. "
        'Retorne somente JSON válido no formato {"transcript": "..."}.'
    )

    try:
        client = genai.Client(api_key=api_key)
        response = _generate_content(
            client,
            model,
            [types.Part.from_bytes(data=data, mime_type=mime_type), prompt],
            "Você é um sistema de transcrição de fala fiel ao que foi dito.",
            temperature=0.0,
        )
        transcript = json.loads(response.text or "{}").get("transcript")
    except Exception as error:
        logger.exception("Falha ao transcrever áudio com o Gemini usando o modelo %s", model)
        raise LLMGenerationError(_generation_error_message(error, "transcrever o áudio")) from error

    if not isinstance(transcript, str):
        raise LLMGenerationError("O Gemini retornou uma transcrição em formato inválido")
    transcript = transcript.strip()
    if not transcript:
        raise EmptyTranscriptError(
            "Não consegui identificar fala no áudio. Verifique o microfone e tente gravar de novo."
        )
    return transcript
