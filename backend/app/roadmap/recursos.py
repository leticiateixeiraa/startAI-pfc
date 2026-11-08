"""
Catálogo de sites e plataformas recomendados nas trilhas de estudo.

A IA NÃO escreve links: ela escolhe recursos deste catálogo pelo id, e o
backend monta o link. Links inventados por modelos de linguagem costumam
apontar para páginas que não existem; com o catálogo, todo link mostrado ao
aluno foi conferido por alguém do time.

Vídeos são a exceção: a IA sugere um termo de busca e o link vai para a
busca do YouTube (ver `link_de_video`), em vez de um vídeo específico que
poderia não existir.

Para incluir um recurso, basta adicionar uma entrada aqui.
"""
from urllib.parse import quote_plus

TIPOS = {
    "pratica": "Prática",
    "curso": "Curso",
    "documentacao": "Documentação",
    "site": "Site",
    "video": "Vídeo",
}

RECURSOS = {
    # --- Base de programação e estudo geral ---
    "roadmap_sh": {"name": "roadmap.sh", "url": "https://roadmap.sh", "type": "site", "description": "Mapas de estudo por carreira (front-end, back-end, DevOps, dados...)"},
    "freecodecamp": {"name": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn", "type": "curso", "description": "Cursos gratuitos e interativos com certificados"},
    "cursoemvideo": {"name": "Curso em Vídeo", "url": "https://www.cursoemvideo.com", "type": "curso", "description": "Cursos gratuitos em português de lógica, Python, HTML/CSS e mais"},
    "cs50": {"name": "CS50 (Harvard)", "url": "https://cs50.harvard.edu/x/", "type": "curso", "description": "Introdução à ciência da computação, gratuita"},
    "the_odin_project": {"name": "The Odin Project", "url": "https://www.theodinproject.com", "type": "curso", "description": "Trilha gratuita e prática de desenvolvimento web"},
    "khan_academy": {"name": "Khan Academy", "url": "https://pt.khanacademy.org", "type": "curso", "description": "Matemática, estatística e computação em português"},
    "coursera": {"name": "Coursera", "url": "https://www.coursera.org", "type": "curso", "description": "Cursos de universidades e empresas (muitos com opção gratuita)"},
    "microsoft_learn": {"name": "Microsoft Learn", "url": "https://learn.microsoft.com/pt-br/training/", "type": "curso", "description": "Trilhas gratuitas de programação, nuvem e dados"},
    "learn_git_branching": {"name": "Learn Git Branching", "url": "https://learngitbranching.js.org/?locale=pt_BR", "type": "pratica", "description": "Aprenda Git de forma visual e interativa"},
    "github_skills": {"name": "GitHub Skills", "url": "https://skills.github.com", "type": "pratica", "description": "Exercícios práticos de Git, GitHub e GitHub Actions"},
    # --- Lógica, algoritmos e entrevistas técnicas ---
    "beecrowd": {"name": "beecrowd", "url": "https://judge.beecrowd.com", "type": "pratica", "description": "Exercícios de lógica e algoritmos, com enunciados em português"},
    "leetcode": {"name": "LeetCode", "url": "https://leetcode.com", "type": "pratica", "description": "Problemas de algoritmos usados em entrevistas técnicas"},
    "neetcode": {"name": "NeetCode", "url": "https://neetcode.io", "type": "pratica", "description": "Lista organizada de problemas de entrevista, com explicações"},
    "hackerrank": {"name": "HackerRank", "url": "https://www.hackerrank.com", "type": "pratica", "description": "Desafios de programação, SQL e preparação para entrevistas"},
    "codewars": {"name": "Codewars", "url": "https://www.codewars.com", "type": "pratica", "description": "Desafios curtos de programação por nível"},
    "exercism": {"name": "Exercism", "url": "https://exercism.org", "type": "pratica", "description": "Exercícios em dezenas de linguagens, com mentoria gratuita"},
    "system_design_primer": {"name": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "documentacao", "description": "Guia de design de sistemas para entrevistas de nível pleno e sênior"},
    "refactoring_guru": {"name": "Refactoring Guru", "url": "https://refactoring.guru/pt-br", "type": "site", "description": "Padrões de projeto e refatoração explicados em português"},
    # --- Front-end ---
    "mdn": {"name": "MDN Web Docs", "url": "https://developer.mozilla.org/pt-BR/", "type": "documentacao", "description": "Referência de HTML, CSS e JavaScript"},
    "react_docs": {"name": "Documentação do React", "url": "https://react.dev/learn", "type": "documentacao", "description": "Guia oficial e interativo do React"},
    "web_dev": {"name": "web.dev", "url": "https://web.dev/learn", "type": "curso", "description": "Cursos do Google sobre CSS, acessibilidade e performance"},
    "frontend_mentor": {"name": "Frontend Mentor", "url": "https://www.frontendmentor.io", "type": "pratica", "description": "Desafios reais de interface para montar portfólio"},
    # --- Back-end e banco de dados ---
    "python_docs": {"name": "Tutorial oficial do Python", "url": "https://docs.python.org/pt-br/3/tutorial/", "type": "documentacao", "description": "Tutorial oficial do Python em português"},
    "fastapi_docs": {"name": "Documentação do FastAPI", "url": "https://fastapi.tiangolo.com/pt/", "type": "documentacao", "description": "Tutorial de APIs REST com Python, em português"},
    "sqlbolt": {"name": "SQLBolt", "url": "https://sqlbolt.com", "type": "pratica", "description": "Lições interativas de SQL"},
    "postgres_tutorial": {"name": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com", "type": "documentacao", "description": "Tutorial completo de PostgreSQL"},
    # --- Mobile ---
    "android_developers": {"name": "Android Developers", "url": "https://developer.android.com/courses", "type": "curso", "description": "Cursos oficiais e gratuitos de Android com Kotlin"},
    "flutter_docs": {"name": "Documentação do Flutter", "url": "https://docs.flutter.dev", "type": "documentacao", "description": "Guia oficial do Flutter"},
    # --- Dados e IA ---
    "kaggle_learn": {"name": "Kaggle Learn", "url": "https://www.kaggle.com/learn", "type": "curso", "description": "Microcursos práticos de Python, pandas, SQL e machine learning"},
    "pandas_docs": {"name": "Documentação do pandas", "url": "https://pandas.pydata.org/docs/getting_started/index.html", "type": "documentacao", "description": "Primeiros passos com análise de dados no pandas"},
    # --- DevOps e cloud ---
    "docker_docs": {"name": "Docker — Get started", "url": "https://docs.docker.com/get-started/", "type": "documentacao", "description": "Guia oficial para começar com containers"},
    "linux_journey": {"name": "Linux Journey", "url": "https://linuxjourney.com", "type": "curso", "description": "Aprenda Linux do básico à linha de comando"},
    "aws_skill_builder": {"name": "AWS Skill Builder", "url": "https://skillbuilder.aws", "type": "curso", "description": "Cursos gratuitos de computação em nuvem da AWS"},
    # --- Segurança ---
    "tryhackme": {"name": "TryHackMe", "url": "https://tryhackme.com", "type": "pratica", "description": "Laboratórios guiados de segurança para iniciantes"},
    "overthewire": {"name": "OverTheWire", "url": "https://overthewire.org/wargames/", "type": "pratica", "description": "Desafios (wargames) de Linux e segurança"},
    "portswigger_academy": {"name": "PortSwigger Web Security Academy", "url": "https://portswigger.net/web-security", "type": "curso", "description": "Laboratórios gratuitos de segurança de aplicações web"},
    "owasp_top10": {"name": "OWASP Top 10", "url": "https://owasp.org/www-project-top-ten/", "type": "documentacao", "description": "Os riscos de segurança web mais comuns"},
    # --- UX/UI ---
    "laws_of_ux": {"name": "Laws of UX", "url": "https://lawsofux.com", "type": "site", "description": "Princípios de psicologia aplicados ao design de interfaces"},
    "nngroup": {"name": "Nielsen Norman Group", "url": "https://www.nngroup.com/articles/", "type": "site", "description": "Artigos de referência sobre usabilidade e pesquisa com usuários"},
    "figma_help": {"name": "Central de ajuda do Figma", "url": "https://help.figma.com", "type": "documentacao", "description": "Tutoriais oficiais do Figma"},
    # --- Qualidade de software ---
    "cypress_docs": {"name": "Documentação do Cypress", "url": "https://docs.cypress.io", "type": "documentacao", "description": "Testes end-to-end para aplicações web"},
    "pytest_docs": {"name": "Documentação do pytest", "url": "https://docs.pytest.org", "type": "documentacao", "description": "Testes automatizados em Python"},
    "ministry_of_testing": {"name": "Ministry of Testing", "url": "https://www.ministryoftesting.com", "type": "site", "description": "Comunidade e conteúdo sobre testes de software"},
    # --- Comunicação e entrevistas ---
    "ted_talks": {"name": "TED Talks", "url": "https://www.ted.com/talks", "type": "site", "description": "Palestras para observar técnicas de oratória e narrativa"},
    "toastmasters": {"name": "Toastmasters", "url": "https://www.toastmasters.org", "type": "site", "description": "Clubes para praticar falar em público"},
    "interviewing_io": {"name": "interviewing.io", "url": "https://interviewing.io", "type": "pratica", "description": "Entrevistas técnicas simuladas e gravações de entrevistas reais"},
    "linkedin_learning": {"name": "LinkedIn Learning", "url": "https://www.linkedin.com/learning/", "type": "curso", "description": "Cursos de carreira, comunicação e tecnologia"},
}


def link_de_video(busca: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(busca)}"


def catalogo_para_o_prompt() -> str:
    return "\n".join(
        f"- {chave}: {dados['name']} ({TIPOS[dados['type']]}) — {dados['description']}"
        for chave, dados in RECURSOS.items()
    )
