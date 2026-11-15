# StartAI

**Simulador Inteligente de Entrevistas e Apresentações com Feedback por Inteligência Artificial**

Plataforma web para treinamento de comunicação de estudantes por meio de entrevistas simuladas, com perguntas geradas por IA e avaliação automática das respostas.

Projeto Final de Curso (PFC) — Bacharelado em Engenharia de Software, Universidade de Mogi das Cruzes (UMC).

---

## Sobre o projeto

A comunicação oral é um dos fatores mais relevantes para o sucesso em entrevistas de emprego, apresentações acadêmicas e processos seletivos, mas grande parte dos estudantes não tem acesso a ambientes de treinamento que permitam praticar essas situações e receber retorno objetivo sobre o próprio desempenho.

O **StartAI** propõe resolver essa lacuna com uma plataforma web que:
- gera perguntas dinamicamente por meio de Inteligência Artificial, adaptadas à vaga ou ao tipo de apresentação escolhida;
- aceita respostas por texto ou por voz, com transcrição automática da fala (Speech-to-Text);
- avalia cada resposta por IA (relevância, coerência, completude e adequação), com nota, pontos de melhoria e sugestão de resposta;
- analisa o currículo do estudante e sugere melhorias;
- gera trilhas de estudo a partir dos pontos fracos e recomenda vagas reais compatíveis com o desempenho;
- mantém um histórico de sessões para que o estudante acompanhe sua evolução ao longo do tempo;
- oferece um painel administrativo com métricas, gestão de usuários e auditoria, em conformidade com a LGPD.

## Equipe

| Integrante | RGM |
|---|---|
| Gabriel Sant'Anna Morais dos Santos | 11251401902 |
| Leonardo Giampaglia Gomes | 11231103169 |
| Letícia Teixeira da Rocha Batista | 11251401609 |

**Orientadora:** Prof. Viviane Guimaraes Ribeiro

## Links

