import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { InterviewForm, type InterviewFormValues } from "@/components/interview/InterviewForm";
import { createInterview, ApiError } from "@/services/interviewApi";
import { saveInterviewSession } from "@/services/interviewSession";
import type { InterviewRequest } from "@/types/interview";

export const Route = createFileRoute("/interview/setup")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({
    meta: [
      { title: "Prepare sua entrevista — StartAI" },
      {
        name: "description",
        content:
          "Personalize sua simulação de entrevista e deixe a IA preparar perguntas alinhadas à oportunidade que você deseja.",
      },
      { property: "og:title", content: "Prepare sua entrevista — StartAI" },
      {
        property: "og:description",
        content:
          "Personalize sua simulação de entrevista e deixe a IA preparar perguntas alinhadas à oportunidade que você deseja.",
      },
    ],
  }),
  component: InterviewSetupPage,
});

function InterviewSetupPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastValues, setLastValues] = useState<InterviewFormValues | null>(null);

  async function generateInterview(values: InterviewFormValues) {
    setIsSubmitting(true);
    setErrorMessage(null);
    setLastValues(values);

    const request: InterviewRequest = {
      job_title: values.jobTitle,
      presentation_type: values.presentationType,
      ...(values.jobDescription ? { job_description: values.jobDescription } : {}),
    };

    try {
      const response = await createInterview(request);
      saveInterviewSession({ request, response });
      navigate({ to: "/interview/questions" });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Não foi possível gerar as perguntas. Tente novamente.";
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex flex-1 flex-col items-center bg-background px-4 py-12 sm:py-20">
      <div className="w-full max-w-xl">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Prepare sua entrevista
          </h1>
          <p className="mt-3 text-base text-muted-foreground">
            Personalize sua simulação e deixe a IA preparar perguntas alinhadas à oportunidade que
            você deseja.
          </p>
          <Link to="/home" className="mt-4 inline-block text-sm font-medium text-muted-foreground hover:text-foreground">
            Voltar ao início
          </Link>
        </header>

        {errorMessage && !isSubmitting ? (
          <div className="flex flex-col gap-6">
            <ErrorState
              message={errorMessage}
              onRetry={() => lastValues && generateInterview(lastValues)}
            />
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-sm font-medium text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
            >
              Editar configuração
            </button>
          </div>
        ) : (
          <InterviewForm isSubmitting={isSubmitting} onSubmit={generateInterview} />
        )}
      </div>
    </main>
  );
}
