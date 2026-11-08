"""
Regras de negócio da recomendação de vagas (funcionalidade 7).

O perfil do aluno é montado com o que ele já fez no StartAI, e as vagas
reais vêm da API da Jooble (jooble.py).

RN01 - Só há recomendação para quem tem ao menos uma entrevista com cargo
       informado OU o questionário de primeiro acesso respondido.
       O cargo vem do cargo mais treinado nas entrevistas; sem entrevista,
       do primeiro cargo da área indicada pelo questionário.
RN02 - O nível recomendado é "compatível com o desempenho":
       média das notas da IA >= 7  -> o nível que o aluno treinou;
       entre 4 e 7                  -> o mesmo nível, com sugestão de treinar mais;
       abaixo de 4                  -> um nível abaixo (ex.: júnior -> estágio).
       Sem nota ainda, vale o nível treinado.
RN03 - A compatibilidade (0 a 100%) de cada vaga é calculada pelo backend:
       até 50 pontos pelo título (palavras do cargo presentes na vaga),
       até 25 pelo nível (o nível da vaga bate com o recomendado) e
       até 25 pelas habilidades do aluno citadas na vaga.
RN04 - As vagas ficam salvas por 24 horas. Dentro desse prazo, e para o
       mesmo cargo e nível, a lista salva é devolvida sem chamar a API.
RN05 - Se a API falhar, devolve a última lista salva com um aviso; sem lista
       salva, informa que o serviço está indisponível.
"""
import json
import re
import unicodedata
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.evaluation.models import InterviewEvaluation
from app.interview.models import InterviewAnswer, InterviewSession
from app.jobs import jooble
from app.jobs.models import JobRecommendation
from app.onboarding.models import CareerOnboarding
from app.onboarding.questionario import AREAS
from app.questions.llm_service import SENIORITY_LEVELS

NIVEIS = ["estagio", "junior", "pleno", "senior"]
NIVEL_PADRAO = "junior"
VALIDADE_CACHE = timedelta(hours=24)
MAX_VAGAS = 12
MAX_HABILIDADES = 8

# Palavras que indicam o nível no título da vaga (já sem acento).
PALAVRAS_NIVEL = {
    "estagio": r"\b(estagio|estagiario|estagiaria|intern|internship|trainee)\b",
    "junior": r"\b(junior|jr)\b",
    "pleno": r"\b(pleno|pl|mid|mid-level)\b",
    "senior": r"\b(senior|sr|especialista|lead|lider)\b",
}

# Habilidades técnicas procuradas nas entrevistas do aluno e nas vagas.
# Lista fechada de propósito: é fácil de explicar e de testar.
HABILIDADES = {
    "SQL": r"\bsql\b|postgres|mysql",
    "Python": r"\bpython\b",
    "Pandas": r"\bpandas\b",
    "Power BI": r"\bpower ?bi\b",
    "Excel": r"\bexcel\b",
    "Estatística": r"\bestatistica\b",
    "Machine Learning": r"machine learning|aprendizado de maquina",
    "Java": r"\bjava\b(?!script)",
    "JavaScript": r"\bjavascript\b|\bjs\b",
    "TypeScript": r"\btypescript\b",
    "React": r"\breact\b",
    "Node.js": r"\bnode(\.?js)?\b",
    "HTML e CSS": r"\bhtml\b|\bcss\b",
    "C#": r"c#|\.net\b|dotnet",
    "PHP": r"\bphp\b",
    "Kotlin": r"\bkotlin\b",
    "Swift": r"\bswift\b",
    "Flutter": r"\bflutter\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "AWS": r"\baws\b|amazon web services",
    "Azure": r"\bazure\b",
    "Linux": r"\blinux\b",
    "Git": r"\bgit\b|github|gitlab",
    "APIs REST": r"\bapi\b|\bapis\b|\brest\b",
    "Testes automatizados": r"\bselenium\b|\bcypress\b|\bpytest\b|testes automatizados",
    "Figma": r"\bfigma\b",
    "Scrum": r"\bscrum\b|\bagil\b|\bageis\b|kanban",
    "Redes": r"\bredes\b|\btcp\b",
}

