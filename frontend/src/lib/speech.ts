// Leitura das perguntas em voz alta (síntese de voz do próprio navegador).
// Não envia nada para servidor: é a Web Speech API local.

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

export function cancelSpeech(): void {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.cancel();
}

export function speakText(text: string): void {
  if (!isSpeechSynthesisSupported()) return;
  cancelSpeech();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "pt-BR";
  const portugueseVoice = window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang.toLowerCase().startsWith("pt-br"));
  if (portugueseVoice) utterance.voice = portugueseVoice;
  window.speechSynthesis.speak(utterance);
}
