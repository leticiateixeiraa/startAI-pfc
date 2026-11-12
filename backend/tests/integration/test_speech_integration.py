"""
Testes de integração da transcrição por voz (app/speech/router.py).
Responsável pelo módulo: Gabriel.

Endpoint: POST /interviews/{session_id}/transcribe (multipart).
Inclui o trio de segurança: sem token -> 401, sessão de outro usuário -> 403,
dono da sessão -> 200. O Gemini é simulado por ser serviço externo.
"""
import io
import uuid
import wave

from app.audit.models import AuditLog
from app.interview.models import InterviewAnswer
from tests.integration.apoio import (
    iniciar_entrevista_mock,
    responder,
    usuario_autenticado,
)


def _wav(segundos: float = 2.0, taxa: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(taxa)
        arquivo.writeframes(b"\x00\x00" * int(taxa * segundos))
    return buffer.getvalue()


def _enviar(api, headers, session_id, conteudo=None, tipo="audio/wav", **form):
    return api.post(
        f"/interviews/{session_id}/transcribe",
        files={"audio": ("resposta.wav", _wav() if conteudo is None else conteudo, tipo)},
        data=form,
        headers=headers,
    )


def test_transcribe_do_dono_deve_retornar_200_com_texto_duracao_e_palavras(api, db, gemini_falso):
    # Arrange
    usuario, headers = usuario_autenticado(api, "voz")
    sessao = iniciar_entrevista_mock(api, headers)
    gemini_falso.responder({"transcript": "Eu, tipo, trabalho com dados."})

    # Act
    resposta = _enviar(api, headers, sessao["session_id"])

    # Assert
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["transcript"] == "Eu, tipo, trabalho com dados."
    assert corpo["word_count"] == 5
    assert corpo["duration_seconds"] == 2.0  # lida do cabeçalho do WAV
    evento = db.query(AuditLog).filter(
        AuditLog.action == "interview.audio_transcribed",
        AuditLog.resource_id == sessao["session_id"],
    ).one()
    # A auditoria guarda só metadados, nunca o que a pessoa falou.
    assert "trabalho com dados" not in (evento.details or "")


def test_transcribe_sem_token_deve_retornar_401(api):
    resposta = api.post(
        f"/interviews/{uuid.uuid4()}/transcribe",
        files={"audio": ("a.wav", _wav(), "audio/wav")},
    )
    assert resposta.status_code == 401


def test_transcribe_de_sessao_de_outro_usuario_deve_retornar_403(api, gemini_falso):
    _, headers_dono = usuario_autenticado(api, "dono")
    _, headers_outro = usuario_autenticado(api, "intruso")
    sessao = iniciar_entrevista_mock(api, headers_dono)

    resposta = _enviar(api, headers_outro, sessao["session_id"])

    assert resposta.status_code == 403
    assert gemini_falso.prompts == []  # o áudio nem chegou ao Gemini


def test_transcribe_de_sessao_inexistente_deve_retornar_404(api):
    _, headers = usuario_autenticado(api, "sem_sessao")
    assert _enviar(api, headers, uuid.uuid4()).status_code == 404


def test_transcribe_com_formato_nao_suportado_deve_retornar_415(api, gemini_falso):
    _, headers = usuario_autenticado(api, "formato")
    sessao = iniciar_entrevista_mock(api, headers)

    resposta = _enviar(api, headers, sessao["session_id"], conteudo=b"abc", tipo="text/plain")

    assert resposta.status_code == 415
    assert gemini_falso.prompts == []


def test_transcribe_com_audio_vazio_deve_retornar_400(api):
    _, headers = usuario_autenticado(api, "vazio")
    sessao = iniciar_entrevista_mock(api, headers)
    assert _enviar(api, headers, sessao["session_id"], conteudo=b"").status_code == 400


def test_transcribe_com_audio_acima_do_limite_deve_retornar_413(api, gemini_falso):
    _, headers = usuario_autenticado(api, "grande")
    sessao = iniciar_entrevista_mock(api, headers)

    resposta = _enviar(api, headers, sessao["session_id"], conteudo=b"x" * (10 * 1024 * 1024 + 1))

    assert resposta.status_code == 413
    assert gemini_falso.prompts == []


def test_transcribe_com_audio_mais_longo_que_o_limite_deve_retornar_400(api, gemini_falso):
    _, headers = usuario_autenticado(api, "longo")
    sessao = iniciar_entrevista_mock(api, headers)

    # 301 s em 8 kHz mono = ~4,8 MB, abaixo do limite de bytes.
    resposta = _enviar(api, headers, sessao["session_id"], conteudo=_wav(301, taxa=8000))

    assert resposta.status_code == 400
    assert gemini_falso.prompts == []


def test_transcribe_sem_fala_deve_retornar_422(api, gemini_falso):
    _, headers = usuario_autenticado(api, "silencio")
    sessao = iniciar_entrevista_mock(api, headers)
    gemini_falso.responder({"transcript": ""})

    resposta = _enviar(api, headers, sessao["session_id"])

    assert resposta.status_code == 422


def test_transcribe_com_gemini_indisponivel_deve_retornar_502(api):
    # Sem a fixture gemini_falso, não há GEMINI_API_KEY: o serviço recusa.
    _, headers = usuario_autenticado(api, "sem_chave")
    sessao = iniciar_entrevista_mock(api, headers)
    assert _enviar(api, headers, sessao["session_id"]).status_code == 502


def test_answer_por_voz_deve_persistir_modo_e_duracao(api, db):
    _, headers = usuario_autenticado(api, "persiste")
    sessao = iniciar_entrevista_mock(api, headers)

    resposta = api.post(
        f"/interviews/{sessao['session_id']}/answer",
        json={
            "answer_text": "Eu organizei as tarefas por impacto e entreguei no prazo combinado.",
            "input_mode": "voice",
            "audio_duration_seconds": 12.5,
        },
        headers=headers,
    )

    assert resposta.status_code == 200, resposta.text
    db.expire_all()
    salva = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == uuid.UUID(sessao["session_id"])
    ).one()
    assert salva.input_mode == "voice"
    assert salva.audio_duration_seconds == 12.5


def test_answer_digitada_deve_continuar_funcionando_como_modo_text(api, db):
    _, headers = usuario_autenticado(api, "digitada")
    sessao = iniciar_entrevista_mock(api, headers)

    resposta = responder(api, headers, sessao["session_id"], "Resposta digitada com mais de oito palavras no total.")

    assert resposta.status_code == 200
    db.expire_all()
    salva = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == uuid.UUID(sessao["session_id"])
    ).one()
    assert salva.input_mode == "text"
    assert salva.audio_duration_seconds is None


def test_answer_com_modo_invalido_deve_retornar_422(api):
    _, headers = usuario_autenticado(api, "modo_ruim")
    sessao = iniciar_entrevista_mock(api, headers)
    resposta = api.post(
        f"/interviews/{sessao['session_id']}/answer",
        json={"answer_text": "x", "input_mode": "video"},
        headers=headers,
    )
    assert resposta.status_code == 422