PALAVRAS_IGNORADAS = {"de", "da", "do", "das", "dos", "e", "em", "para", "a", "o"}


class SemPerfil(Exception):
    """O aluno ainda não tem dados para montar o perfil (RN01)."""


def sem_acento(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto or "")
    return "".join(letra for letra in normalizado if not unicodedata.combining(letra)).lower()


def cargo_sem_nivel(cargo: str) -> str:
    """'Analista de Dados Júnior' -> 'Analista de Dados'. Tira também o "(a)"."""
    texto = re.sub(r"\(a\)", "", cargo or "")
    # Só as palavras de nível que as pessoas escrevem no cargo. "Especialista"
    # e "Líder" ficam: fazem parte do nome de muitos cargos.
    texto = re.sub(
        r"(?<!\w)(j[uú]nior|jr\.?|pleno|s[eê]nior|sr\.?|est[aá]gio|estagi[aá]ri[oa])(?!\w)",
        " ",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\s+", " ", texto).strip(" -–,")
    # "Estágio em Desenvolvimento Web" -> "Desenvolvimento Web"
    texto = re.sub(r"^(em|de|da|do|na|no)\s+", "", texto, flags=re.IGNORECASE)
    return texto or (cargo or "").strip()


def nivel_do_titulo(titulo: str) -> str | None:
    titulo = sem_acento(titulo)
    for nivel, padrao in PALAVRAS_NIVEL.items():
        if re.search(padrao, titulo):
            return nivel
    return None


def habilidades_no_texto(texto: str) -> Counter:
    texto = sem_acento(texto)
    return Counter(
        {nome: len(re.findall(padrao, texto)) for nome, padrao in HABILIDADES.items() if re.search(padrao, texto)}
    )


def nivel_recomendado(nivel_treinado: str, media: float | None) -> tuple[str, str]:
    """RN02. Devolve (nível, explicação para o aluno)."""
    rotulo = SENIORITY_LEVELS[nivel_treinado]["label"]
    if media is None:
        return nivel_treinado, f"Você treinou para o nível {rotulo}. Depois da primeira avaliação, o nível passa a considerar suas notas."
    nota = f"{media:.1f}".replace(".", ",")
    if media >= 7:
        return nivel_treinado, f"Sua nota média é {nota}: você está preparado(a) para vagas de nível {rotulo}."
    if media >= 4:
        return nivel_treinado, f"Sua nota média é {nota}. As vagas são de nível {rotulo}, mas vale treinar mais para chegar bem na entrevista."
    indice = max(0, NIVEIS.index(nivel_treinado) - 1)
    abaixo = NIVEIS[indice]
    if abaixo == nivel_treinado:
        return nivel_treinado, f"Sua nota média é {nota}. Continue treinando: vagas de {rotulo} são o melhor começo."
    return abaixo, (
        f"Sua nota média é {nota}. Por enquanto, recomendamos vagas de nível "
        f"{SENIORITY_LEVELS[abaixo]['label']}, um passo antes de {rotulo}."
    )


def montar_perfil(db: Session, user_id: uuid.UUID) -> dict:
    """RN01 e RN02. Pode levantar SemPerfil."""
    sessoes = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id, InterviewSession.job_title.isnot(None))
        .order_by(InterviewSession.created_at.desc())
        .all()
    )
    sessoes = [sessao for sessao in sessoes if (sessao.job_title or "").strip()]
    onboarding = (
        db.query(CareerOnboarding)
        .filter(CareerOnboarding.user_id == user_id, CareerOnboarding.skipped.is_(False))
        .first()
    )
    area = AREAS.get(onboarding.recommended_area) if onboarding and onboarding.recommended_area else None

    if sessoes:
        # Cargo mais treinado; no empate, o mais recente (a lista já vem do mais novo).
        contagem = Counter(sem_acento(cargo_sem_nivel(sessao.job_title)) for sessao in sessoes)
        mais_treinado = max(contagem, key=lambda chave: contagem[chave])
        sessoes_do_cargo = [s for s in sessoes if sem_acento(cargo_sem_nivel(s.job_title)) == mais_treinado]
        cargo = cargo_sem_nivel(sessoes_do_cargo[0].job_title)
        nivel_treinado = next((s.seniority for s in sessoes_do_cargo if s.seniority in NIVEIS), NIVEL_PADRAO)
        origem = "entrevistas"
    elif area:
        cargo = cargo_sem_nivel(area["roles"][0])
        nivel_treinado = NIVEL_PADRAO
        sessoes_do_cargo = []
        origem = "questionario"
    else:
        raise SemPerfil("Faça uma entrevista ou responda o questionário de área para receber vagas.")

    notas = [
        nota
        for (nota,) in db.query(InterviewEvaluation.overall_score)
        .filter(InterviewEvaluation.user_id == user_id)
        .all()
    ]
    media = round(sum(notas) / len(notas), 1) if notas else None
    nivel, explicacao = nivel_recomendado(nivel_treinado, media)

    # Habilidades: o que apareceu nas entrevistas (cargo + respostas) e o que
    # o questionário indicou para a área. O texto fica só aqui no backend.
    textos = [s.job_title for s in sessoes]
    if sessoes:
        respostas = (
            db.query(InterviewAnswer.answer_text)
            .filter(InterviewAnswer.session_id.in_([s.id for s in sessoes]))
            .all()
        )
        textos += [texto for (texto,) in respostas]
    if area:
        textos += area["skills"] + [area["name"]]
    habilidades = [nome for nome, _ in habilidades_no_texto(" ".join(textos)).most_common(MAX_HABILIDADES)]

    return {
        "job_title": cargo,
        "source": origem,
        "area": area["name"] if area else None,
        "practiced_seniority": nivel_treinado,
        "recommended_seniority": nivel,
        "recommended_seniority_label": SENIORITY_LEVELS[nivel]["label"],
        "level_reason": explicacao,
        "average_score": media,
        "interviews_count": len(sessoes_do_cargo),
        "skills": habilidades,
    }


