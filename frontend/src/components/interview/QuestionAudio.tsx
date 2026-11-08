import { Volume2 } from "lucide-react";
import { useEffect, useState } from "react";
import { cancelSpeech, isSpeechSynthesisSupported, speakText } from "@/lib/speech";

type QuestionAudioProps = {
  text: string;
};

// Botão "Ouvir pergunta" e opção de leitura automática a cada nova pergunta.
export function QuestionAudio({ text }: QuestionAudioProps) {
  const [autoRead, setAutoRead] = useState(false);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    setSupported(isSpeechSynthesisSupported());
  }, []);

  useEffect(() => {
    if (autoRead) speakText(text);
  }, [autoRead, text]);

  // Sair da tela (ou trocar de pergunta) interrompe a leitura em andamento.
  useEffect(() => cancelSpeech, [text]);

  if (!supported) return null;

  return (
    <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-sm">
      <button
        type="button"
        onClick={() => speakText(text)}
        className="inline-flex items-center gap-2 rounded-lg border border-input bg-card px-3 py-1.5 font-medium text-card-foreground transition-colors hover:bg-accent"
      >
        <Volume2 className="h-4 w-4" aria-hidden />
        Ouvir pergunta
      </button>
      <label className="inline-flex cursor-pointer items-center gap-2 text-muted-foreground">
        <input
          type="checkbox"
          checked={autoRead}
          onChange={(event) => setAutoRead(event.target.checked)}
          className="h-4 w-4 accent-primary"
        />
        Ler perguntas automaticamente
      </label>
    </div>
  );
}
