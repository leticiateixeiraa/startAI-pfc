import { Loader2, Mic, Square } from "lucide-react";
import { useState } from "react";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { blobToWav } from "@/lib/audio";

export const MAX_RECORDING_SECONDS = 180;

type VoiceRecorderProps = {
  disabled?: boolean;
  // Recebe o WAV já convertido; o pai envia ao backend e usa o texto devolvido.
  // Se lançar erro, a mensagem é mostrada aqui.
  onAudioReady: (wav: Blob, durationSeconds: number) => Promise<void>;
  onStart?: () => void;
};

function formatTime(seconds: number): string {
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

export function VoiceRecorder({ disabled, onAudioReady, onStart }: VoiceRecorderProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingError, setProcessingError] = useState<string | null>(null);

  async function handleRecorded(blob: Blob) {
    setIsProcessing(true);
    setProcessingError(null);
    try {
      const { wav, durationSeconds } = await blobToWav(blob);
      await onAudioReady(wav, durationSeconds);
    } catch (error) {
      setProcessingError(
        error instanceof Error && error.message ? error.message : "Não foi possível transcrever o áudio.",
      );
    } finally {
      setIsProcessing(false);
    }
  }

  const recorder = useAudioRecorder({ maxSeconds: MAX_RECORDING_SECONDS, onRecorded: handleRecorded });
  const errorMessage = recorder.error ?? processingError;

  if (!recorder.isSupported) {
    return (
      <p className="text-xs text-muted-foreground">
        Gravação por voz indisponível neste navegador (ou fora de conexão segura). Digite sua resposta.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-3">
        {recorder.status === "recording" ? (
          <>
            <button
              type="button"
              onClick={recorder.stop}
              className="inline-flex items-center gap-2 rounded-lg bg-destructive px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-destructive/90"
            >
              <Square className="h-4 w-4 fill-current" aria-hidden />
              Parar e transcrever
            </button>
            <button
              type="button"
              onClick={recorder.cancel}
              className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              Cancelar
            </button>
            <span className="inline-flex items-center gap-2 text-sm tabular-nums text-foreground" role="timer">
              <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-destructive" aria-hidden />
              Gravando {formatTime(recorder.elapsed)} / {formatTime(MAX_RECORDING_SECONDS)}
            </span>
          </>
        ) : (
          <button
            type="button"
            onClick={() => {
              setProcessingError(null);
              onStart?.();
              void recorder.start();
            }}
            disabled={disabled || isProcessing || recorder.status === "requesting"}
            className="inline-flex items-center gap-2 rounded-lg border border-input bg-card px-4 py-2 text-sm font-medium text-card-foreground transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isProcessing || recorder.status === "requesting" ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Mic className="h-4 w-4" aria-hidden />
            )}
            {isProcessing
              ? "Transcrevendo..."
              : recorder.status === "requesting"
                ? "Aguardando o microfone..."
                : "Responder por voz"}
          </button>
        )}
      </div>

      {errorMessage && (
        <p className="text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
