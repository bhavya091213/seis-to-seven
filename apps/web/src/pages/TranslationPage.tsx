import React, {
  useMemo,
  useRef,
  useState,
  createContext,
  useContext,
} from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Mic, Volume2 } from "lucide-react";

/** ---------------------------------- Theme ---------------------------------- */

/** ---------------------------------- Language Map ---------------------------------- */
const LANG_MAP: Record<string, string> = {
  en: "English",
  es: "Spanish",
  zh: "Chinese",
  hi: "Hindi",
  fr: "French",
  de: "German",
  pt: "Portuguese",
  ru: "Russian",
  ja: "Japanese",
  ko: "Korean",
  ar: "Arabic",
  bn: "Bengali",
  it: "Italian",
  tr: "Turkish",
  vi: "Vietnamese",
  ta: "Tamil",
  ur: "Urdu",
  fa: "Persian (Farsi)",
  pl: "Polish",
  id: "Indonesian",
  ms: "Malay",
  th: "Thai",
  sw: "Swahili",
  nl: "Dutch",
  uk: "Ukrainian",
};

/** ---------------------------------- Types ---------------------------------- */
type Side = "A" | "B";
type MicState = "INACTIVE" | "RECORDING" | "WAITING_STREAM" | "PLAYING";

type TranslationCtx = {
  langA: string;
  setLangA: (v: string) => void;
  langB: string;
  setLangB: (v: string) => void;
  currentSide: Side;
  setCurrentSide: (s: Side) => void;
  micState: MicState;
  setMicState: (m: MicState) => void;
  volume: number; // 0..1 live rms (mic while recording; stream while playing)
  setVolume: (v: number) => void;
};

const Ctx = createContext<TranslationCtx | null>(null);
const useTranslationCtx = () => {
  const c = useContext(Ctx);
  if (!c) throw new Error("useTranslationCtx must be inside provider");
  return c;
};

/** ---------------------------------- Mic Recorder (WAV 16kHz 16-bit) ---------------------------------- */
class MicRecorder {
  private stream: MediaStream | null = null;
  private audioCtx: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private worklet: AudioWorkletNode | null = null;
  private proc: ScriptProcessorNode | null = null;
  private chunks: Float32Array[] = [];
  private inputSampleRate = 48000;
  private onLevel?: (level: number) => void;

