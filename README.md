# StartAI

**Simulador Inteligente de Entrevistas e Apresentações com Feedback de Oratória por Inteligência Artificial**

Plataforma web para treinamento de comunicação de estudantes por meio de entrevistas simuladas, com perguntas geradas por IA e análise automática da fala.

Projeto Final de Curso (PFC) — Bacharelado em Engenharia de Software, Universidade de Mogi das Cruzes (UMC).

---

## Sobre o projeto

A comunicação oral é um dos fatores mais relevantes para o sucesso em entrevistas de emprego, apresentações acadêmicas e processos seletivos, mas grande parte dos estudantes não tem acesso a ambientes de treinamento que permitam praticar essas situações e receber retorno objetivo sobre o próprio desempenho.

O **StartAI** propõe resolver essa lacuna com uma plataforma web que:
- gera perguntas dinamicamente por meio de Inteligência Artificial, adaptadas à vaga ou ao tipo de apresentação escolhida;
- transcreve as respostas faladas usando reconhecimento automático de fala (Speech-to-Text);
- analisa a oratória do usuário, identificando métricas como vícios de linguagem, palavras repetidas, duração e velocidade da fala;
- mantém um histórico de sessões para que o estudante acompanhe sua evolução ao longo do tempo.

## Equipe

| Integrante | RGM |
|---|---|
| Gabriel Sant'Anna Morais dos Santos | 11251401902 |
| Leonardo Giampaglia Gomes | 11231103169 |
| Letícia Teixeira da Rocha Batista | 11251401609 |

**Orientadora:** Prof. Viviane Guimaraes Ribeiro

## Links

