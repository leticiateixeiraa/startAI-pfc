"""
Perguntas prontas do questionário de primeiro acesso e áreas da tecnologia.

Cada alternativa soma pontos para uma ou mais áreas (2 = combina muito,
1 = combina um pouco). Os pesos ficam só aqui no backend: o front-end recebe
as perguntas sem os pesos, para a resposta não ser "guiada" pelo resultado.

Para mudar o questionário basta editar estas listas; a regra de cálculo
(service.py) não muda.
"""

AREAS = {
    "frontend": {
        "name": "Desenvolvimento Front-end",
        "description": "Cria as telas e a interação de sites e sistemas web, unindo programação e cuidado com a experiência de quem usa.",
        "roles": ["Desenvolvedor(a) Front-end", "Desenvolvedor(a) Web", "Engenheiro(a) de Interfaces"],
        "skills": ["HTML, CSS e JavaScript", "React ou outro framework", "Acessibilidade e responsividade"],
        "suggested_job_title": "Desenvolvedor Front-end Júnior",
    },
    "backend": {
        "name": "Desenvolvimento Back-end",
        "description": "Constrói a lógica, as APIs e os bancos de dados que fazem os sistemas funcionarem por trás das telas.",
        "roles": ["Desenvolvedor(a) Back-end", "Engenheiro(a) de Software", "Desenvolvedor(a) de APIs"],
        "skills": ["Uma linguagem como Python, Java ou C#", "Bancos de dados SQL", "APIs REST e testes automatizados"],
        "suggested_job_title": "Desenvolvedor Back-end Júnior",
    },
    "mobile": {
        "name": "Desenvolvimento Mobile",
        "description": "Desenvolve aplicativos para celular, aproveitando recursos como câmera, GPS e notificações.",
        "roles": ["Desenvolvedor(a) Android", "Desenvolvedor(a) iOS", "Desenvolvedor(a) Flutter / React Native"],
        "skills": ["Kotlin, Swift ou Flutter", "Design de interfaces para telas pequenas", "Publicação nas lojas de apps"],
        "suggested_job_title": "Desenvolvedor Mobile Júnior",
    },
    "dados_ia": {
        "name": "Dados e Inteligência Artificial",
        "description": "Transforma dados em informação: análises, painéis, previsões e modelos de inteligência artificial.",
        "roles": ["Analista de Dados", "Cientista de Dados", "Engenheiro(a) de Machine Learning"],
        "skills": ["SQL e Python (pandas)", "Estatística", "Visualização de dados e machine learning"],
        "suggested_job_title": "Analista de Dados Júnior",
    },
    "devops_cloud": {
        "name": "DevOps e Cloud",
        "description": "Automatiza a entrega de software e mantém sistemas estáveis, rápidos e escaláveis na nuvem.",
        "roles": ["Engenheiro(a) DevOps", "Analista de Infraestrutura Cloud", "SRE (Confiabilidade)"],
        "skills": ["Linux e redes", "Docker e CI/CD", "AWS, Azure ou Google Cloud"],
        "suggested_job_title": "Analista DevOps Júnior",
    },
    "seguranca": {
        "name": "Segurança da Informação",
        "description": "Protege sistemas e dados, encontra vulnerabilidades antes dos atacantes e responde a incidentes.",
        "roles": ["Analista de Segurança", "Pentester", "Analista de SOC"],
        "skills": ["Redes e sistemas operacionais", "OWASP Top 10", "Ferramentas de pentest e CTFs"],
        "suggested_job_title": "Analista de Segurança da Informação Júnior",
    },
    "ux_ui": {
        "name": "UX/UI Design",
        "description": "Pesquisa as necessidades das pessoas e desenha produtos digitais fáceis e agradáveis de usar.",
        "roles": ["UX Designer", "UI Designer", "Product Designer"],
        "skills": ["Figma", "Pesquisa com usuários", "Prototipação e testes de usabilidade"],
        "suggested_job_title": "UX/UI Designer Júnior",
    },
    "qa": {
        "name": "Qualidade de Software (QA)",
        "description": "Garante que o software funcione como deveria, planejando e automatizando testes.",
        "roles": ["Analista de Testes", "QA Engineer", "Engenheiro(a) de Automação de Testes"],
        "skills": ["Técnicas de teste", "Automação com Cypress, Selenium ou Pytest", "Escrita de casos de teste"],
        "suggested_job_title": "Analista de QA Júnior",
    },
}

