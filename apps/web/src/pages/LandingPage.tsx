import { Link } from "react-router-dom";
import { useRef } from "react";

export const LandingPage = () => {
  return (
    <div className="relative min-h-svh overflow-hidden bg-black text-white">
      {/* Background accents */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(600px 300px at 20% 10%, rgba(234,88,12,0.18), transparent 60%), radial-gradient(700px 350px at 80% 20%, rgba(234,88,12,0.15), transparent 60%), radial-gradient(800px 400px at 50% 90%, rgba(255,255,255,0.06), transparent 60%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
          backgroundSize: "28px 28px, 28px 28px",
          maskImage:
            "radial-gradient(900px 600px at 50% 20%, black 55%, transparent 80%)",
        }}
      />

      <main className="relative pt-[5%] z-10 mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* HERO */}
        <section className="flex min-h-svh flex-col items-center justify-center text-center">
          <div className="mx-auto max-w-4xl">
            <h1 className="text-balance text-4xl font-extrabold leading-tight sm:text-6xl md:text-7xl">
              Break the language barrier.{" "}
              <span className="bg-gradient-to-r from-orange-400 via-orange-500 to-amber-400 bg-clip-text text-transparent">
                In real time.
              </span>
            </h1>

            <p className="mx-auto mt-5 max-w-2xl text-pretty text-base text-white/70 sm:text-lg">
              Technology is everywhere, but language still blocks critical conversations—from
              doctors and patients to everyday chats. We’re expanding on Apple’s new AirPods
              translation idea with a fully cross-platform, low-latency pipeline.
            </p>

            <div className="mt-8 flex items-center justify-center">
              <Link
                to="/translate"
                className="btn-aurora group inline-flex items-center gap-2 rounded-xl bg-orange-500 px-6 py-3 text-base font-semibold text-black shadow-[0_10px_30px_-10px_rgba(234,88,12,0.8)] transition hover:-translate-y-0.5 hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/70 active:translate-y-0"
              >
                Start Translating
                <svg
                  className="h-5 w-5 transition-transform group-hover:translate-x-0.5"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path d="M13.172 12 8.222 7.05l1.414-1.414L16 12l-6.364 6.364-1.414-1.414z" />
                </svg>
              </Link>
            </div>
          </div>

          {/* FEATURE CARDS (content rewritten) */}
          <div className="mt-12 w-full max-w-5xl">
            <div className="relative rounded-2xl border border-white/10 bg-white/5 p-1 backdrop-blur">
              <div
                className="absolute -inset-1 rounded-2xl opacity-30 blur-2xl"
                style={{
                  background:
                    "conic-gradient(from 180deg at 50% 50%, rgba(234,88,12,0.25), transparent 40%, rgba(255,255,255,0.1), transparent 70%, rgba(234,88,12,0.25))",
                }}
                aria-hidden
              />
              <div className="relative rounded-xl bg-black/60 p-6 sm:p-8">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <ShowcaseCard
                    title="1) The Problem We Solve"
                    desc="Even with modern devices, the language gap remains. We focus on live, two-way conversations—clinics, travel, support—where clarity matters most."
                    icon={<ProblemIcon />}
                  />
                  <ShowcaseCard
                    title="2) Gemini-Powered Translation"
                    desc="Leverages Gemini for fast, dialog-tuned translation across many languages—built for back-and-forth speech, not just paragraphs."
                    icon={<TranslateIcon />}
                  />
                  <ShowcaseCard
                    title="3) ElevenLabs Detection & TTS"
                    desc="Auto-detects languages and outputs natural speech via ElevenLabs—capable of custom voice profiles that can mimic your voice."
                    icon={<VoiceIcon />}
                  />
                  <ShowcaseCard
                    title="4) Ultra-Low Latency"
                    desc="Streaming audio, chunked inference, and rapid TTS—engineered to keep delays minimal so conversations feel natural."
                    icon={<SpeedIcon />}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* TEAM */}
          <div className="mx-auto mt-16 w-full max-w-6xl">
            <h2 className="text-center text-2xl font-semibold sm:text-3xl">
              The Team
            </h2>

            <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <TeamMember
                name="Simir Vempali"
                role="Gemini engineering, prompting & integration"
                imgSrc="/team/simir.jpg"
                linkedIn="https://www.linkedin.com/in/simir-vempali/"
              />
              <TeamMember
                name="Aaryan Bhardwaj"
                role="ElevenLabs STT integration & language detection"
                imgSrc="/team/aaryan.jpg"
                linkedIn="https://www.linkedin.com/in/aaryan-bhardwaj1/"
              />
              <TeamMember
                name="Bhavya P."
                role="Full-stack & Spring Boot service integration"
                imgSrc="/team/bhavya.jpg"
                linkedIn="https://linkedin.com/in/bhavyap12"
              />
              <TeamMember
                name="Mihir Chanduka"
                role="TTS with ElevenLabs, custom voice profiles, final output"
                imgSrc="/team/mihir.jpg"
                linkedIn="https://www.linkedin.com/in/mihirchanduka/"
              />
            </div>
          </div>

          {/* Footer microcopy (simple, neutral) */}
          <div className="mt-12 pb-12 text-center text-xs text-white/40">
            © {new Date().getFullYear()} All rights reserved.
          </div>
        </section>
      </main>
    </div>
  );
};

