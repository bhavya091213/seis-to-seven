## 🧠 Inspiration

Inspired by Apple’s new AirPods translation feature, we wanted to push the idea further — making live translation more **human-to-human, accessible, and instant**. “Seis to Seven” plays on the “six to seven” meme — bridging the gap between languages just like moving one number closer to understanding.

At its core, this project is about **social good** — breaking down communication barriers that isolate people across healthcare, education, and global collaboration. Everyone deserves to be heard and understood, no matter what language they speak.

---

## 💬 What It Does

**Seis to Seven** enables natural, **two-way speech translation** in real time. From doctor–patient consultations to travelers asking for directions, it empowers seamless conversations across languages while preserving tone and emotion.

Our system auto-detects the spoken language, translates it using **Gemini**, and reproduces it with **ElevenLabs voice cloning** — so each speaker hears the other in their own language, **in the same voice**, creating true connection rather than machine output.

---

## 🧩 How We Built It

We engineered a **cross-platform, low-latency translation pipeline** combining:

* **Spring Boot** backend for stable networking and stream orchestration.
* **Python bridge service** for ASR → Gemini Translation → ElevenLabs TTS.
* **WebSockets** for real-time streaming and bi-directional data flow.
* **Audio chunking** for phrase-by-phrase inference, reducing delay.
* **Voice caching** to store cloned voices once and reuse them for faster response.

Every decision was designed to **reduce latency and humanize machine speech**, making real-time translation not only possible but natural and inclusive.

---

## ⚙️ Challenges We Ran Into

* Synchronizing **audio chunks** without cutting words mid-sentence.
* Managing **latency bottlenecks** between multiple APIs and frameworks.
* Persisting cloned voices securely to save time and storage.
* Achieving consistent **stream quality** across different browsers and networks.

---

## 🏆 Accomplishments That We’re Proud Of

* Reached **sub-second translation feedback** for real-time dialogue.
* Created a scalable, modular architecture ready for web and mobile.
* Unified **Gemini + ElevenLabs** in a single low-latency pipeline.
* Built something that could **genuinely improve accessibility** for multilingual communication worldwide.

---

## 📚 What We Learned

* The art of balancing **speed, accuracy, and humanity** in machine translation.
* Designing for **stream synchronization** and concurrency between Java and Python.
* How emotional realism in TTS can change how users feel when using translation tools.

---

## 🚀 What’s Next for *Seis to Seven*

* Expand to **mobile and wearable devices** for real-world translation use.
* Integrate **emotion transfer** and contextual understanding for empathy in speech.
* Enable **multi-party translation** for classrooms, meetings, and global teams.
* Partner with NGOs and accessibility groups to bring real-time translation to **underserved communities**.
