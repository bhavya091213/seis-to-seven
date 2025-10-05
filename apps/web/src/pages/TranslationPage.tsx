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

/** ---------------------------------- PCM Helpers (WS player) ---------------------------------- */
function pcm16ToFloat32(ab: ArrayBuffer): Float32Array {
  const src = new Int16Array(ab);
  const dst = new Float32Array(src.length);
  for (let i = 0; i < src.length; i++) dst[i] = src[i] / 32768;
  return dst;
}
function rmsFloat32(a: Float32Array): number {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * a[i];
  return Math.sqrt(s / Math.max(1, a.length));
}

/** ---------------------------------- WebSocket PCM Player (16kHz mono) ---------------------------------- */
class PCMWebSocketPlayer {
  private ws: WebSocket | null = null;
  private audioCtx: AudioContext;
  private gain: GainNode;
  private queue: Float32Array[] = [];
  private isPlaying = false;
  private onLevel?: (level: number) => void;

  constructor(audioCtx: AudioContext, onLevel?: (level: number) => void) {
    this.audioCtx = audioCtx;
    this.gain = this.audioCtx.createGain();
    this.gain.connect(this.audioCtx.destination);
    this.onLevel = onLevel;
  }

  connect(url: string) {
    this.disconnect();
    this.ws = new WebSocket(url);
    this.ws.binaryType = "arraybuffer";

    this.ws.onopen = () => {
      this.audioCtx.resume();
    };
    this.ws.onmessage = (ev) => {
      const floats = pcm16ToFloat32(ev.data as ArrayBuffer);
      if (this.onLevel) {
        const v = Math.min(1, Math.pow(rmsFloat32(floats), 0.65) * 1.35);
        this.onLevel(v);
      }
      this.queue.push(floats);
      this.pump();
    };
    this.ws.onerror = (e) => console.error("WS error", e);
    this.ws.onclose = () => {
      this.ws = null;
    };
  }

  disconnect() {
    if (this.ws) {
      try {
        this.ws.close();
      } catch {}
      this.ws = null;
    }
    this.queue = [];
  }

  private async pump() {
    if (this.isPlaying) return;
    this.isPlaying = true;
    while (this.queue.length) {
      const floats = this.queue.shift()!;
      const buf = this.audioCtx.createBuffer(1, floats.length, 16000);
      buf.getChannelData(0).set(floats);
      const src = this.audioCtx.createBufferSource();
      src.buffer = buf;
      src.connect(this.gain);
      const done = new Promise<void>((res) => (src.onended = () => res()));
      src.start();
      await done;
    }
    this.isPlaying = false;
  }
}

/** ---------------------------------- Mic Recorder (WAV 16kHz 16-bit) ---------------------------------- */
class MicRecorder {
  private stream: MediaStream | null = null;
  private audioCtx: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private worklet: AudioWorkletNode | null = null;
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

    // AudioWorklet (no deprecated ScriptProcessor)
    const workletUrl = URL.createObjectURL(
      new Blob(
        [
          `class RecorderProcessor extends AudioWorkletProcessor {
             process(inputs){
               const input = inputs[0];
               if (input && input[0]){
                 const ch = input[0];
                 const buf = new Float32Array(ch.length);
                 buf.set(ch);
                 this.port.postMessage(buf, [buf.buffer]);
               }
               return true;
             }
           }
           registerProcessor('recorder-processor', RecorderProcessor);`,
        ],
        { type: "application/javascript" }
      )
    );
    await (this.audioCtx as any).audioWorklet.addModule(workletUrl);
    URL.revokeObjectURL(workletUrl);

