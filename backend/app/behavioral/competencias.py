"""
Competências e tipos de perfil usados no perfil comportamental.

A IA dá a nota de cada competência (0 a 10), mas quem decide o TIPO de
perfil é o backend: é a competência com a maior nota. Assim a regra é
sempre a mesma e fácil de explicar, igual às notas da avaliação (RN03 de
app/evaluation/service.py).
"""

TIPO_COMPORTAMENTAL = "comportamental"

# A ordem do dicionário também desempata: em notas iguais vale a que vem antes.
COMPETENCIAS = {
    "comunicacao": {
        "label": "Comunicação",
        "description": "clareza, objetividade e organização ao contar uma situação",
    },
    "trabalho_em_equipe": {
        "label": "Trabalho em equipe",
        "description": "colaboração, escuta e divisão de responsabilidades com outras pessoas",
    },
    "lideranca": {
        "label": "Liderança",
        "description": "iniciativa, tomada de decisão e capacidade de orientar ou influenciar outras pessoas",
    },
    "resolucao_de_problemas": {
        "label": "Resolução de problemas",
        "description": "análise da causa, alternativas consideradas e solução aplicada",
    },
    "adaptabilidade": {
        "label": "Adaptabilidade",
        "description": "como lida com mudanças, imprevistos, pressão e aprendizado rápido",
    },
    "inteligencia_emocional": {
        "label": "Inteligência emocional",
        "description": "autoconhecimento, empatia e controle emocional em conflitos ou erros",
    },
}

STAR = {
    "situation": "Situação",
    "task": "Tarefa",
    "action": "Ação",
    "result": "Resultado",
}

ARQUETIPOS = {
    "comunicacao": {
        "name": "Perfil Comunicativo",
        "description": "Você se expressa com clareza e sabe adaptar a mensagem para quem está ouvindo.",
    },
    "trabalho_em_equipe": {
        "name": "Perfil Colaborativo",
        "description": "Você valoriza o time, divide responsabilidades e constrói soluções em conjunto.",
    },
    "lideranca": {
        "name": "Perfil de Liderança",
        "description": "Você toma a iniciativa, assume decisões e mobiliza as pessoas em direção a um objetivo.",
    },
    "resolucao_de_problemas": {
        "name": "Perfil Analítico",
        "description": "Você investiga a causa dos problemas e chega a soluções de forma estruturada.",
    },
    "adaptabilidade": {
        "name": "Perfil Adaptável",
        "description": "Você lida bem com mudanças e imprevistos e aprende rápido em situações novas.",
    },
    "inteligencia_emocional": {
        "name": "Perfil Empático",
        "description": "Você mantém o equilíbrio sob pressão e entende o lado das outras pessoas.",
    },
}


def competencia_mais_forte(notas: dict) -> str:
    return max(COMPETENCIAS, key=lambda chave: (notas[chave], -list(COMPETENCIAS).index(chave)))


def competencia_mais_fraca(notas: dict) -> str:
    return min(COMPETENCIAS, key=lambda chave: (notas[chave], list(COMPETENCIAS).index(chave)))


def definir_arquetipo(notas: dict) -> dict:
    chave = competencia_mais_forte(notas)
    return {"key": chave, **ARQUETIPOS[chave]}