- **Repositório:** https://github.com/leticiateixeiraa/startAI-pfc
- **Sistema publicado:** https://start-ai-pfc.vercel.app (API: https://startai-api.onrender.com/docs)
- **Protótipo inicial:** [Excalidraw](https://excalidraw.com/#room=c32bc75f252f581eb196,eyeJOwdcVDtgzDAnt68_bw)
- **Evidências de desenvolvimento:** [docs/evidencias](docs/evidencias/README.md) (prints de cada funcionalidade e resultados dos testes)

---

## Funcionalidades

Escopo definido na Ficha de Caracterização do projeto. Situação em novembro/2026:

| # | Funcionalidade | Responsável | Situação |
|---|---|---|---|
| 1 | Cadastro, login e autenticação (JWT, bcrypt, recuperação de senha) | Letícia | ✅ Pronta |
| 2 | Seleção da vaga/tipo de apresentação e perguntas geradas por IA | Leonardo | ✅ Pronta |
| 3 | Entrevistador dinâmico (adaptação das perguntas às respostas) | Gabriel | ✅ Pronta |
| 4 | Captura de áudio e transcrição da resposta (Speech-to-Text) | Gabriel | ✅ Pronta |
| 5 | Análise de currículo por IA (substituiu o analisador de oratória) | Gabriel | ✅ Pronta |
| 6 | Histórico de entrevistas e painel de evolução | Leonardo | ✅ Pronta |
| 7 | Recomendação de vagas compatíveis com o perfil do aluno | Letícia | ✅ Pronta |
| 8 | Trilhas de estudo personalizadas | Leonardo | ✅ Pronta |
| 9 | Avaliação do conteúdo das respostas por IA (nota e feedback) | Letícia | ✅ Pronta |
| 10 | Painel administrativo (usuários, auditoria geral, métricas e exclusão LGPD) | Letícia | ✅ Pronta |

**Mudança de escopo:** o analisador de oratória (funcionalidade 5 da ficha) foi substituído pela [análise de currículo](#análise-de-currículo), decisão da equipe registrada na monografia.

**Além das 10 funcionalidades:** questionário de área no primeiro acesso, perfil comportamental e [exclusão de conta](#exclusão-de-conta-lgpd).

**Fora do escopo:** análise de oratória (ritmo e vícios de linguagem), análise de linguagem corporal por vídeo, candidatura a vagas diretamente pela plataforma e recursos de gamificação ou comparação social entre usuários.

## Arquitetura

O sistema segue o modelo cliente-servidor, dividido em camadas de apresentação, processamento e persistência:

- **Apresentação:** aplicação web em React, responsável pela interação com o usuário (entrevistas, gravação de áudio, resultados, perfil, trilhas, vagas, currículo e administração).
- **Processamento:** API REST em FastAPI, responsável pela autenticação, entrevistas, transcrição, avaliação das respostas, análise de currículo, trilhas, recomendação de vagas, auditoria e integração com os serviços externos (Gemini e Jooble).
- **Persistência:** PostgreSQL para dados relacionais. O áudio das respostas é processado em memória e descartado logo após a transcrição: nenhum arquivo de áudio (nem de currículo) é armazenado.

## Tecnologias

| Categoria | Tecnologia |
|---|---|
| Front-end | React.js (TypeScript), Vite, TanStack Router/Start, TailwindCSS, shadcn/ui |
| Back-end | Python, FastAPI |
| Banco de dados | PostgreSQL, com SQLAlchemy (ORM) |
| APIs de IA | Google Gemini (geração e adaptação de perguntas, avaliação das respostas, transcrição do áudio e análise de currículo) |
| API de vagas | Jooble (vagas reais no Brasil, plano gratuito) |
| Testes e qualidade | Pytest e pytest-cov (back-end, 364 testes, 97% de cobertura); Oxlint (front-end) |
| Segurança | JWT, bcrypt |
| Versionamento | Git e GitHub |
| Deploy | Front-end na Vercel; back-end e PostgreSQL no Render |

## Metodologia

Desenvolvimento conduzido com **Scrum** (SCHWABER; SUTHERLAND, 2020), com gestão das tarefas em quadro Kanban no Trello. Requisitos levantados por meio de histórias de usuário; modelagem com prototipação de telas, Diagrama de Classes (UML) e BPMN; validação por revisão de sprint com o grupo e testes automatizados.

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

O sistema trata dados pessoais do usuário (cadastro, áudio das respostas, transcrições, avaliações, vagas recomendadas e a análise do currículo). Os áudios e os arquivos de currículo são descartados após o processamento (só o texto transcrito e o resultado da análise ficam salvos), as senhas são armazenadas com criptografia (bcrypt) e o usuário pode excluir a própria conta e todos os dados a qualquer momento, na página **Minha conta**.

## Auditoria e logs

O backend registra eventos relevantes na tabela `audit_logs`. Cada evento pode
conter usuário, ação, recurso afetado, identificador do recurso, data/hora,
endereço IP e detalhes adicionais em JSON serializado. São registrados eventos
de autenticação, início e respostas de entrevistas, transcrições de áudio (`interview.audio_transcribed`, só com duração e número de palavras), análises de currículo (`resume.analyzed`, só com tipo do arquivo e nota) e alterações no roadmap.

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
- **Usuários** (`GET /admin/users`, `PATCH /admin/users/{id}`,
  `DELETE /admin/users/{id}`): busca, desativação/reativação e exclusão de
  contas (veja [Exclusão de conta](#exclusão-de-conta-lgpd)). Conta desativada
  perde o acesso na hora;
- **Auditoria geral** (`GET /admin/audit/logs`): eventos de todos os usuários,
  com filtros por usuário, ação e período. O próprio acesso fica auditado.

O administrador **não** vê o conteúdo das respostas das entrevistas
(minimização de dados, LGPD). O cadastro público nunca cria administradores:
o papel é concedido por quem tem acesso ao servidor, na pasta `backend/`:

```bash
python -m app.scripts.promote_admin email@exemplo.com          # torna admin
python -m app.scripts.promote_admin email@exemplo.com --revoke # remove
```

## Recomendação de vagas

A página **Vagas** mostra vagas **reais** publicadas no último mês no Brasil,
buscadas na API da [Jooble](https://br.jooble.org/api/about), e ordena cada uma
por **compatibilidade** com o perfil do aluno (`app/jobs/`). A candidatura
é feita no site da vaga, pois candidatar-se pela plataforma está fora do escopo.

**Perfil do aluno**, montado com o que ele já fez no StartAI:

| Dado | De onde vem |
|---|---|
| Cargo | Cargo mais treinado nas entrevistas; sem entrevista, o primeiro cargo da área indicada pelo questionário |
| Nível | Nível escolhido nas entrevistas (estágio a sênior), ajustado pelo desempenho |
| Desempenho | Média das notas da avaliação por IA |
| Habilidades | Tecnologias citadas no cargo e nas respostas das entrevistas, mais as da área do questionário |

**Regras de negócio** (`app/jobs/service.py`):

- **RN01:** só há recomendação com ao menos uma entrevista com cargo ou o
  questionário respondido; sem isso, a página convida a treinar;
- **RN02, nível compatível com o desempenho:** com média ≥ 7, o nível treinado;
  entre 4 e 7, o mesmo nível com sugestão de treinar mais; abaixo de 4, um nível
  abaixo (ex.: júnior → estágio);
- **RN03, compatibilidade de 0 a 100%** calculada pelo backend: até 50 pontos
  pelo título (palavras do cargo), até 25 pelo nível e até 25 pelas
  habilidades do aluno citadas na vaga. Cada vaga mostra os motivos;
- **RN04:** as vagas ficam salvas por 24 h (tabela `job_recommendations`).
  Reabrir a página não gasta a cota da API (o plano gratuito da Jooble tem
  500 chamadas no total por chave); o botão **Atualizar vagas** força
  uma nova busca, e mudar de cargo ou de nível invalida a lista;
- **RN05:** se a Jooble falhar, aparecem as últimas vagas salvas, com aviso.

**LGPD:** para a Jooble vai só o texto da busca (cargo e nível); nome,
e-mail e respostas não saem do backend. As vagas salvas são apagadas na
exclusão da conta. A busca na API é auditada como `jobs.recommended`, só com
a quantidade de vagas. Os links das vagas só são aceitos se forem `http(s)`.

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/jobs/recommendations` | Perfil e vagas recomendadas (`?refresh=true` força nova busca) |

## Exclusão de conta (LGPD)

O direito de eliminação dos dados (LGPD, Art. 18, VI) pode ser exercido de
dois jeitos, com a mesma regra (`app/lgpd/service.py`):

- **Pelo próprio usuário**, na página **Minha conta** (`DELETE /auth/me`),
  digitando a senha de novo para confirmar;
- **Pelo administrador**, em Administração > Usuários
  (`DELETE /admin/users/{id}`), para atender um pedido recebido por outro
  canal. O admin não exclui a si mesmo nem outro administrador.

O que acontece na exclusão:

- **São apagados** o cadastro, as entrevistas (sessões, perguntas e
  respostas), as avaliações da IA, os perfis comportamentais, o questionário
  de primeiro acesso, a análise de currículo, as trilhas de estudo, as vagas recomendadas e os tokens
  de redefinição de senha;
- **A auditoria é anonimizada, e não apagada:** o vínculo com a pessoa
  (`user_id`) e o IP são removidos, mas o registro do evento continua, para
  fins de segurança (legítimo interesse);
- Tudo ocorre em **uma única transação**: se algo falhar, nada é apagado;
- A exclusão fica registrada como `lgpd.account_deleted` (pelo titular) ou
  `admin.user_deleted` (pelo admin), sem dados pessoais;
- O último administrador ativo não pode excluir a própria conta.

Diferença para **desativar**: a conta desativada perde o acesso, mas os dados
continuam no banco e podem ser reativados.

## Resposta por voz

Na tela de perguntas, o botão **Responder por voz** grava a resposta pelo
microfone e a transcreve com o Gemini. O texto cai na caixa de resposta, onde
a pessoa revisa e corrige antes de enviar. Também há o botão **Ouvir pergunta**
(e a opção de ler cada pergunta automaticamente), que usa a síntese de voz do
próprio navegador.

- **Endpoint:** `POST /interviews/{id}/transcribe` (multipart, campo `audio`).
  Devolve `transcript`, `duration_seconds` e `word_count`. Só o dono da sessão
  acessa, e a sessão não pode estar finalizada.
- **Formato:** o navegador converte a gravação (webm no Chrome, mp4 no Safari)
  para WAV mono de 16 kHz antes de enviar, então o backend recebe sempre o mesmo
  formato. Limites: 3 minutos de gravação e 10 MB por áudio.
- **Transcrição literal:** hesitações e vícios de linguagem ("é", "né", "tipo")
  são mantidos de propósito, o que permite uma futura análise de oratória.
- **Dados salvos:** cada resposta guarda `input_mode` (`text` ou `voice`) e
  `audio_duration_seconds`, que servem para calcular palavras por minuto.
- **Privacidade:** o áudio é lido em memória e descartado após a transcrição; a
  auditoria registra só duração e número de palavras.
- **Requisitos:** `GEMINI_API_KEY` configurada; o microfone só funciona em
  `localhost` ou em https.

## Análise de currículo

Em **Meu perfil**, o aluno anexa o currículo e a IA devolve uma análise. É a
funcionalidade 5 da versão atual, no lugar do analisador de oratória previsto
na ficha.

- **Endpoints:** `POST /resume/analyze` (multipart: `file` e `target_role`,
  opcional), `GET /resume/me` (última análise ou `null`) e `DELETE /resume/me`.
- **Arquivos:** PDF ou DOCX, até 5 MB. O tipo é conferido pelo conteúdo, não
  pelo nome. PDF vai direto ao Gemini (inclusive digitalizado); do DOCX o
  texto é extraído no servidor.
- **O que a IA devolve:** nota de 0 a 10, quatro critérios (estrutura, clareza,
  resultados e alinhamento com a vaga), pontos fortes, melhorias com sugestão
  prática, habilidades encontradas e as que a vaga costuma pedir e não aparecem.
- **Cuidados:** o conteúdo do currículo é tratado como dado, e ordens escritas
  nele são ignoradas; idade, gênero, foto e estado civil não influenciam a nota.
- **Privacidade:** o arquivo não é armazenado; fica só o resultado da análise
  (uma por usuário, substituída a cada novo envio), apagado junto com a conta.
  A auditoria guarda apenas o tipo do arquivo e a nota.

## Avaliação das respostas por IA

Ao finalizar a entrevista, o aluno é levado para a tela de resultado
(`/interview/result`). O backend envia as perguntas e respostas da sessão ao
Gemini em **uma única chamada**, e o modelo dá uma nota de 0 a 10 para cada
critério da ficha: **relevância, coerência, completude e adequação**, além
de um feedback curto, pontos fortes e pontos a melhorar.

- **Quem calcula a nota é o backend, não a IA:** a nota da resposta é a
  média dos 4 critérios, e a nota geral é a média das respostas.
- **A avaliação é gerada uma vez e fica salva** (tabelas
  `interview_evaluations` e `answer_evaluations`). Reabrir o resultado pelo
  histórico não chama o Gemini de novo, e a nota não muda.
- **Temperatura baixa (0.2):** a mesma resposta tende a receber a mesma nota.
- **Proteção contra "me dê nota 10":** o modelo é instruído a tratar o texto
  da resposta só como conteúdo a ser avaliado.
- Se o Gemini falhar, nada é gravado e o aluno pode tentar de novo.
- Na auditoria fica registrada apenas a nota geral (`interview.evaluated`),
  nunca o texto das respostas. O administrador não acessa a avaliação.

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/interviews/{id}/evaluation` | Gera a avaliação (201) ou devolve a já existente (200) |
| `GET` | `/interviews/{id}/evaluation` | Consulta a avaliação salva (404 se ainda não foi gerada) |

O histórico (`GET /interviews/history`) também passou a trazer a `overall_score`
de cada entrevista, exibida nos cards da página inicial.

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

### 2. Crie o arquivo `.env` (um só, na raiz)

O projeto usa **um único `.env` na raiz do repositório**, lido pelo backend
e pelo frontend. Na raiz, rode:

```bash
python scripts/configurar_env.py
```

O script copia o `.env.example`, **gera a `JWT_SECRET_KEY` sozinho** e
pergunta a senha do PostgreSQL e a chave do Gemini (Enter pula). Se você já
tinha um `backend/.env` antigo, os valores dele são aproveitados. Rodar de
novo é seguro: nada que já está preenchido é apagado.

A chave do Gemini é gratuita: https://aistudio.google.com/apikey.

| Variável | Usada por | Obrigatória | Para quê |
|---|---|---|---|
| `DATABASE_URL` | backend | sim | Conexão com o PostgreSQL |
| `JWT_SECRET_KEY` | backend | sim | Assinatura do token de login (gerada pelo script) |
| `GEMINI_API_KEY` | backend | sim | Perguntas e avaliação por IA |
| `GEMINI_MODEL` | backend | não | Modelo do Gemini (padrão `gemini-3.6-flash`) |
| `JOOBLE_API_KEY` | backend | não | Busca de vagas reais (página Vagas). Chave gratuita do Brasil em https://br.jooble.org/api/about |
| `JOOBLE_API_URL` | backend | não | Endereço da API (padrão `https://br.jooble.org/api/`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | não | Validade do login (padrão 1440 = 24h) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | backend | não | E-mail de "esqueci minha senha" |
| `FRONTEND_URL` | backend | não | Endereço usado no link do e-mail |
| `CORS_ORIGINS` | backend | não | Sites que podem chamar a API (separados por vírgula) |
| `VITE_API_URL` | frontend | não | Endereço da API (padrão `http://localhost:8000`) |

**Por segurança, o backend se recusa a iniciar** sem `DATABASE_URL` e
`JWT_SECRET_KEY`. Sem SMTP, cadastro e login funcionam normalmente; só o
"esqueci minha senha" fica indisponível. Com Gmail, `SMTP_PASSWORD` precisa
ser uma **senha de app** (https://myaccount.google.com/apppasswords), o que
exige verificação em duas etapas na conta.

> O `.env` nunca vai para o GitHub (está no `.gitignore`). Só variáveis com
> prefixo `VITE_` chegam ao navegador, então nenhum segredo vai para o front.

### 3. Rode o backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
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

### 5. Rode os testes

```bash
cd backend
pytest
```

Os testes usam um SQLite em memória e o Gemini, a Jooble e o SMTP simulados:
não precisam de PostgreSQL, de `.env` nem de internet. Na versão de
14/11/2026 são **364 testes, todos passando**. Para medir a cobertura (97%):

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term
```

O resultado completo está em
[docs/evidencias/testes](docs/evidencias/testes/cobertura-backend.txt). No frontend, `npm run lint` roda o
Oxlint e `npm run build` faz a checagem de tipos.

## Deploy

O backend e o banco vão para o **Render**, e o frontend para a **Vercel**.
As variáveis são as mesmas do `.env`, cadastradas no painel de cada serviço.

### Backend + PostgreSQL (Render)

1. No Render: **New > Blueprint** e escolha este repositório. O arquivo
   `render.yaml` cria o banco `startai-db` e a API `startai-api` já ligados.
2. A `DATABASE_URL` vem do banco e a `JWT_SECRET_KEY` é gerada pelo próprio
   Render. Na criação, preencha `GEMINI_API_KEY`, `JOOBLE_API_KEY`,
   `FRONTEND_URL`, `CORS_ORIGINS` e, se quiser o e-mail, `SMTP_USER` e
   `SMTP_PASSWORD`. Como a Vercel ainda não existe nesse momento, use
   `http://localhost:5173` em `FRONTEND_URL` e `CORS_ORIGINS` e troque depois.
3. O teste de saúde usa `GET /health`. As tabelas são criadas sozinhas na
   primeira inicialização.

### Frontend (Vercel)

1. Na Vercel: **Add New > Project**, escolha o repositório e defina
   **Root Directory = `frontend`**.
2. Em **Environment Variables**, cadastre `VITE_API_URL` com a URL da API no
   Render (ex.: `https://startai-api.onrender.com`).
3. O `frontend/vercel.json` redireciona todas as rotas para o `index.html`,
   para links como `/reset-password?token=...` funcionarem ao abrir direto.

### Ligando os dois

No Render, em **startai-api > Environment**, troque `FRONTEND_URL` e
`CORS_ORIGINS` pela URL final da Vercel, **sem barra no final**, e salve. Sem
isso, o site abre, mas o login falha por CORS.

### Primeiro administrador em produção

O plano gratuito do Render não tem terminal. O admin é definido a partir da
sua máquina, apontando para o banco do Render:

1. Cadastre a conta pelo site publicado (use uma conta de teste).
2. No Render, em **startai-db > Connections**, copie a **External Database URL**.
3. Na pasta `backend/`, com o venv ativo:

```powershell
$env:DATABASE_URL="EXTERNAL_DATABASE_URL_DO_RENDER"   # PowerShell
python -m app.scripts.promote_admin email-da-conta@teste.com
```

Feche o terminal depois, para essa variável não continuar valendo.

### Limites do plano gratuito

- A API **dorme após 15 minutos sem uso** e leva cerca de 1 minuto para
  acordar. Abra o site alguns minutos antes de uma apresentação.
- O **PostgreSQL gratuito do Render expira 30 dias após a criação** (com 14 dias
  de carência). Para uso mais longo, crie o banco no Neon (gratuito, não expira)
  e cadastre a URL dele em `DATABASE_URL`.
- As chaves (`GEMINI_API_KEY`, `JOOBLE_API_KEY`, SMTP) ficam só no painel do
  Render; nunca no GitHub.

---

Projeto acadêmico desenvolvido para o Projeto Final de Curso (PFC) de Engenharia de Software — UMC, 2026.