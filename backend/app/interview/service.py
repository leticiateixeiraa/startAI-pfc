"""
feat(interview-backend): lógica do entrevistador dinâmico (geração e
adaptação de perguntas com base nas respostas anteriores)

MOCK: enquanto o módulo `questions` (Leonardo) não fornece perguntas reais
geradas por LLM, este módulo usa um banco de perguntas fixo por categoria
(QUESTION_BANK) e uma lógica baseada em regras simples para decidir quando
"adaptar" a próxima pergunta em vez de seguir o roteiro padrão — cumprindo
o critério de aceitação combinado: "ao menos uma pergunta subsequente é
ajustada com base na resposta dada".

>>> PONTO DE INTEGRAÇÃO FUTURA <<<
Quando tivermos a API de LLM configurada, o ideal é substituir só a função
`_adapt_next_question` por uma chamada real ao modelo (passando a pergunta
atual + resposta + histórico da sessão como contexto/prompt) e o
QUESTION_BANK pelas perguntas reais vindas do módulo `questions`. As funções
públicas (`start_mock_session`, `register_answer_and_get_next`) não
precisam mudar de assinatura quando isso acontecer — só a implementação
interna.
"""
import uuid

from sqlalchemy.orm import Session

from app.interview.models import InterviewAnswer, InterviewQuestion, InterviewSession
from app.questions.llm_service import LLMGenerationError, generate_adapted_question

QUESTION_BANK: dict[str, list[str]] = {
    "entrevista_de_emprego": [
        "Fale um pouco sobre você e sua trajetória profissional.",
        "Descreva um desafio técnico ou profissional que você enfrentou recentemente e como resolveu.",
        "Como você lida com prazos apertados e prioridades conflitantes?",
        "Por que você quer trabalhar nesta vaga?",
    ],
    "apresentacao_academica": [
        "Apresente o tema do seu trabalho em poucas frases.",
        "Qual foi a principal motivação para escolher esse tema?",
        "Quais foram os principais resultados encontrados?",
        "Quais são as limitações do seu estudo e propostas para trabalhos futuros?",
    ],
}

DEFAULT_CATEGORY = "entrevista_de_emprego"

# Gatilhos simples de palavra-chave -> pergunta de aprofundamento.
# Simula o comportamento de um entrevistador atento sem precisar de LLM.
# Tupla: (palavras-chave, pergunta de acompanhamento)
FOLLOWUP_TRIGGERS: list[tuple[list[str], str]] = [
    (
        ["dificil", "difícil", "desafio", "problema", "erro"],
        "Você mencionou uma dificuldade — como exatamente você a superou, passo a passo?",
    ),
    (
        ["equipe", "time", "colegas"],
        "Como foi a dinâmica com o restante da equipe nessa situação?",
    ),
    (
        ["prazo", "deadline", "urgente"],
        "Como você organizou suas prioridades para conseguir cumprir esse prazo?",
    ),
]

MIN_WORDS_FOR_DETAILED_ANSWER = 8


def _valid_category(category: str) -> str:
    return category if category in QUESTION_BANK else DEFAULT_CATEGORY


def _question_at(category: str, index: int) -> str | None:
    bank = QUESTION_BANK[_valid_category(category)]
    return bank[index] if index < len(bank) else None


def _session_question_at(db: Session, session: InterviewSession, index: int) -> str | None:
    question = (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.session_id == session.id,
            InterviewQuestion.order_index == index,
        )
        .first()
    )
    return question.text if question else _question_at(session.category, index)


def start_mock_session(db: Session, user_id: uuid.UUID, category: str) -> InterviewSession:
    """Cria uma sessão mockada com a primeira pergunta da categoria escolhida.

    Substitui, por enquanto, o POST /interviews que será do módulo
    `questions` (ver docstring de app/interview/models.py).
    """
    category = _valid_category(category)
    session = InterviewSession(
        user_id=user_id,
        category=category,
        presentation_type=category,
        current_index=0,
        current_question_text=_question_at(category, 0),
        finished=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _adapt_next_question(category: str, previous_answer: str, next_index: int) -> tuple[str | None, bool]:
    """Decide a próxima pergunta. Retorna (texto_da_pergunta, foi_adaptada).

    Regra 1: se a resposta contiver alguma palavra-chave de aprofundamento,
             insere uma pergunta de acompanhamento (desvia do roteiro fixo).
    Regra 2: se a resposta for muito curta/rasa, pede pra elaborar melhor.
    Regra 3 (fallback): segue a próxima pergunta fixa do banco da categoria.
    """
    answer_lower = previous_answer.lower()

    for keywords, followup in FOLLOWUP_TRIGGERS:
        if any(keyword in answer_lower for keyword in keywords):
            return followup, True

    word_count = len(previous_answer.split())
    if word_count < MIN_WORDS_FOR_DETAILED_ANSWER:
        return (
            "Pode detalhar um pouco mais sua resposta anterior, com um exemplo concreto?",
            True,
        )

    return _question_at(category, next_index), False


def _generated_count(db: Session, session: InterviewSession) -> int:
    return db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session.id).count()


def total_questions(db: Session, session: InterviewSession) -> int:
    """Quantas perguntas a entrevista tem: as geradas pela IA ou as do banco fixo."""
    return _generated_count(db, session) or len(QUESTION_BANK[_valid_category(session.category)])


def register_answer_and_get_next(
    db: Session, session: InterviewSession, answer_text: str
) -> tuple[str | None, bool, bool]:
    """Persiste a resposta à pergunta pendente e decide a próxima pergunta.

    Retorna (proxima_pergunta_ou_None, foi_adaptada, sessao_finalizada).
    """
    current_question = session.current_question_text
    if current_question is None or session.finished:
        session.finished = True
        db.commit()
        return None, False, True

    db.add(
        InterviewAnswer(
            session_id=session.id,
            order_index=session.current_index,
            question_text=current_question,
            answer_text=answer_text,
        )
    )

    category = _valid_category(session.category)
    generated_count = _generated_count(db, session)
    max_questions = generated_count or len(QUESTION_BANK[category])
    next_index = session.current_index + 1

    if next_index >= max_questions:
        session.finished = True
        session.current_question_text = None
        db.commit()
        return None, False, True

    if generated_count:
        previous_answers = [
            (answer.question_text, answer.answer_text)
            for answer in db.query(InterviewAnswer)
            .filter(InterviewAnswer.session_id == session.id)
            .order_by(InterviewAnswer.order_index)
            .all()
        ]
        try:
            next_question = generate_adapted_question(
                current_question,
                answer_text,
                previous_answers,
                session.presentation_type,
                session.seniority,
            )
            adapted = True
        except LLMGenerationError:
            next_question, adapted = _adapt_next_question(
                category, answer_text, next_index
            )
            if not adapted:
                next_question = _session_question_at(db, session, next_index)
    else:
        next_question, adapted = _adapt_next_question(category, answer_text, next_index)
        if not adapted:
            next_question = _session_question_at(db, session, next_index)

    session.current_index = next_index

    session.current_question_text = next_question
    session.finished = False
    db.commit()

    return next_question, adapted, False