- **Repositório:** https://github.com/leticiateixeiraa/entrevistaia-pfc
- **Protótipo:** [Excalidraw](https://excalidraw.com/#room=c32bc75f252f581eb196,eyeJOwdcVDtgzDAnt68_bw)

---

## Funcionalidades

### MVP (primeira versão — escopo deste PFC)

| # | Funcionalidade | Critério de aceitação |
|---|---|---|
| 1 | Cadastro, login e autenticação do usuário | Usuário cria conta e autentica-se com segurança (e-mail/senha) |
| 2 | Seleção da vaga ou tipo de apresentação + exibição das perguntas geradas pela IA | Usuário escolhe uma categoria e recebe um conjunto de perguntas correspondente |
| 3 | Entrevistador dinâmico (geração e adaptação de perguntas) | Ao menos uma pergunta subsequente é ajustada com base na resposta dada |
| 4 | Captura de áudio e transcrição da resposta (Speech-to-Text) | Resposta falada é convertida em texto e exibida ao usuário |
| 5 | Analisador de oratória (vícios de linguagem, repetições, duração, palavras por minuto) | Relatório apresenta as métricas quantitativas de cada resposta |
| 6 | Histórico de entrevistas e painel de evolução | Usuário visualiza e compara métricas de sessões anteriores |
| 9 | Avaliação do conteúdo das respostas por IA | IA analisa relevância, coerência e completude da resposta, com nota e feedback |

**Fora do escopo do MVP:** análise de linguagem corporal por vídeo, integração com plataformas reais de recrutamento (além da API de vagas da Fase 2) e recursos de gamificação/comparação social entre usuários.

### Fase 2 (roadmap futuro)

| # | Funcionalidade | Critério de aceitação |
|---|---|---|
| 7 | Recomendação de vagas compatíveis com o perfil do aluno | Usuário recebe lista de vagas relacionadas às entrevistas praticadas |
| 8 | Trilhas de estudo personalizadas | Usuário visualiza sugestões de estudo com base nas métricas de oratória |

---

## Arquitetura

O sistema segue o modelo cliente-servidor, dividido em camadas de apresentação, processamento e persistência:

- **Apresentação:** aplicação web em React, responsável pela interação com o usuário (gerenciamento das entrevistas, gravação de áudio, relatórios e evolução do desempenho).
- **Processamento:** API REST em FastAPI, responsável pela autenticação, gerenciamento das entrevistas, transcrição, análise de oratória e integração com serviços externos de IA.
- **Persistência:** PostgreSQL para dados relacionais; Redis para gerenciamento de tarefas assíncronas do processamento de áudio; armazenamento temporário para os arquivos de áudio.

## Tecnologias

| Categoria | Tecnologia |
|---|---|
| Front-end | React.js (TypeScript), Vite, TanStack Router/Start, TailwindCSS, shadcn/ui |
| Back-end | Python, FastAPI |
| Banco de dados | PostgreSQL, com SQLAlchemy (ORM) |
| Filas / cache | Redis |
| APIs de IA | OpenAI Whisper (Speech-to-Text); Google Gemini para geração e adaptação de perguntas |
| Testes | Pytest (back-end); Jest / React Testing Library (front-end) |
| Segurança | JWT, bcrypt |
| Versionamento | Git e GitHub |
| Deploy | Front-end na Vercel; back-end no Render/Railway |

## Metodologia

Desenvolvimento conduzido com **Scrum** (SCHWABER; SUTHERLAND, 2020), com gestão das tarefas em quadro Kanban no Trello. Requisitos levantados por meio de histórias de usuário; modelagem apoiada em prototipação de telas e Diagrama de Casos de Uso (UML); validação por testes com usuários-piloto ao final de cada sprint.

## Cronograma macro

| Etapa | Período | Entregável |
|---|---|---|
| Definição e validação do problema | 03–21/08/2026 | Ficha de Caracterização do projeto |
| Levantamento de requisitos | 22–28/08/2026 | Diagrama de Arquitetura, Introdução e Referências na monografia |
| Modelagem e prototipação | 29/08–14/09/2026 | Primeira regra de negócio completa (front, back e banco) no GitHub |
| Implementação — ciclo 1 | 15–28/09/2026 | Login, auditoria/log, LGPD, integração com API externa |
| Implementação — ciclo 2 | 29/09–09/11/2026 | Requisitos funcionais/não funcionais, Diagrama de Classes, BPMN, 75% implementado |
| Testes e validação | 10–23/11/2026 | Monografia completa, slides, vídeo demonstrativo, testes com ≥50% de cobertura |
| Deploy e documentação | 30/11–07/12/2026 | Apresentação e defesa do PFC |
| Preparação final | 11–17/12/2026 | Reentrega de ajustes solicitados pela banca |

## Privacidade e LGPD

O sistema trata dados pessoais do usuário (cadastro, áudio das respostas, transcrições e métricas de oratória). Os áudios são descartados após a transcrição, as senhas são armazenadas com criptografia (bcrypt) e o usuário pode excluir seu histórico a qualquer momento.

## Auditoria e logs

O backend registra eventos relevantes na tabela `audit_logs`. Cada evento pode
conter usuário, ação, recurso afetado, identificador do recurso, data/hora,
endereço IP e detalhes adicionais em JSON serializado. São registrados eventos
de autenticação, início e respostas de entrevistas e alterações no roadmap.

O usuário autenticado consulta seus próprios eventos em `GET /audit/logs`, com
os filtros `limit` e `action`. A consulta usa o identificador extraído do JWT,
impedindo que um usuário visualize os logs de outro usuário.

## Roadmap de ensino personalizado

Um roadmap é criado por usuário em `POST /roadmaps`, com objetivo e etapas
ordenadas. Cada etapa começa como `pending` e pode ser alterada para
`in_progress` ou `completed` em
`PATCH /roadmaps/{roadmap_id}/items/{item_id}`. A aplicação pode gerar as
etapas a partir dos pontos fracos observados nas entrevistas: respostas
comportamentais curtas viram prática da estrutura STAR, desempenho técnico
baixo vira revisão do assunto e problemas de clareza viram treino de
apresentação. `GET /roadmaps` retorna os planos do usuário.

As modalidades `comportamental`, `tecnica`, `mista` e `apresentacao_pessoal`
possuem regras próprias no prompt do Gemini.

## Administração

O sistema tem dois papéis: **usuário** (padrão de todo cadastro) e
**administrador**. O administrador acessa o menu "Administração", com:

- **Painel** (`GET /admin/metrics`): usuários, entrevistas, taxa de conclusão,
  logins com falha, entrevistas por dia e por tipo;
- **Usuários** (`GET /admin/users`, `PATCH /admin/users/{id}`): busca e
  desativação/reativação de contas. Conta desativada perde o acesso na hora;
- **Auditoria geral** (`GET /admin/audit/logs`): eventos de todos os usuários,
  com filtros por usuário, ação e período. O próprio acesso fica auditado.

O administrador **não** vê o conteúdo das respostas das entrevistas
(minimização de dados, LGPD). O cadastro público nunca cria administradores:
o papel é concedido por quem tem acesso ao servidor, na pasta `backend/`:

```bash
python -m app.scripts.promote_admin email@exemplo.com          # torna admin
python -m app.scripts.promote_admin email@exemplo.com --revoke # remove
```

## Recuperação de senha

O usuário pode redefinir a própria senha em caso de esquecimento, a partir
da tela de login. Em `POST /auth/forgot-password`, o sistema gera um token
aleatório, armazena apenas o hash desse token no banco (nunca o valor em
texto puro) e envia por e-mail um link válido por 30 minutos.

Ao acessar o link, o usuário define a nova senha em
`POST /auth/reset-password`, seguindo as mesmas regras de senha forte do
cadastro. O token só pode ser usado uma vez, e a resposta da API é sempre a
mesma, com ou sem e-mail cadastrado — protegendo contra a descoberta de
quais e-mails têm conta no sistema.

## Como rodar o projeto localmente

### Pré-requisitos

- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [PostgreSQL](https://www.postgresql.org/download/) instalado e rodando
- [pgAdmin 4](https://www.pgadmin.org/) (já vem junto com o instalador do PostgreSQL) para gerenciar o banco visualmente

### 1. Crie o banco de dados

Abra o pgAdmin, conecte no seu servidor PostgreSQL e crie um banco chamado `entrevistaia` (botão direito em Databases > Create > Database).

> **Se aparecer erro de "incompatibilidade de versão de ordenação"** ao criar o banco: abra a Query Tool no banco `postgres` e rode `ALTER DATABASE template1 REFRESH COLLATION VERSION;`, depois tente criar o banco de novo.

### 2. Configure o backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Copie o `.env.example` para `.env` e ajuste a senha do seu PostgreSQL. **Por
segurança, o backend se recusa a iniciar** se `DATABASE_URL` ou
`JWT_SECRET_KEY` não forem preenchidas com um valor de verdade (o texto de
exemplo do `.env.example` não é aceito):

​```
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/entrevistaia
JWT_SECRET_KEY=
GEMINI_API_KEY=sua-chave-do-gemini-aqui
​```

Gere uma `JWT_SECRET_KEY` forte com o comando abaixo e cole o resultado no `.env`:

​```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
​```

Para gerar a `GEMINI_API_KEY`, crie uma chave gratuita em https://aistudio.google.com/apikey.

Para o envio de e-mails de recuperação de senha, configure também as
variáveis de SMTP:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=
FRONTEND_URL=http://localhost:5173

Se usar o Gmail, `SMTP_PASSWORD` precisa ser uma **senha de app** (não a
senha normal da conta), gerada em
https://myaccount.google.com/apppasswords — exige verificação em duas
etapas ativada na conta. Sem essas variáveis configuradas, o cadastro e o
login continuam funcionando normalmente; só o fluxo de "esqueci minha
senha" fica indisponível.

### 3. Rode o backend

```bash
uvicorn app.main:app --reload
```

Se aparecer `Application startup complete`, está tudo certo. Acesse **http://localhost:8000/docs** para testar os endpoints pela documentação interativa.

### 4. Rode o frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Acesse o endereço que aparecer no terminal (geralmente **http://localhost:5173**).

---

Projeto acadêmico desenvolvido para o Projeto Final de Curso (PFC) de Engenharia de Software — UMC, 2026.