  async start(onLevel?: (level: number) => void) {
    this.onLevel = onLevel;
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
      video: false,
    });
    this.audioCtx = new (window.AudioContext ||
      (window as any).webkitAudioContext)({ sampleRate: 48000 });
    this.inputSampleRate = this.audioCtx.sampleRate;
    this.source = this.audioCtx.createMediaStreamSource(this.stream);

    if (
      this.audioCtx.audioWorklet &&
      (this.audioCtx as any).audioWorklet.addModule
    ) {
      const workletUrl = URL.createObjectURL(
        new Blob(
          [
            `
          class RecorderProcessor extends AudioWorkletProcessor {
            process(inputs) {
              const input = inputs[0];
              if (input && input[0]) {
                const ch = input[0];
                const buf = new Float32Array(ch.length);
                buf.set(ch);
                this.port.postMessage(buf, [buf.buffer]);
              }
              return true;
            }
          }
          registerProcessor('recorder-processor', RecorderProcessor);
        `,
          ],
          { type: "application/javascript" }
        )
      );
      await this.audioCtx.audioWorklet.addModule(workletUrl);
      URL.revokeObjectURL(workletUrl);

      this.worklet = new AudioWorkletNode(this.audioCtx, "recorder-processor");
      this.worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
        const block = e.data;
        this.chunks.push(block);
        if (this.onLevel) this.onLevel(this.rms(block));
      };
      this.source.connect(this.worklet);
    } else {
      // Fallback: ScriptProcessorNode
      this.proc = this.audioCtx.createScriptProcessor(2048, 1, 1);
      this.proc.onaudioprocess = (evt) => {
        const ch = evt.inputBuffer.getChannelData(0);
        const copy = new Float32Array(ch.length);
        copy.set(ch);
        this.chunks.push(copy);
        if (this.onLevel) this.onLevel(this.rms(copy));
      };
      this.source.connect(this.proc);
      this.proc.connect(this.audioCtx.destination); // needed on some browsers
    }
  }

  async stop(): Promise<Blob> {
    try {
      if (this.worklet) {
        try {
          this.worklet.port.close();
        } catch {}
        try {
          this.source?.disconnect();
        } catch {}
        try {
          this.worklet.disconnect();
        } catch {}
      }
      if (this.proc) {
        try {
          this.source?.disconnect();
        } catch {}
        try {
          this.proc.disconnect();
        } catch {}
      }
      if (this.audioCtx) await this.audioCtx.close();
      if (this.stream) this.stream.getTracks().forEach((t) => t.stop());
    } finally {
      const wav = this.floatChunksToWav(
        this.chunks,
        this.inputSampleRate,
        16000
      );
      this.stream = null;
      this.audioCtx = null;
      this.source = null;
      this.worklet = null;
      this.proc = null;
      this.chunks = [];
      return wav;
    }
  }

  private rms(arr: Float32Array) {
    let s = 0;
    for (let i = 0; i < arr.length; i++) s += arr[i] * arr[i];
    return Math.sqrt(s / arr.length);
  }
  private mergeFloat32(chunks: Float32Array[]) {
    let total = 0;
    for (const c of chunks) total += c.length;
    const out = new Float32Array(total);
    let off = 0;
    for (const c of chunks) {
      out.set(c, off);
      off += c.length;
    }
    return out;
  }
  private resampleLinear(
    input: Float32Array,
    fromRate: number,
    toRate: number
  ) {
    if (fromRate === toRate) return input;
    const ratio = fromRate / toRate;
    const newLen = Math.round(input.length / ratio);
    const out = new Float32Array(newLen);
    for (let i = 0; i < newLen; i++) {
      const idx = i * ratio;
      const i0 = Math.floor(idx);
      const i1 = Math.min(i0 + 1, input.length - 1);
      const t = idx - i0;
      out[i] = (1 - t) * input[i0] + t * input[i1];
    }
    return out;
  }
  private floatToPCM16(float32: Float32Array) {
    const pcm = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      let s = Math.max(-1, Math.min(1, float32[i]));
      pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return pcm;
  }
  private encodeWavPCM16(pcm16: Int16Array, sampleRate: number) {
    const numChannels = 1,
      blockAlign = numChannels * 2,
      byteRate = sampleRate * blockAlign,
      dataSize = pcm16.length * 2;
    const buffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(buffer);
    const w = (o: number, s: string) => {
      for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i));
    };
    w(0, "RIFF");
    view.setUint32(4, 36 + dataSize, true);
    w(8, "WAVE");
    w(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, byteRate, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, 16, true);
    w(36, "data");
    view.setUint32(40, dataSize, true);
    let off = 44;
    for (let i = 0; i < pcm16.length; i++, off += 2)
      view.setInt16(off, pcm16[i], true);
    return new Blob([view], { type: "audio/wav" });
  }
  private floatChunksToWav(
    chunks: Float32Array[],
    fromRate: number,
    toRate: number
  ) {
    const merged = this.mergeFloat32(chunks);
    const resampled = this.resampleLinear(merged, fromRate, toRate);
    const pcm16 = this.floatToPCM16(resampled);
    return this.encodeWavPCM16(pcm16, toRate);
  }
}

/** ---------------------------------- Audio Stream Player (WS -> PCM16 -> AudioContext) ---------------------------------- */
class AudioStreamPlayer {
  private ctx: AudioContext | null = null;
  private worklet: AudioWorkletNode | null = null;
  private scriptNode: ScriptProcessorNode | null = null;
  private queue: Float32Array[] = [];
  private ws: WebSocket | null = null;
  private sampleRate: number;
  private onRms?: (v: number) => void;
  private onEnd?: () => void;
  private closed = false;
  private endTimeout: number | null = null;

  constructor(sampleRate = 16000) {
    this.sampleRate = sampleRate;
  }

