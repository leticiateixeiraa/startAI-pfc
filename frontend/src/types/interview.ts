// Tipos compartilhados com o contrato do backend FastAPI.

export type InterviewRequest = {
  job_title: string;
  presentation_type: string;
  job_description?: string;
  seniority?: string;
};

export type InterviewQuestion = {
  order: number;
  text: string;
};

export type InterviewResponse = {
  session_id: string;
  questions: InterviewQuestion[];
};

export const PRESENTATION_TYPES = [
  {
    value: "comportamental",
    label: "Comportamental",
    description: "Situações reais, decisões e resultados usando a estrutura STAR.",
  },
  {
    value: "tecnica",
    label: "Técnica",
    description: "Conhecimentos técnicos, raciocínio e resolução prática de problemas.",
  },
  {
    value: "mista",
    label: "Mista",
    description: "Entrevista equilibrada, combinando perguntas comportamentais e técnicas.",
  },
  {
    value: "apresentacao_pessoal",
    label: "Apresentação pessoal",
    description: "Trajetória, motivação, clareza e organização da sua narrativa.",
  },
] as const;

export function presentationTypeLabel(value: string): string {
  return PRESENTATION_TYPES.find((t) => t.value === value)?.label ?? value;
}

// Nível da vaga: deve acompanhar SENIORITY_LEVELS do backend (questions/llm_service.py).
export const SENIORITY_LEVELS = [
  { value: "estagio", label: "Estágio", description: "Fundamentos, projetos acadêmicos e vontade de aprender." },
  { value: "junior", label: "Júnior", description: "Fundamentos aplicados a tarefas bem definidas." },
  { value: "pleno", label: "Pleno", description: "Autonomia, decisões técnicas e trade-offs." },
  { value: "senior", label: "Sênior", description: "Arquitetura, decisões de alto impacto e liderança técnica." },
] as const;

export function seniorityLabel(value: string): string {
  return SENIORITY_LEVELS.find((level) => level.value === value)?.label ?? value;
}
