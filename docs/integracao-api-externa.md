# Integração com API externa — Google Gemini

## Visão geral

O StartAI usa a API do **Google Gemini** para gerar e adaptar dinamicamente
as perguntas das entrevistas simuladas. A integração está isolada no módulo
`backend/app/questions/llm_service.py`, que expõe duas funções usadas pelo
resto do backend: `generate_questions` (gera o roteiro inicial de perguntas)
e `generate_adapted_question` (gera a próxima pergunta, adaptada à resposta
anterior do usuário).

## Projeto lógico

### Onde a integração se encaixa

Front-end (React)
│ POST /interviews { job_title, presentation_type, job_description }
▼
FastAPI — questions/router.py (start_interview)
│
▼
questions/service.py
│ chama generate_questions(...)
▼
questions/llm_service.py ──▶ Google Gemini (genai.Client)
│
▼ { "questions": ["...", "...", ...] }
InterviewQuestion (banco) ──▶ resposta ao front-end


Para a adaptação de perguntas durante a entrevista, o fluxo é semelhante,
partindo de `interview/service.py` e chamando `generate_adapted_question`.

### Fluxo de geração das perguntas iniciais (`generate_questions`)

1. O usuário informa cargo/tipo de apresentação e, opcionalmente, a
   descrição da vaga.
2. O backend monta um *prompt* em português combinando esses dados com uma
   regra específica da modalidade (`INTERVIEW_RULES`), que ajusta o foco das
   perguntas: comportamental (estrutura STAR), técnica, mista ou
   apresentação pessoal.
3. O Gemini é instruído a responder **apenas em JSON** (`response_mime_type:
   "application/json"`), no formato `{"questions": ["pergunta 1", ...]}`,
   com temperatura 0.7.
4. O backend valida a resposta: confere se é uma lista, remove itens vazios,
   e exige no mínimo 5 perguntas — se a resposta não seguir o contrato,
   levanta `LLMGenerationError` em vez de propagar um erro genérico.

### Fluxo de adaptação de pergunta (`generate_adapted_question`)

Mesma lógica, mas o *prompt* inclui o histórico de perguntas e respostas já
dadas na sessão, pedindo uma única pergunta nova em JSON
(`{"question": "..."}`), que aprofunda um ponto da resposta anterior sem
repetir perguntas já feitas.

## Tratamento de erros e resiliência

- **Retentativas automáticas:** erros temporários do Gemini (HTTP 429, 500,
  502, 503, 504) disparam até 3 tentativas, com espera exponencial (1s, 2s)
  entre elas — implementado em `_generate_content`.
- **Erros definitivos** (ex.: chave inválida — 401/403, modelo não
  disponível — 404) não são repetidos; a função levanta imediatamente
  `LLMGenerationError` com uma mensagem específica para o usuário
  (`_generation_error_message`).
- **Validação de saída:** mesmo com resposta HTTP 200, o backend valida se o
  conteúdo é um JSON no formato esperado antes de aceitar — protegendo o
  sistema contra uma resposta do modelo fora do contrato.
- Na API, `LLMGenerationError` é convertida em **HTTP 502** (Bad Gateway),
  sinalizando ao front-end que a falha é de um serviço externo, não do
  próprio backend (`questions/router.py`).

## Configuração

A integração depende de duas variáveis de ambiente, definidas no `.env` da
raiz do projeto (nunca no código-fonte):

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `GEMINI_API_KEY` | Sim | — | Chave da API, gerada em https://aistudio.google.com/apikey |
| `GEMINI_MODEL` | Não | `gemini-3.6-flash` | Modelo do Gemini utilizado |

Se `GEMINI_API_KEY` não estiver configurada, as funções levantam
`LLMGenerationError` de forma explícita, em vez de falhar silenciosamente.

## Limitações conhecidas

- Não há cache de perguntas: cada nova sessão de entrevista gera uma nova
  chamada ao Gemini, mesmo para cargos/descrições repetidos.
- O limite de 3 tentativas e o tempo de espera são fixos no código, não
  configuráveis via `.env`.
- Não há um limite de uso (*rate limiting*) por usuário para as chamadas ao
  Gemini, o que pode ficar caro em caso de abuso — ponto de atenção para
  produção.