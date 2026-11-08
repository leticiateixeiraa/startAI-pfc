// Conversão da gravação do navegador para WAV mono de 16 kHz.
//
// O MediaRecorder entrega webm/opus (Chrome, Firefox) ou mp4/aac (Safari), e o
// Gemini não aceita todos esses formatos. Convertendo aqui, o backend recebe
// sempre o mesmo formato, em qualquer navegador. 16 kHz mono é suficiente para
// fala e mantém o arquivo pequeno (~2 MB por minuto).

export const TARGET_SAMPLE_RATE = 16000;

type WindowWithWebkitAudio = Window & { webkitAudioContext?: typeof AudioContext };

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const bytesPerSample = 2;
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
  const view = new DataView(buffer);

  const writeText = (offset: number, text: string) => {
    for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i));
  };

  writeText(0, "RIFF");
  view.setUint32(4, 36 + samples.length * bytesPerSample, true);
  writeText(8, "WAVE");
  writeText(12, "fmt ");
  view.setUint32(16, 16, true); // tamanho do bloco fmt
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true);
  view.setUint16(32, bytesPerSample, true);
  view.setUint16(34, 16, true); // bits por amostra
  writeText(36, "data");
  view.setUint32(40, samples.length * bytesPerSample, true);

  for (let i = 0; i < samples.length; i++) {
    const clipped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * bytesPerSample, clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}

export async function blobToWav(blob: Blob): Promise<{ wav: Blob; durationSeconds: number }> {
  const AudioContextClass = window.AudioContext ?? (window as WindowWithWebkitAudio).webkitAudioContext;
  if (!AudioContextClass) throw new Error("Este navegador não consegue processar áudio.");

  const context = new AudioContextClass();
  try {
    const decoded = await context.decodeAudioData(await blob.arrayBuffer());
    // OfflineAudioContext de 1 canal reamostra para 16 kHz e junta os canais.
    const offline = new OfflineAudioContext(
      1,
      Math.max(1, Math.ceil(decoded.duration * TARGET_SAMPLE_RATE)),
      TARGET_SAMPLE_RATE,
    );
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();
    const rendered = await offline.startRendering();
    return {
      wav: encodeWav(rendered.getChannelData(0), TARGET_SAMPLE_RATE),
      durationSeconds: rendered.duration,
    };
  } finally {
    void context.close();
  }
}
