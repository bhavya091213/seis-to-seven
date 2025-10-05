export async function startAudioGate(
  onGateOpen: () => void,
  onGateClose: () => void,
  threshold = 0.05
) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(1024, 1, 1);

  source.connect(processor);
  processor.connect(audioContext.destination);

  processor.onaudioprocess = (event) => {
    const input = event.inputBuffer.getChannelData(0);
    let sum = 0;
    for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
    const rms = Math.sqrt(sum / input.length);

    if (rms > threshold) {
      onGateOpen();
    } else {
      onGateClose();
    }
  };

  return () => {
    processor.disconnect();
    source.disconnect();
    audioContext.close();
  };
}