def termo_de_busca(perfil: dict) -> str:
    # Estágio costuma ser anunciado com a palavra no título; nos outros níveis
    # a busca é pelo cargo e o nível entra na compatibilidade (RN03), senão a
    # API deixaria de fora as vagas que escrevem "Jr" em vez de "Júnior".
    if perfil["recommended_seniority"] == "estagio":
        return f"Estágio {perfil['job_title']}"
    return perfil["job_title"]


def calcular_compatibilidade(vaga: dict, perfil: dict) -> tuple[int, list[str]]:
    """RN03. Devolve (porcentagem, motivos em texto)."""
    motivos = []
    titulo = sem_acento(vaga["title"])

    palavras = [p for p in re.findall(r"[a-z0-9+#.]+", sem_acento(perfil["job_title"])) if p not in PALAVRAS_IGNORADAS]
    encontradas = [p for p in palavras if re.search(rf"\b{re.escape(p)}", titulo)]
    pontos_titulo = 50 * len(encontradas) / len(palavras) if palavras else 0
    if palavras and len(encontradas) == len(palavras):
        motivos.append(f"O título bate com o cargo que você treinou ({perfil['job_title']})")
    elif encontradas:
        motivos.append(f"O título é parecido com o cargo que você treinou ({perfil['job_title']})")

    desejado = perfil["recommended_seniority"]
    nivel_vaga = nivel_do_titulo(vaga["title"])
    if nivel_vaga == desejado:
        pontos_nivel = 25
        motivos.append(f"Vaga de nível {SENIORITY_LEVELS[desejado]['label']}, o recomendado para você")
    elif nivel_vaga is None:
        pontos_nivel = 15  # a vaga não diz o nível: nem soma tudo, nem penaliza
    elif abs(NIVEIS.index(nivel_vaga) - NIVEIS.index(desejado)) == 1:
        pontos_nivel = 8
    else:
        pontos_nivel = 0

    texto_vaga = f"{vaga['title']} {vaga.get('description') or ''}"
    citadas = [nome for nome in perfil["skills"] if nome in habilidades_no_texto(texto_vaga)]
    if perfil["skills"]:
        pontos_habilidades = 25 * min(1, len(citadas) / 3)
    else:
        pontos_habilidades = 10
    if citadas:
        lista = ", ".join(citadas[:3])
        motivos.append(f"Cita {lista}, que aparece no seu perfil" if len(citadas) == 1 else f"Cita {lista}, que aparecem no seu perfil")

    return round(pontos_titulo + pontos_nivel + pontos_habilidades), motivos