/* ---- Feature Card with aura + mouse-follow ---- */
const ShowcaseCard = ({
  title,
  desc,
  icon,
}: {
  title: string;
  desc: string;
  icon: React.ReactNode;
}) => {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * 100;
    const y = ((e.clientY - r.top) / r.height) * 100;
    el.style.setProperty("--x", `${x}%`);
    el.style.setProperty("--y", `${y}%`);
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      className="aura group relative overflow-hidden rounded-xl border border-white/10 bg-white/[0.04] p-5 transition hover:bg-white/[0.06]"
    >
      <div className="flex items-start gap-4">
        <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/15 ring-1 ring-inset ring-orange-500/30">
          <div className="text-orange-400">{icon}</div>
        </div>
        <div>
          <h3 className="text-base font-semibold">{title}</h3>
          <p className="mt-1 text-sm text-white/70">{desc}</p>
        </div>
      </div>
    </div>
  );
};

/* ---- Team Card ---- */
const TeamMember = ({
  name,
  role,
  imgSrc,
  linkedIn,
}: {
  name: string;
  role: string;
  imgSrc?: string;
  linkedIn: string;
}) => {
  return (
    <div className="aura relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] p-6 text-center transition hover:bg-white/[0.06]">
      <div className="mx-auto h-24 w-24 overflow-hidden rounded-full ring-1 ring-white/10">
        {/* If no image exists yet, place a gradient initial */}
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={name}
            className="h-full w-full object-cover"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = "none";
              const fallback = e.currentTarget.nextElementSibling as HTMLDivElement | null;
              if (fallback) fallback.style.display = "grid";
            }}
          />
        ) : null}
        <div
          className="hidden h-full w-full place-items-center bg-gradient-to-br from-orange-600/70 to-amber-400/60 text-black"
          aria-hidden
        >
          <span className="text-2xl font-bold">
            {name
              .split(" ")
              .map((n) => n[0])
              .slice(0, 2)
              .join("")}
          </span>
        </div>
      </div>

      <h3 className="mt-4 text-base font-semibold">{name}</h3>
      <p className="mt-1 text-sm text-white/70">{role}</p>

      <div className="mt-4">
        <a
          href={linkedIn}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-aurora inline-flex items-center gap-2 rounded-lg bg-orange-500 px-3 py-2 text-sm font-semibold text-black transition hover:-translate-y-0.5 hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/70"
        >
          <LinkedInIcon />
          LinkedIn
        </a>
      </div>
    </div>
  );
};

/* ---- Inline icons ---- */
const ProblemIcon = () => (
  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor" aria-hidden="true">
    <path d="M12 2a10 10 0 1 0 10 10A10.011 10.011 0 0 0 12 2zm1 15h-2v-2h2zm0-4h-2V7h2z" />
  </svg>
);
const TranslateIcon = () => (
  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor" aria-hidden="true">
    <path d="M4 4h9v2H6v3h5.5a8.5 8.5 0 0 1-2.3 4.5l2.3 2.3-1.4 1.4-2.6-2.6A10.3 10.3 0 0 1 5 9H4zM15 11h5l-4 9h-2l1.1-2.6h-3.2L11 20H9z" />
  </svg>
);
const VoiceIcon = () => (
  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor" aria-hidden="true">
    <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3zm-7-3h2a5 5 0 0 0 10 0h2a7 7 0 0 1-6 6.92V20h3v2H8v-2h3v-2.08A7 7 0 0 1 5 11z" />
  </svg>
);
const SpeedIcon = () => (
  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor" aria-hidden="true">
    <path d="M21 12a9 9 0 1 0-6.5 8.6l2.1-7.7 2.9-2.9-3.7 1.1-7.7 2.1A7 7 0 1 1 19 12h2z" />
  </svg>
);
const LinkedInIcon = () => (
  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden="true">
    <path d="M4.98 3.5C4.98 4.88 3.86 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM0 8h5v16H0zM8 8h4.7v2.2h.1c.7-1.2 2.5-2.4 5.1-2.4C21.8 7.8 24 10 24 14.1V24h-5v-8.7c0-2.1-.8-3.6-2.7-3.6-1.5 0-2.4 1-2.8 2-.1.3-.1.8-.1 1.3V24H8z" />
  </svg>
);