  private async ensureAudio() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: this.sampleRate,
    });

    // Inline AudioWorklet via Blob (no external file needed)
    try {
      const workletUrl = URL.createObjectURL(
        new Blob(
          [
            `
            class PCMPlayerProcessor extends AudioWorkletProcessor {
              constructor(){
                super();
                this.buffer = new Int16Array(0);
                this.readIndex = 0;
                this.port.onmessage = (e) => {
                  if(e.data?.type === 'push'){
                    const chunk = new Int16Array(e.data.payload);
                    const merged = new Int16Array(this.buffer.length + chunk.length);
                    merged.set(this.buffer, 0);
                    merged.set(chunk, this.buffer.length);
                    this.buffer = merged;
                  }
                };
              }
              process(inputs, outputs){
                const out = outputs[0][0];
                const N = out.length;
                for(let i=0;i<N;i++){
                  if(this.readIndex < this.buffer.length){
                    out[i] = Math.max(-1, Math.min(1, this.buffer[this.readIndex++] / 32768));
                  } else {
                    out[i] = 0;
                  }
                }
                if(this.readIndex >= this.buffer.length){
                  this.buffer = new Int16Array(0);
                  this.readIndex = 0;
                } else if(this.readIndex > 8192){
                  const rem = this.buffer.length - this.readIndex;
                  const tmp = new Int16Array(rem);
                  tmp.set(this.buffer.subarray(this.readIndex));
                  this.buffer = tmp;
                  this.readIndex = 0;
                }
                return true;
              }
            }
            registerProcessor('pcm-player', PCMPlayerProcessor);
          `,
          ],
          { type: "application/javascript" }
        )
      );
      await this.ctx.audioWorklet.addModule(workletUrl);
      URL.revokeObjectURL(workletUrl);
      this.worklet = new AudioWorkletNode(this.ctx, "pcm-player");
      this.worklet.connect(this.ctx.destination);
    } catch {
      // Fallback
      this.scriptNode = this.ctx.createScriptProcessor(2048, 0, 1);
      this.scriptNode.onaudioprocess = (e) => {
        const ch = e.outputBuffer.getChannelData(0);
        if (this.queue.length === 0) {
          ch.fill(0);
          return;
        }
        const buf = this.queue.shift()!;
        const n = Math.min(ch.length, buf.length);
        ch.set(buf.subarray(0, n));
        if (buf.length > n) this.queue.unshift(buf.subarray(n));
        else if (n < ch.length) ch.fill(0, n);
      };
      this.scriptNode.connect(this.ctx.destination);
    }
  }

  private int16ToFloat32(int16: Int16Array): Float32Array {
    const out = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) out[i] = int16[i] / 32768;
    return out;
  }

  private updateRms(int16: Int16Array) {
    if (!this.onRms) return;
    let s = 0;
    for (let i = 0; i < int16.length; i++) {
      const f = int16[i] / 32768;
      s += f * f;
    }
    const rms = Math.sqrt(s / Math.max(1, int16.length));
    const exaggerated = Math.min(1, Math.pow(rms, 0.65) * 1.35);
    this.onRms(exaggerated);
  }

  async playFromWebSocket(
    url: string,
    onRms: (v: number) => void,
    onEnd: () => void,
    maxDurationMs: number = 15000 // safety cap
  ) {
    await this.ensureAudio();
    this.onRms = onRms;
    this.onEnd = onEnd;
    this.closed = false;

    // safety: auto-stop after maxDurationMs in case server never closes
    if (this.endTimeout) window.clearTimeout(this.endTimeout);
    this.endTimeout = window.setTimeout(() => this.stop(), maxDurationMs);

    this.ws = new WebSocket(url);
    this.ws.binaryType = "arraybuffer";
    this.ws.onopen = () => {
      try {
        this.ws?.send("PING");
      } catch {}
    };
    this.ws.onmessage = (evt) => {
      if (typeof evt.data === "string") return;
      const int16 = new Int16Array(evt.data as ArrayBuffer);
      this.updateRms(int16);

      if (this.worklet) {
        // zero-copy transfer to worklet
        this.worklet.port.postMessage({ type: "push", payload: int16.buffer }, [
          int16.buffer,
        ]);
      } else {
        this.queue.push(this.int16ToFloat32(int16));
      }
    };
    this.ws.onclose = () => this.stop();
    this.ws.onerror = () => this.stop();
  }

  stop() {
    if (this.closed) return;
    this.closed = true;

    try {
      this.ws?.close();
    } catch {}
    this.ws = null;

    try {
      this.worklet?.disconnect();
    } catch {}
    this.worklet = null;

    try {
      this.scriptNode?.disconnect();
    } catch {}
    this.scriptNode = null;

    if (this.ctx) {
      // let tail ring-out a touch
      const ctx = this.ctx;
      this.ctx = null;
      setTimeout(() => ctx.close(), 120);
    }

    if (this.endTimeout) {
      window.clearTimeout(this.endTimeout);
      this.endTimeout = null;
    }

    if (this.onRms) this.onRms(0);
    this.queue = [];

    if (this.onEnd) this.onEnd();
  }
}