PERGUNTAS = [
    {
        "id": "atividade_favorita",
        "text": "Qual dessas atividades você faria por horas sem ver o tempo passar?",
        "options": [
            {"id": "a", "text": "Montar o visual de uma página e deixar tudo bonito e responsivo", "weights": {"frontend": 2, "ux_ui": 1}},
            {"id": "b", "text": "Pensar em como os dados são guardados e como o sistema responde por trás", "weights": {"backend": 2, "dados_ia": 1}},
            {"id": "c", "text": "Analisar números e descobrir padrões em uma planilha", "weights": {"dados_ia": 2}},
            {"id": "d", "text": "Configurar servidores e automatizar tarefas repetitivas", "weights": {"devops_cloud": 2, "seguranca": 1}},
            {"id": "e", "text": "Testar um sistema procurando falhas e situações inesperadas", "weights": {"qa": 2, "seguranca": 1}},
        ],
    },
    {
        "id": "app_novo",
        "text": "Quando você usa um aplicativo novo, o que mais chama sua atenção?",
        "options": [
            {"id": "a", "text": "Se ele é fácil de usar e agradável de olhar", "weights": {"ux_ui": 2, "frontend": 1}},
            {"id": "b", "text": "Os recursos do celular que ele usa, como câmera, GPS e notificações", "weights": {"mobile": 2}},
            {"id": "c", "text": "Se ele é rápido e nunca sai do ar", "weights": {"devops_cloud": 2, "backend": 1}},
            {"id": "d", "text": "Se os meus dados estão protegidos", "weights": {"seguranca": 2}},
            {"id": "e", "text": "As recomendações personalizadas que ele faz", "weights": {"dados_ia": 2}},
        ],
    },
    {
        "id": "tipo_de_problema",
        "text": "Que tipo de problema você prefere resolver?",
        "options": [
            {"id": "a", "text": "Lógica e regras de negócio complexas", "weights": {"backend": 2, "qa": 1}},
            {"id": "b", "text": "Entender o que as pessoas precisam e desenhar uma solução para elas", "weights": {"ux_ui": 2}},
            {"id": "c", "text": "Fazer previsões e tomar decisões a partir de dados", "weights": {"dados_ia": 2}},
            {"id": "d", "text": "Encontrar brechas pensando como um invasor", "weights": {"seguranca": 2}},
            {"id": "e", "text": "Fazer algo funcionar bem em telas e dispositivos diferentes", "weights": {"frontend": 2, "mobile": 1}},
        ],
    },
    {
        "id": "papel_no_grupo",
        "text": "Em um trabalho em grupo, qual papel você costuma assumir?",
        "options": [
            {"id": "a", "text": "Quem cuida da apresentação visual", "weights": {"ux_ui": 2, "frontend": 1}},
            {"id": "b", "text": "Quem organiza a estrutura e garante que as partes se conectam", "weights": {"backend": 2, "devops_cloud": 1}},
            {"id": "c", "text": "Quem revisa tudo e encontra os erros antes da entrega", "weights": {"qa": 2}},
            {"id": "d", "text": "Quem pesquisa e traz dados para embasar as decisões", "weights": {"dados_ia": 2}},
            {"id": "e", "text": "Quem pensa nos riscos e no que pode dar errado", "weights": {"seguranca": 2, "qa": 1}},
        ],
    },
    {
        "id": "assunto_favorito",
        "text": "Qual desses assuntos você mais curte estudar?",
        "options": [
            {"id": "a", "text": "Design, artes e comunicação visual", "weights": {"ux_ui": 2, "frontend": 1}},
            {"id": "b", "text": "Estatística e matemática", "weights": {"dados_ia": 2}},
            {"id": "c", "text": "Redes de computadores e sistemas operacionais", "weights": {"devops_cloud": 2, "seguranca": 1}},
            {"id": "d", "text": "Algoritmos e estruturas de dados", "weights": {"backend": 2}},
            {"id": "e", "text": "Programação de apps e interfaces", "weights": {"mobile": 2, "frontend": 1}},
        ],
    },
    {
        "id": "projeto_portfolio",
        "text": "Que projeto você gostaria de ter no seu portfólio?",
        "options": [
            {"id": "a", "text": "Um app de celular publicado na loja", "weights": {"mobile": 2}},
            {"id": "b", "text": "Um site ou painel interativo, com animações", "weights": {"frontend": 2, "ux_ui": 1}},
            {"id": "c", "text": "Uma API usada por outros sistemas", "weights": {"backend": 2}},
            {"id": "d", "text": "Um modelo de IA que classifica imagens ou textos", "weights": {"dados_ia": 2}},
            {"id": "e", "text": "Um deploy automático de uma aplicação na nuvem", "weights": {"devops_cloud": 2}},
            {"id": "f", "text": "Um desafio de segurança resolvido (CTF)", "weights": {"seguranca": 2}},
            {"id": "g", "text": "A automação dos testes de um sistema", "weights": {"qa": 2}},
        ],
    },
    {
        "id": "resultado_do_trabalho",
        "text": "Como você prefere ver o resultado do seu trabalho?",
        "options": [
            {"id": "a", "text": "Na tela, na hora, assim que eu salvo o código", "weights": {"frontend": 2, "mobile": 1}},
            {"id": "b", "text": "Em pessoas usando o produto com mais facilidade", "weights": {"ux_ui": 2, "mobile": 1}},
            {"id": "c", "text": "Em sistemas estáveis que aguentam muitos acessos", "weights": {"devops_cloud": 2, "backend": 1}},
            {"id": "d", "text": "Em gráficos e indicadores que mudam decisões", "weights": {"dados_ia": 2}},
            {"id": "e", "text": "Em um sistema sem falhas e com qualidade comprovada", "weights": {"qa": 2}},
            {"id": "f", "text": "Em ataques evitados e dados protegidos", "weights": {"seguranca": 2}},
        ],
    },
    {
        "id": "frase",
        "text": "Qual frase combina mais com você?",
        "options": [
            {"id": "a", "text": "Gosto de entender por que cada parte do sistema funciona", "weights": {"backend": 2}},
            {"id": "b", "text": "Sou curioso(a) e adoro investigar", "weights": {"dados_ia": 1, "seguranca": 1}},
            {"id": "c", "text": "Me importo muito com a experiência das pessoas", "weights": {"ux_ui": 2, "frontend": 1}},
            {"id": "d", "text": "Gosto de automatizar tudo que é repetitivo", "weights": {"devops_cloud": 2}},
            {"id": "e", "text": "Estou sempre testando apps novos no celular", "weights": {"mobile": 2}},
            {"id": "f", "text": "Sou detalhista e não deixo nada passar", "weights": {"qa": 2}},
        ],
    },
]
