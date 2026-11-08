"""
Testes unitários da transcrição por voz (app/speech/service.py).
Responsável pelo módulo: Gabriel.
"""
import io
import wave
from types import SimpleNamespace

import pytest

from app.questions.llm_service import LLMGenerationError
from app.speech import service


def _wav(segundos: float, taxa: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(taxa)
        arquivo.writeframes(b"\x00\x00" * int(taxa * segundos))
    return buffer.getvalue()


class _ClienteFalso:
    def __init__(self, texto):
        self.texto = texto
        self.models = self
        self.chamadas = []

    def __call__(self, api_key):
        return self

    def generate_content(self, model, contents, config):
        self.chamadas.append(contents)
        return SimpleNamespace(text=self.texto)


def test_normalize_mime_type_deve_aceitar_wav_com_parametros_e_variacoes():
    assert service.normalize_mime_type("audio/wav") == "audio/wav"
    assert service.normalize_mime_type("audio/x-wav") == "audio/wav"
    assert service.normalize_mime_type("Audio/WAV; codecs=1") == "audio/wav"


@pytest.mark.parametrize("tipo", [None, "", "text/plain", "audio/webm", "video/mp4"])
def test_normalize_mime_type_com_formato_nao_suportado_deve_falhar(tipo):
    with pytest.raises(service.AudioValidationError):
        service.normalize_mime_type(tipo)


def test_validate_audio_deve_rejeitar_vazio_e_arquivo_grande_demais():
    with pytest.raises(service.AudioValidationError, match="vazio"):
        service.validate_audio(b"", "audio/wav")
    with pytest.raises(service.AudioValidationError, match="grande"):
        service.validate_audio(b"x" * (service.MAX_AUDIO_BYTES + 1), "audio/wav")


def test_wav_duration_seconds_deve_ler_duracao_do_cabecalho():
    assert service.wav_duration_seconds(_wav(2.5)) == pytest.approx(2.5)


def test_wav_duration_seconds_com_arquivo_que_nao_e_wav_deve_retornar_none():
    assert service.wav_duration_seconds(b"nao sou um wav") is None


def test_count_words_deve_contar_palavras_separadas_por_espaco():
    assert service.count_words("  eu, tipo, trabalho   com dados ") == 5
    assert service.count_words("") == 0


def test_transcribe_audio_sem_chave_deve_falhar_com_mensagem_clara():
    with pytest.raises(LLMGenerationError, match="GEMINI_API_KEY"):
        service.transcribe_audio(_wav(1), "audio/wav")


def test_transcribe_audio_deve_enviar_o_audio_ao_gemini_e_devolver_o_texto(monkeypatch):
    cliente = _ClienteFalso('{"transcript": "  Eu, tipo, sou desenvolvedor.  "}')
    monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa")
    monkeypatch.setattr("app.questions.llm_service.genai.Client", cliente)
    audio = _wav(1)

    texto = service.transcribe_audio(audio, "audio/wav")

    assert texto == "Eu, tipo, sou desenvolvedor."
    parte_audio, prompt = cliente.chamadas[0]
    assert parte_audio.inline_data.data == audio
    assert parte_audio.inline_data.mime_type == "audio/wav"
    assert "literal" in prompt  # vícios de linguagem precisam ser preservados


def test_transcribe_audio_sem_fala_deve_levantar_erro_de_transcricao_vazia(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa")
    monkeypatch.setattr("app.questions.llm_service.genai.Client", _ClienteFalso('{"transcript": "  "}'))
    with pytest.raises(service.EmptyTranscriptError):
        service.transcribe_audio(_wav(1), "audio/wav")


def test_transcribe_audio_com_resposta_fora_do_formato_deve_levantar_erro_do_llm(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa")
    monkeypatch.setattr("app.questions.llm_service.genai.Client", _ClienteFalso('{"outra_coisa": 1}'))
    with pytest.raises(LLMGenerationError):
        service.transcribe_audio(_wav(1), "audio/wav")