/** ---------------------------------- Accent Orbs ---------------------------------- */
const AccentOrb: React.FC<{
  x: string;
  y: string;
  size: number;
  hue: string;
  volume: number;
}> = ({ x, y, size, hue, volume }) => {
  const jitterRef = React.useRef(0.6 + Math.random() * 0.5);
  const j = jitterRef.current;
  const v = Math.min(1, volume * 3.2);
  const vNL = Math.min(1, Math.pow(v, 0.55));
  const baseOpacity = 0.08 + vNL * 0.55 * j;

  return (
    <motion.div
      className="pointer-events-none absolute rounded-full"
      style={{
        left: x,
        top: y,
        width: size,
        height: size,
        background: `radial-gradient(circle at 30% 30%, ${hue}, transparent 60%)`,
        filter: "blur(95px)",
      }}
      animate={{
        x: [0, 12 * j, -10 * j, 0],
        y: [0, -10 * j, 14 * j, 0],
        scale: 1 + vNL * 0.12,
        opacity: baseOpacity,
      }}
      transition={{ duration: 9 + 2 * j, repeat: Infinity, ease: "easeInOut" }}
    />
  );
};

/** ---------------------------------- Siri Orb ---------------------------------- */
const SiriOrb: React.FC<{ volume: number; active: boolean }> = ({
  volume,
  active,
}) => {
  const v = Math.min(1, volume * 3.2);
  const base = active ? Math.min(1, Math.pow(v, 0.55)) : 0;
  const rings = [
    {
      size: 520,
      blur: 70,
      from: "rgba(234,88,12,0.35)",
      to: "rgba(255,255,255,0.10)",
    },
    {
      size: 440,
      blur: 60,
      from: "rgba(251,146,60,0.28)",
      to: "rgba(255,255,255,0.08)",
    },
    {
      size: 360,
      blur: 52,
      from: "rgba(255,255,255,0.20)",
      to: "rgba(255,255,255,0.04)",
    },
  ];

  return (
    <div className="relative w-[30rem] h-[30rem] flex items-center justify-center pointer-events-none">
      {rings.map((r, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full"
          style={{
            width: r.size,
            height: r.size,
            background: `radial-gradient(circle at 40% 40%, ${r.from}, ${r.to} 70%)`,
            filter: `blur(${r.blur}px)`,
          }}
          animate={{
            scale: active ? 1 + base * (0.5 - i * 0.1) : 1,
            rotate: active ? (i % 2 ? 360 : -360) : 0,
          }}
          transition={{
            duration: 10 - i * 2,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
      <motion.div
        className="absolute rounded-full bg-orange-500/85 border border-white/10 shadow-[0_0_110px_rgba(234,88,12,0.38)]"
        style={{ width: 190, height: 190 }}
        animate={{ scale: active ? 1 + base * 0.3 : 1 }}
        transition={{ type: "spring", stiffness: 180, damping: 24 }}
      />
      <motion.div
        className="absolute rounded-full border border-white/30"
        style={{ width: 260, height: 260 }}
        animate={{
          scale: active ? [1, 1.28 + base * 0.28, 1] : 1,
          opacity: active ? [0.7, 0.2, 0.7] : 0.22,
        }}
        transition={{ duration: 1.8, repeat: Infinity }}
      />
    </div>
  );
};

/** ---------------------------------- Central Button ---------------------------------- */
const CenterButton: React.FC<{
  state: MicState;
  side: Side;
  onClick: () => void;
  disabled?: boolean;
}> = ({ state, side, onClick, disabled }) => {
  const isRec = state === "RECORDING";
  const isSpeak = state === "WAITING_STREAM" || state === "PLAYING";
  const label = isRec
    ? "Stop"
    : isSpeak
      ? state === "PLAYING"
        ? "Playing…"
        : "Processing…"
      : "Start";
  const color = isRec
    ? "bg-orange-600 hover:bg-orange-500"
    : isSpeak
      ? "bg-zinc-800"
      : "bg-orange-500 hover:bg-orange-400";
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      disabled={disabled}
      onClick={onClick}
      className={`rounded-full px-8 py-5 text-lg font-extrabold tracking-wide shadow-xl transition ${color} disabled:opacity-50`}
      title={label}
    >
      <div className="flex items-center gap-3">
        {isSpeak ? (
          <Volume2 className="w-7 h-7" />
        ) : (
          <Mic className="w-7 h-7" />
        )}
        {label}
        <span className="text-xs opacity-70 ml-2">
          {side === "A" ? "Left" : "Right"}
        </span>
      </div>
    </motion.button>
  );
};

/** ---------------------------------- Side Panel ---------------------------------- */
const SidePanel: React.FC<{
  title: string;
  lang: string;
  setLang: (v: string) => void;
  active: boolean;
}> = ({ title, lang, setLang, active }) => {
  return (
    <div
      className={`rounded-2xl p-6 border ${active ? "border-orange-500/60" : "border-white/10"} bg-white/5 backdrop-blur-sm shadow-xl`}
      style={{ minWidth: 320 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-extrabold tracking-wide">{title}</h2>
        <span
          className={`text-xs px-2 py-1 rounded ${active ? "bg-orange-600/30 text-orange-200" : "bg-zinc-700 text-zinc-200"}`}
        >
          {active ? "Your turn" : "Waiting"}
        </span>
      </div>
      <label className="block text-sm mb-1 opacity-80 font-semibold">
        Language
      </label>
      <select
        className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 outline-none focus:ring-2 focus:ring-orange-500"
        value={lang}
        onChange={(e) => setLang(e.target.value)}
      >
        {Object.entries(LANG_MAP).map(([code, name]) => (
          <option key={code} value={code}>
            {name} ({code})
          </option>
        ))}
      </select>
      <div className="mt-4 text-xs opacity-70 space-y-1">
        <p>
          <span className="font-semibold">From</span> uses this panel’s
          language.
        </p>
        <p>
          <span className="font-semibold">To</span> uses the opposite panel’s
          language.
        </p>
      </div>
    </div>
  );
};

/** ---------------------------------- Page ---------------------------------- */
export const TranslationPage: React.FC = () => {
  const [langA, setLangA] = useState<string>("en");
  const [langB, setLangB] = useState<string>("es");
  const [currentSide, setCurrentSide] = useState<Side>("A");
  const [micState, setMicState] = useState<MicState>("INACTIVE");
  const [volume, setVolume] = useState<number>(0);

  const recorderRef = useRef<MicRecorder | null>(null);
  if (!recorderRef.current) recorderRef.current = new MicRecorder();

  // Player for WS stream
  const playerRef = useRef<AudioStreamPlayer | null>(null);
  if (!playerRef.current) playerRef.current = new AudioStreamPlayer(16000);

  const sameLang = langA === langB;
  const WS_URL = "ws://localhost:8080/audio/stream?streamId=main";

  // ---- central interaction loop ----
  const startRec = async () => {
    await recorderRef.current!.start((lvl) => setVolume(lvl));
    setMicState("RECORDING");
  };

  const stopRec = async () => {
    setMicState("WAITING_STREAM");
    const wav = await recorderRef.current!.stop();
    setVolume(0);

    // Send to backend (placeholder log)
    await onUtteranceFinished(currentSide, wav, langA, langB);

    // Play from WebSocket stream instead of sine
    setMicState("PLAYING");
    playerRef.current!.playFromWebSocket(
      WS_URL,
      (rms) => setVolume(rms), // drive visuals during playback
      () => {
        // when stream finishes or times out
        setVolume(0);
        setMicState("INACTIVE");
        setCurrentSide((s) => (s === "A" ? "B" : "A"));
      },
      20000 // optional: 20s safety cap
    );
  };

  const handleCenterClick = async () => {
    if (sameLang) return;
    if (micState === "INACTIVE") await startRec();
    else if (micState === "RECORDING") await stopRec();
  };

  // Utterance handler: build payload {from, to, audio}
  const onUtteranceFinished = async (
    side: Side,
    audioBlob: Blob,
    lA: string,
    lB: string
  ) => {
    const from = side === "A" ? lA : lB;
    const to = side === "A" ? lB : lA;
    const payload = {
      from,
      to,
      audioBytes: await audioBlob
        .arrayBuffer()
        .then((b) => (b as ArrayBuffer).byteLength),
      mime: audioBlob.type,
      note: "Pretend this was POSTed to /translate",
    };
    console.log("✅ Sent to backend:", payload);
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      try {
        playerRef.current?.stop();
      } catch {}
    };
  }, []);

  const ctxValue = useMemo<TranslationCtx>(
    () => ({
      langA,
      setLangA,
      langB,
      setLangB,
      currentSide,
      setCurrentSide,
      micState,
      setMicState,
      volume,
      setVolume,
    }),
    [langA, langB, currentSide, micState, volume]
  );

  return (
    <Ctx.Provider value={ctxValue}>
      <div className="relative min-h-svh overflow-hidden bg-black text-white">
        {/* Ambient backdrop: accent orbs tied to volume (mic or playback) */}
        <AccentOrb
          x="-8%"
          y="-10%"
          size={760}
          hue="rgba(234,88,12,0.65)"
          volume={volume}
        />
        <AccentOrb
          x="72%"
          y="-12%"
          size={700}
          hue="rgba(255,255,255,0.60)"
          volume={volume}
        />
        <AccentOrb
          x="-12%"
          y="68%"
          size={760}
          hue="rgba(251,146,60,0.55)"
          volume={volume}
        />
        <AccentOrb
          x="70%"
          y="76%"
          size={700}
          hue="rgba(255,255,255,0.45)"
          volume={volume}
        />

        {/* Top bar */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <Link to="/" className="text-xl font-semibold hover:opacity-80">
            ← Back
          </Link>
          <div className="text-sm">
            <span className="uppercase tracking-widest text-zinc-400">
              Turn
            </span>{" "}
            <span className="font-bold">
              {currentSide === "A" ? "Left (A)" : "Right (B)"}
            </span>
          </div>
        </div>

        {/* Centered Layout */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 pb-20">
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] items-center gap-10 lg:gap-16 place-items-center">
            {/* Left */}
            <SidePanel
              title="Speaker A"
              lang={langA}
              setLang={setLangA}
              active={currentSide === "A"}
            />

            {/* Center controls bigger */}
            <div className="flex flex-col items-center text-center">
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
                Real-time <span className="text-orange-400">Conversation</span>{" "}
                Translator
              </h1>
              <p className="mt-3 text-base md:text-lg text-zinc-300 max-w-xl">
                Tap once to speak. Tap again to translate & stream audio back.
                Then it’s the other side’s turn.
              </p>

              {/* Orb */}
              <div className="relative mt-8 z-0">
                <SiriOrb volume={volume} active={micState === "RECORDING"} />
                {langA === langB && (
                  <div className="absolute inset-0 rounded-2xl bg-black/60 backdrop-blur-[2px] flex items-center justify-center">
                    <div className="px-4 py-2 rounded-xl bg-zinc-900/80 border border-white/10 text-sm md:text-base font-semibold">
                      Choose different languages to start
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 relative z-20">
                <CenterButton
                  state={micState}
                  side={currentSide}
                  onClick={handleCenterClick}
                  disabled={langA === langB || micState === "WAITING_STREAM"}
                />
              </div>

              <div className="mt-3 text-sm opacity-85 font-semibold">
                {micState === "RECORDING" ? (
                  <span className="text-orange-300">
                    Listening… press to stop
                  </span>
                ) : micState === "WAITING_STREAM" ? (
                  <span className="text-orange-200">
                    Processing & waiting for stream…
                  </span>
                ) : micState === "PLAYING" ? (
                  <span className="text-white">Playing translation…</span>
                ) : (
                  <span>
                    Press to speak —{" "}
                    <span className="text-white">
                      {currentSide === "A" ? "Left (A)" : "Right (B)"}
                    </span>
                  </span>
                )}
              </div>
            </div>

            {/* Right */}
            <SidePanel
              title="Speaker B"
              lang={langB}
              setLang={setLangB}
              active={currentSide === "B"}
            />
          </div>
        </div>
      </div>
    </Ctx.Provider>
  );
};