def _chave(perfil: dict) -> str:
    return f"{sem_acento(perfil['job_title'])}|{perfil['recommended_seniority']}"[:220]


def _como_utc(data: datetime) -> datetime:
    # O SQLite dos testes devolve datas sem fuso; o PostgreSQL devolve com.
    return data if data.tzinfo else data.replace(tzinfo=timezone.utc)


def _vagas_salvas(db: Session, user_id: uuid.UUID) -> list[JobRecommendation]:
    return (
        db.query(JobRecommendation)
        .filter(JobRecommendation.user_id == user_id)
        .order_by(JobRecommendation.position)
        .all()
    )


def _para_resposta(vaga: JobRecommendation) -> dict:
    return {
        "id": vaga.id,
        "title": vaga.title,
        "company": vaga.company,
        "location": vaga.location,
        "salary_min": vaga.salary_min,
        "salary_max": vaga.salary_max,
        "url": vaga.url,
        "description": vaga.description,
        "posted_at": vaga.posted_at,
        "compatibility": vaga.compatibility,
        "reasons": json.loads(vaga.reasons or "[]"),
    }


def recomendar(db: Session, user_id: uuid.UUID, atualizar: bool = False) -> dict:
    """Monta o perfil e devolve as vagas (salvas ou novas). Pode levantar
    SemPerfil ou jooble.VagasIndisponiveis. Não faz commit."""
    perfil = montar_perfil(db, user_id)
    chave = _chave(perfil)
    salvas = _vagas_salvas(db, user_id)
    agora = datetime.now(timezone.utc)

    validas = (
        salvas
        and salvas[0].search_key == chave
        and agora - _como_utc(salvas[0].fetched_at) < VALIDADE_CACHE
    )
    if validas and not atualizar:
        return _resultado(perfil, salvas, from_cache=True)

    try:
        encontradas = jooble.buscar_vagas(termo_de_busca(perfil))
    except jooble.VagasIndisponiveis as error:
        if salvas:  # RN05
            return _resultado(perfil, salvas, from_cache=True, aviso=f"{error} Mostrando as últimas vagas salvas.")
        raise

    pontuadas = []
    vistas = set()
    for vaga in encontradas:
        # A Jooble às vezes repete a mesma vaga vinda de sites diferentes.
        repetida = (sem_acento(vaga["title"]), sem_acento(vaga.get("company") or ""))
        if repetida in vistas:
            continue
        vistas.add(repetida)
        pontos, motivos = calcular_compatibilidade(vaga, perfil)
        pontuadas.append((pontos, vaga, motivos))
    pontuadas.sort(key=lambda item: item[0], reverse=True)

    db.query(JobRecommendation).filter(JobRecommendation.user_id == user_id).delete(synchronize_session=False)
    novas = []
    for posicao, (pontos, vaga, motivos) in enumerate(pontuadas[:MAX_VAGAS]):
        registro = JobRecommendation(
            user_id=user_id,
            search_key=chave,
            position=posicao,
            compatibility=pontos,
            reasons=json.dumps(motivos, ensure_ascii=False),
            fetched_at=agora,
            **vaga,
        )
        db.add(registro)
        novas.append(registro)
    db.flush()
    return _resultado(perfil, novas, from_cache=False)


def _resultado(perfil: dict, vagas: list[JobRecommendation], from_cache: bool, aviso: str | None = None) -> dict:
    return {
        "profile": perfil,
        "jobs": [_para_resposta(vaga) for vaga in vagas],
        "fetched_at": _como_utc(vagas[0].fetched_at) if vagas else None,
        "from_cache": from_cache,
        "warning": aviso,
    }
