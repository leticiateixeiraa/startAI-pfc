import json
import logging
import os
import time

from google import genai
from google.genai import types


logger = logging.getLogger(__name__)


class LLMGenerationError(RuntimeError):
    pass


TEMPORARY_GEMINI_ERRORS = {429, 500, 502, 503, 504}


def _generate_content(
    client,
    model: str,
    prompt: str,
    system_instruction: str,
    temperature: float = 0.7,
):
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        response_mime_type="application/json",
    )
    for attempt in range(3):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
        except Exception as error:
            status_code = getattr(error, "status_code", None)
            if status_code not in TEMPORARY_GEMINI_ERRORS or attempt == 2:
                raise
            wait_seconds = 2 ** attempt
            logger.warning(
                "Gemini indisponível (HTTP %s); nova tentativa em %ss (%s/3)",
                status_code,
                wait_seconds,
                attempt + 1,
            )
            time.sleep(wait_seconds)


def _generation_error_message(error: Exception, action: str) -> str:
    status_code = getattr(error, "status_code", None)
    if status_code in TEMPORARY_GEMINI_ERRORS:
        return (
            f"O Gemini está temporariamente indisponível para {action}. "
            "Aguarde alguns segundos e tente novamente."
        )
    if status_code == 404:
        return f"O modelo Gemini configurado não está disponível para esta chave ao {action}."
    if status_code in {401, 403}:
        return f"A chave do Gemini não tem permissão para {action}. Verifique a API key e o acesso ao modelo."
    return f"Não foi possível {action} com o Gemini."


INTERVIEW_RULES = {
    "comportamental": (
        "Priorize situações reais, comportamento, tomada de decisão e use a estrutura "
        "situação, ação e resultado (STAR)."
    ),
    "tecnica": (
        "Priorize fundamentos técnicos, raciocínio, trade-offs, depuração e exemplos "
        "práticos relacionados às responsabilidades da vaga."
    ),
    "mista": (
        "Equilibre perguntas comportamentais e técnicas, alternando competências humanas "
        "com a aplicação prática dos conhecimentos exigidos."
    ),
    "apresentacao_pessoal": (
        "Priorize clareza da narrativa pessoal, trajetória, motivação, comunicação e "
        "adequação ao objetivo informado, sem transformar a sessão em uma prova técnica."
    ),
}


# Nível da vaga: muda a dificuldade das perguntas e o quanto a avaliação exige.
SENIORITY_LEVELS = {
    "estagio": {
        "label": "Estágio",
        "rule": (
            "Candidato ainda estudando, com pouca ou nenhuma experiência profissional. "
            "Pergunte sobre fundamentos, projetos acadêmicos ou pessoais, vontade de aprender "
            "e situações da faculdade. Não exija experiência de mercado."
        ),
    },
    "junior": {
        "label": "Júnior",
        "rule": (
            "Até cerca de 2 anos de experiência. Cobre fundamentos sólidos aplicados a tarefas "
            "bem definidas, as primeiras experiências profissionais e como a pessoa aprende e "
            "pede ajuda."
        ),
    },
    "pleno": {
        "label": "Pleno",
        "rule": (
            "Profissional que trabalha com autonomia. Aprofunde em decisões técnicas, "
            "trade-offs, resolução de problemas sem supervisão, qualidade e colaboração com o time."
        ),
    },
    "senior": {
        "label": "Sênior",
        "rule": (
            "Referência técnica do time. Aprofunde em arquitetura, escalabilidade, decisões de "
            "alto impacto, liderança técnica, mentoria e influência em outras áreas."
        ),
    },
}


def seniority_rule(seniority: str | None) -> str:
    """Trecho do prompt com o nível da vaga; vazio quando não informado."""
    level = SENIORITY_LEVELS.get(seniority or "")
    if not level:
        return ""
    return f"Nível da vaga: {level['label']}. {level['rule']}"


