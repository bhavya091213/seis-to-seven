// public/pcm-player-worklet.js
class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Int16Array(0);
    this.readIndex = 0;
    this.sampleRateTarget = sampleRate; // audio context sampleRate
    this.port.onmessage = (e) => {
      const { type, payload } = e.data || {};
      if (type === "push") {
        const chunk = new Int16Array(payload);
        // concat
        const merged = new Int16Array(this.buffer.length + chunk.length);
        merged.set(this.buffer, 0);
        merged.set(chunk, this.buffer.length);
        this.buffer = merged;
      }
    };
  }

  process(inputs, outputs, params) {
    const output = outputs[0];
    const channel = output[0]; // mono
    const frames = channel.length;

    for (let i = 0; i < frames; i++) {
      if (this.readIndex < this.buffer.length) {
        // Int16 -> Float32
        const s = this.buffer[this.readIndex++] / 32768;
        channel[i] = Math.max(-1, Math.min(1, s));
      } else {
        channel[i] = 0;
      }
    }

    // Trim consumed
    if (this.readIndex > 0 && this.readIndex >= this.buffer.length) {
      this.buffer = new Int16Array(0);
      this.readIndex = 0;
    } else if (this.readIndex > 0 && this.readIndex % 8192 === 0) {
      // occasionally compact
      const remaining = this.buffer.length - this.readIndex;
      const tmp = new Int16Array(remaining);
      tmp.set(this.buffer.subarray(this.readIndex));
      this.buffer = tmp;
      this.readIndex = 0;
    }

    return true;
  }
}

registerProcessor("pcm-player", PCMPlayerProcessor);
