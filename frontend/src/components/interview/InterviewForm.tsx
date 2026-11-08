import { useState, type FormEvent } from "react";
import { PRESENTATION_TYPES } from "@/types/interview";

export type InterviewFormValues = {
  jobTitle: string;
  presentationType: string;
  jobDescription: string;
};

type InterviewFormProps = {
  isSubmitting: boolean;
  onSubmit: (values: InterviewFormValues) => void;
  // Cargo já preenchido (ex.: sugerido pelo questionário de área).
  initialJobTitle?: string;
};

export function InterviewForm({ isSubmitting, onSubmit, initialJobTitle = "" }: InterviewFormProps) {
  const [jobTitle, setJobTitle] = useState(initialJobTitle);
  const [presentationType, setPresentationType] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const selectedType = PRESENTATION_TYPES.find((type) => type.value === presentationType);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;
    if (!jobTitle.trim()) {
      setValidationMessage("Informe o cargo da vaga.");
      return;
    }
    if (!presentationType) {
      setValidationMessage("Selecione o tipo de entrevista.");
      return;
    }
    if (jobDescription.trim().length < 20) {
      setValidationMessage("Descreva a vaga com pelo menos 20 caracteres.");
      return;
    }
    setValidationMessage(null);
    onSubmit({ jobTitle: jobTitle.trim(), presentationType, jobDescription: jobDescription.trim() });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full flex-col gap-5 rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8"
    >
      <div className="flex flex-col gap-1.5">
        <label htmlFor="job-title" className="text-sm font-medium text-card-foreground">
          Vaga / Cargo
        </label>
        <input
          id="job-title"
          type="text"
          value={jobTitle}
          onChange={(e) => setJobTitle(e.target.value)}
          placeholder="Ex.: Analista de Dados"
          required
          className="rounded-lg border border-input bg-background px-3 py-2.5 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="presentation-type" className="text-sm font-medium text-card-foreground">
          Tipo de entrevista
        </label>
        <select
          id="presentation-type"
          value={presentationType}
          onChange={(e) => setPresentationType(e.target.value)}
          required
          className="rounded-lg border border-input bg-background px-3 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
        >
          <option value="" disabled>
            Selecione uma opção
          </option>
          {PRESENTATION_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-baseline justify-between">
          <label htmlFor="job-description" className="text-sm font-medium text-card-foreground">
            Descrição da vaga
          </label>
          {jobDescription.length > 0 && (
            <span className="text-xs text-muted-foreground">{jobDescription.length} caracteres</span>
          )}
        </div>
        {selectedType && (
          <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2.5 text-sm text-primary">
            <p className="font-semibold">A IA vai conduzir uma entrevista {selectedType.label.toLowerCase()}</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{selectedType.description}</p>
          </div>
        )}
        <textarea
          id="job-description"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Cole aqui a descrição da vaga, requisitos ou principais responsabilidades."
          rows={5}
          required
          className="resize-none rounded-lg border border-input bg-background px-3 py-2.5 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
        <span className="text-xs text-muted-foreground">
          Informe pelo menos 20 caracteres para a IA gerar perguntas específicas.
        </span>
        {validationMessage && (
          <p className="text-sm text-destructive" role="alert">
            {validationMessage}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="mt-1 inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
        )}
        {isSubmitting ? "Preparando suas perguntas…" : "Gerar entrevista"}
      </button>
    </form>
  );
}
