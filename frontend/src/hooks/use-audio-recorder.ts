import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderStatus = "idle" | "requesting" | "recording";

type Options = {
  maxSeconds: number;
  minSeconds?: number;
  // Chamado com o áudio bruto quando a gravação termina (parada manual ou
  // pelo limite de tempo). Não é chamado quando a gravação é cancelada.
  onRecorded: (blob: Blob) => void;
};

function microphoneErrorMessage(error: unknown): string {
  const name = (error as { name?: string } | null)?.name;
  if (name === "NotAllowedError" || name === "SecurityError") {
    return "O acesso ao microfone foi negado. Libere a permissão no navegador e tente de novo.";
  }
  if (name === "NotFoundError" || name === "OverconstrainedError") {
    return "Nenhum microfone foi encontrado neste dispositivo.";
  }
  if (name === "NotReadableError") {
    return "Não foi possível usar o microfone. Ele pode estar em uso por outro aplicativo.";
  }
  return "Não foi possível iniciar a gravação.";
}

export function useAudioRecorder({ maxSeconds, minSeconds = 1, onRecorded }: Options) {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | undefined>(undefined);
  const startedAtRef = useRef(0);
  const discardRef = useRef(false);
  const onRecordedRef = useRef(onRecorded);

  useEffect(() => {
    onRecordedRef.current = onRecorded;
  });

  // Só no navegador (e só em https/localhost, onde o microfone é liberado).
  useEffect(() => {
    setIsSupported(
      typeof MediaRecorder !== "undefined" && typeof navigator.mediaDevices?.getUserMedia === "function",
    );
  }, []);

  const releaseMicrophone = useCallback(() => {
    window.clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    recorderRef.current = null;
  }, []);

  const stop = useCallback(() => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  }, []);

  const cancel = useCallback(() => {
    discardRef.current = true;
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    } else {
      releaseMicrophone();
      setStatus("idle");
    }
  }, [releaseMicrophone]);

  const start = useCallback(async () => {
    if (status !== "idle") return;
    setError(null);
    setElapsed(0);
    setStatus("requesting");

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      setError(microphoneErrorMessage(err));
      setStatus("idle");
      return;
    }

    streamRef.current = stream;
    chunksRef.current = [];
    discardRef.current = false;

    const recorder = new MediaRecorder(stream);
    recorderRef.current = recorder;

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };
    recorder.onstop = () => {
      const seconds = (Date.now() - startedAtRef.current) / 1000;
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
      releaseMicrophone();
      setStatus("idle");
      if (discardRef.current) return;
      if (seconds < minSeconds) {
        setError("A gravação ficou muito curta. Segure um pouco mais e fale a resposta.");
        return;
      }
      onRecordedRef.current(blob);
    };

    startedAtRef.current = Date.now();
    recorder.start();
    setStatus("recording");
    timerRef.current = window.setInterval(() => {
      const seconds = (Date.now() - startedAtRef.current) / 1000;
      setElapsed(seconds);
      if (seconds >= maxSeconds) stop();
    }, 250);
  }, [status, maxSeconds, minSeconds, releaseMicrophone, stop]);

  // Sair da tela com o microfone aberto deixaria a gravação ligada.
  useEffect(
    () => () => {
      discardRef.current = true;
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      releaseMicrophone();
    },
    [releaseMicrophone],
  );

  return { status, elapsed, error, isSupported, start, stop, cancel, clearError: () => setError(null) };
}