    this.worklet = new AudioWorkletNode(
      this.audioCtx as any,
      "recorder-processor"
    );
    this.worklet.port.onmessage = (e: MessageEvent<Float32Array>) => {
      const block = e.data;
      this.chunks.push(block);
      if (this.onLevel) {
        const v = Math.min(1, Math.pow(this.rms(block), 0.65) * 1.35);
        this.onLevel(v);
      }
    };
    (this.source as unknown as AudioNode).connect(
      this.worklet as unknown as AudioNode
    );
  }

  async stop(): Promise<Blob> {
    try {
      this.source?.disconnect?.();
      this.worklet?.disconnect?.();
      this.worklet?.port?.close?.();
      await this.audioCtx?.close?.();
      this.stream?.getTracks().forEach((t) => t.stop());
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

/** ---------------------------------- WebAudio decode-and-play (REST) ---------------------------------- */
async function decodeAndPlayWithWebAudio(
  ctx: AudioContext,
  arrayBuffer: ArrayBuffer,
  onLevel?: (v: number) => void
): Promise<void> {
  // NEW: guard empty and resume if needed
  if (!arrayBuffer || arrayBuffer.byteLength === 0) {
    throw new Error("Empty audio buffer (0 bytes) from server");
  }
  if (ctx.state === "suspended") {
    try {
      await ctx.resume();
    } catch {}
  }

  const analyser = ctx.createAnalyser();
  analyser.fftSize = 1024;

  let audioBuffer: AudioBuffer;
  try {
    audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
  } catch {
    throw new Error("Unable to decode audio data (bad format or truncated)");
  }

  const src = ctx.createBufferSource();
  src.buffer = audioBuffer;
  src.connect(analyser);
  analyser.connect(ctx.destination);

  let rafId: number | null = null;
  const data = new Float32Array(analyser.frequencyBinCount);
  const loop = () => {
    analyser.getFloatTimeDomainData(data);
    let s = 0;
    for (let i = 0; i < data.length; i++) s += data[i] * data[i];
    const rms = Math.sqrt(s / Math.max(1, data.length));
    const exaggerated = Math.min(1, Math.pow(rms, 0.65) * 1.35);
    onLevel?.(exaggerated);
    rafId = requestAnimationFrame(loop);
  };

  rafId = requestAnimationFrame(loop);

  const done = new Promise<void>((res) => (src.onended = () => res()));
  src.start();

  await done;

  if (rafId) cancelAnimationFrame(rafId);
  onLevel?.(0);
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
      className={`rounded-2xl p-6 border ${
        active ? "border-orange-500/60" : "border-white/10"
      } bg-white/5 backdrop-blur-sm shadow-xl`}
      style={{ minWidth: 320 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-extrabold tracking-wide">{title}</h2>
        <span
          className={`text-xs px-2 py-1 rounded ${
            active
              ? "bg-orange-600/30 text-orange-200"
              : "bg-zinc-700 text-zinc-200"
          }`}
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

/** ---------------------------------- Helpers ---------------------------------- */
async function blobToBase64(b: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onerror = () => reject(fr.error);
    fr.onload = () => {
      const result = String(fr.result || "");
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    fr.readAsDataURL(b);
  });
}

/** ---------------------------------- Page ---------------------------------- */
export const TranslationPage: React.FC = () => {
  const [langA, setLangA] = useState<string>("en");
  const [langB, setLangB] = useState<string>("es");
  const [currentSide, setCurrentSide] = useState<Side>("A");
  const [micState, setMicState] = useState<MicState>("INACTIVE");
  const [volume, setVolume] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  const recorderRef = useRef<MicRecorder | null>(null);
  if (!recorderRef.current) recorderRef.current = new MicRecorder();

  // WebAudio context for WS PCM playback (fixed 16k for timing)
  const wsAudioCtxRef = useRef<AudioContext | null>(null);
  const wsPlayerRef = useRef<PCMWebSocketPlayer | null>(null);

  // Dedicated playback context for REST decode (lets browser pick correct rate)
  const playbackCtxRef = useRef<AudioContext | null>(null);

  React.useEffect(() => {
    const ctx16k = new (window.AudioContext ||
      (window as any).webkitAudioContext)({ sampleRate: 16000 });
    wsAudioCtxRef.current = ctx16k;
    wsPlayerRef.current = new PCMWebSocketPlayer(ctx16k, (v) => setVolume(v));

    playbackCtxRef.current = new (window.AudioContext ||
      (window as any).webkitAudioContext)();

    return () => {
      wsPlayerRef.current?.disconnect();
      ctx16k.close();
      playbackCtxRef.current?.close();
    };
  }, []);

  const toggleWS = () => {
    if (!wsPlayerRef.current) return;
    if (!wsConnected) {
      const host = location.host;

      const url = `ws://${host}/audio/stream?streamId=main`;
      // setTimeout(() => wsPlayerRef.current!.connect(url), 1000000);
      wsPlayerRef.current.connect(url);
      setWsConnected(true);
    } else {
      wsPlayerRef.current.disconnect();
      setWsConnected(false);
      setVolume(0);
    }
  };

  const sameLang = langA === langB;
  const API_BASE = "http://localhost:8080"; // rely on your existing setup
  const API_URL = `${API_BASE}/api/voice/translate`;

  // ---- central interaction loop ----
  const startRec = async () => {
    setError(null);
    await recorderRef.current!.start((lvl) => setVolume(lvl));
    setMicState("RECORDING");
  };

  const stopRec = async () => {
    setMicState("WAITING_STREAM");
    const wav = await recorderRef.current!.stop(); // 16-bit 16kHz WAV
    setVolume(0);
    await onUtteranceFinished(currentSide, wav, langA, langB);
  };

  const handleCenterClick = async () => {
    if (sameLang) return;
    if (micState === "INACTIVE") await startRec();
    else if (micState === "RECORDING") await stopRec();
  };

  // Utterance handler: POST JSON {from_lang, to_lang, audio_b64} -> decode & play bytes
  const onUtteranceFinished = async (
    side: Side,
    audioBlob: Blob,
    lA: string,
    lB: string
  ) => {
    const from_lang = side === "A" ? lA : lB;
    const to_lang = side === "A" ? lB : lA;

    try {
      // 1) Convert to base64
      const audio_b64 = await blobToBase64(audioBlob);
      let name = side;
      console.log(name);

      // 2) Call Spring Boot JSON endpoint
      const resp = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "audio/wav, audio/mpeg;q=0.8",
        },
        body: JSON.stringify({ from_lang, to_lang, audio_b64, name }),
      });
      console.log("did we have an ok");

      if (!resp.ok) {
        const text = await resp.text().catch(() => "");
        throw new Error(
          `HTTP ${resp.status} ${resp.statusText}${text ? ` — ${text}` : ""}`
        );
      }

      // 3) Accumulate (handles chunked streaming) then decode and play
      let buf: ArrayBuffer;
      if (resp.body) {
        const reader = resp.body.getReader();
        const chunks: Uint8Array[] = [];
        let total = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value && value.length) {
            chunks.push(value);
            total += value.length;
          }
        }
        const out = new Uint8Array(total);
        let off = 0;
        for (const c of chunks) {
          out.set(c, off);
          off += c.length;
        }
        buf = out.buffer;
      } else {
        buf = await resp.arrayBuffer();
      }

      if (!buf || buf.byteLength === 0) {
        throw new Error("No audio received from server");
      }

      const ctx = playbackCtxRef.current!;
      setMicState("PLAYING");
      console.log("trying to decode");
      try {
        console.log(ctx);
        console.log(buf);
        await decodeAndPlayWithWebAudio(ctx, buf, (v) => setVolume(v));
      } finally {
        setVolume(0);
        setMicState("INACTIVE");
        setCurrentSide((s) => (s === "A" ? "B" : "A"));
      }
    } catch (e: any) {
      console.error(e);
      setError(e?.message || "Playback failed");
      setVolume(0);
      setMicState("INACTIVE");
    }
  };

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
        {/* Ambient backdrop: accent orbs tied to volume */}
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
        <div className="relative z-10 max-w-7xl mx-auto px-6 py-6 flex items-center justify-between gap-4">
          <Link to="/" className="text-xl font-semibold hover:opacity-80">
            ← Back
          </Link>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleWS}
              className={`px-3 py-1.5 rounded text-sm font-semibold ${
                wsConnected ? "bg-green-600" : "bg-zinc-700"
              }`}
              title="Connect to live WS stream (PCM16)"
            >
              {wsConnected ? "Live: ON" : "Live: OFF"}
            </button>
            <div className="text-sm">
              <span className="uppercase tracking-widest text-zinc-400">
                Turn
              </span>{" "}
              <span className="font-bold">
                {currentSide === "A" ? "Left (A)" : "Right (B)"}
              </span>
            </div>
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
                <SiriOrb
                  volume={volume}
                  active={micState === "RECORDING" || wsConnected}
                />
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
                  <span className="text-orange-200">Processing request…</span>
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

              {error && (
                <div className="mt-3 text-sm text-red-300 bg-red-900/30 border border-red-800/40 px-3 py-2 rounded-xl max-w-md">
                  {error}
                </div>
              )}
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