def generate_questions(
    job_title: str,
    presentation_type: str,
    job_description: str | None,
    seniority: str | None = None,
) -> list[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMGenerationError(
            "GEMINI_API_KEY não configurada. Adicione uma chave do Gemini no arquivo .env da raiz do projeto."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    rule = INTERVIEW_RULES.get(presentation_type, INTERVIEW_RULES["mista"])
    level_rule = seniority_rule(seniority)
    prompt = (
        "Analise a vaga abaixo e crie de 4 a 6 perguntas de entrevista em "
        "portugues do Brasil.\n\n"
        f"Cargo: {job_title}\n"
        f"Tipo de entrevista: {presentation_type}\n"
        f"Descricao da vaga:\n{job_description or 'Nao informada'}\n\n"
        f"Regra desta modalidade: {rule}\n"
        + (f"{level_rule} A dificuldade das perguntas deve combinar com esse nível.\n" if level_rule else "")
        + "\nAs perguntas devem avaliar competencias, responsabilidades e contexto "
        "especificos da vaga. Evite perguntas genericas quando a descricao trouxer "
        "detalhes. Gere exatamente 5 perguntas. Retorne somente JSON valido no formato: "
        '{"questions": ["pergunta 1", "pergunta 2"]}'
    )

    try:
        client = genai.Client(api_key=api_key)
        response = _generate_content(
            client,
            model,
            prompt,
            "Voce e um entrevistador tecnico experiente e objetivo.",
        )
        content = response.text or "{}"
        questions = json.loads(content).get("questions")
    except Exception as error:
        logger.exception("Falha ao gerar perguntas com o Gemini usando o modelo %s", model)
        raise LLMGenerationError(
            _generation_error_message(error, "gerar perguntas")
        ) from error

    if not isinstance(questions, list):
        raise LLMGenerationError("O LLM retornou um formato de perguntas invalido")

    cleaned = [
        question.strip()
        for question in questions
        if isinstance(question, str) and question.strip()
    ]
    if len(cleaned) < 5:
        raise LLMGenerationError("O LLM retornou menos de 5 perguntas")
    return cleaned[:5]


def generate_adapted_question(
    current_question: str,
    answer_text: str,
    previous_answers: list[tuple[str, str]],
    presentation_type: str | None = None,
    seniority: str | None = None,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMGenerationError(
            "GEMINI_API_KEY não configurada. Adicione uma chave do Gemini no arquivo .env da raiz do projeto."
        )

    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    history = "\n".join(
        f"Pergunta: {question}\nResposta: {answer}"
        for question, answer in previous_answers
    )
    prompt = (
        "Crie a próxima pergunta de uma entrevista em português do Brasil. "
        "Adapte-a ao conteúdo da resposta atual e ao histórico, aprofundando "
        "um ponto relevante sem repetir perguntas. Retorne somente JSON válido "
        'no formato {"question": "..."}.\n\n'
        f"Histórico:\n{history or 'Nenhum'}\n\n"
        f"Pergunta atual: {current_question}\n"
        f"Resposta atual: {answer_text}\n"
        f"Regra da modalidade: {INTERVIEW_RULES.get(presentation_type or 'mista', INTERVIEW_RULES['mista'])}\n"
        f"{seniority_rule(seniority)}"
    )

    try:
        client = genai.Client(api_key=api_key)
        response = _generate_content(
            client,
            model,
            prompt,
            (
                "Você é um entrevistador atento. Faça uma pergunta por vez, "
                "clara, específica e diretamente relacionada à resposta."
            ),
        )
        question = json.loads(response.text or "{}").get("question")
    except Exception as error:
        logger.exception("Falha ao gerar pergunta adaptada com o Gemini usando o modelo %s", model)
        raise LLMGenerationError(
            _generation_error_message(error, "adaptar a próxima pergunta")
        ) from error

    if not isinstance(question, str) or not question.strip():
        raise LLMGenerationError("O LLM retornou uma pergunta adaptada inválida")
    return question.strip()
