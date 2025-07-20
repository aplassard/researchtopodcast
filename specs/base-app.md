1  Project Overview

Concern	Choice / Rationale
Primary Goal	Transform an academic or technical PDF/Markdown/HTML document into a 5‑minute conversational podcast.
Core Flow	(1) Generate podcast script with LLM(s) → (2) Synthesize audio with TTS → (3) Wrap both into CLI & API → (4) Serve via React UI.
Target Use	Researchers, educators, or newsrooms who want “audio summaries on demand.”
Build Style	Modular, async‑first Python 3.11+, FastAPI for services, React + Vite for client, Docker for reproducibility.
Default package manager should be uv
Default Cloud	Everything runs locally by default, flips to cloud if OPENAI_API_KEY and/or OPENROUTER_API_KEY & OPENROUTER_BASE_URL are present.
Licensing	Apache‑2.0 (all dependencies compatible).


⸻

2  Phased Road‑map

Each phase should complete red‑green‑refactor (tests first, implementation, tidy) before merging to main.

Phase	Deliverables	Key Modules	Milestones
0. Bootstrap	Poetry/Docker project skeleton, CI (GitHub Actions)	—	• docker compose up prints “Hello Audio!”
1. LLM Integration	llm_client/ package with pluggable back‑ends	openrouter.py, openai.py, base.py, models.py	• Unit tests hit mocked endpoints.• Supports three script modes (Solo, Single‑LLM Multi‑Speaker, Multi‑Agent Multi‑Speaker).
2. Script Generation	script_engine/ package, role presets, prompt templates	planner.py, persona.py, template/	• Generates .podcast.yaml (see §4).
3. TTS Integration	speech/ package for Google TTS (Gemini voices)	google.py, base.py	• Mockable synthesis returning WAV/MP3 bytes.
4. CLI	bin/research2podcast entrypoint	cli.py (Typer)	• research2podcast generate --input doc.pdf outputs output/episode01.mp3.
5. FastAPI Service	api/ package, OpenAPI 3 schema	routers/podcast.py, dependencies.py	• POST /podcast mirrors CLI options.
6. React Dashboard	Parameter‑rich UI, upload + progress bar	vite scaffold, api.ts client	• Live demo over Docker Compose.
7. End‑to‑End Test	Integration test producing 5‑min episode from sample doc	tests/e2e/test_episode.py	• Artifact saved as CI workflow summary.
8. Packaging / Release	Versioned Docker image, Poetry publish	—	• docker pull org/research2podcast:1.0.0 works.


⸻

3  Module & Package Layout

reseachtopodcast/
├── llm_client/
│   ├── __init__.py
│   ├── base.py           # common interface: chat(), name, cost()
│   ├── openrouter.py      # default
│   ├── openai.py          # fallback
│   └── models.py          # enum of supported model IDs
├── script_engine/
│   ├── __init__.py
│   ├── persona.py         # Host persona dataclass
│   ├── planner.py         # chooses strategy & prompts
│   ├── templates/         # Jinja2 prompt & role files
│   └── formatter.py       # renders to .podcast.yaml
├── speech/
│   ├── __init__.py
│   ├── base.py            # synthesize(text, voice) → audio bytes
│   └── google.py          # Google Gemini TTS
├── cli/
│   └── cli.py             # Typer commands (generate, play, list‑voices)
├── api/
│   ├── main.py            # FastAPI app
│   ├── dependencies.py
│   └── routers/
│       └── podcast.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── frontend/              # React (Vite) app
│   └── ...
└── pyproject.toml

Key Interfaces (simplified)

# llm_client.base
class LLMClient(Protocol):
    name: str
    async def chat(self, messages: list[ChatMessage], **kw) -> str: ...

# speech.base
class SpeechEngine(Protocol):
    async def synthesize(self, script: Script, **kw) -> Path: ...


⸻

4  Script File Format (*.podcast.yaml)

meta:
  title: "Episode 1 – Stem Cells in 2025"
  duration_sec: 300
  created: 2025-07-20T12:34:56Z
hosts:
  - name: "Dr. Ada"
    persona: "Expert host—friendly, concise."
    voice_id: "en-US-Standard-A"
  - name: "Ben"
    persona: "Curious co-host—asks clarifying questions."
    voice_id: "en-US-Standard-B"
segments:
  - speaker: "Dr. Ada"
    text: |
      Welcome to Research‑to‑Podcast...
  - speaker: "Ben"
    text: |
      Thanks, Ada! Let's dive in.

Reasons:
	•	Keeps TTS parameters adjacent to dialogue.
	•	YAML is easy for humans, stable for parsers (use ruamel.yaml for round‑trip fidelity).

⸻

5  Default Model & Persona Catalogue

Mode	LLM(s)	Host Names	Intended Feel
Solo	openrouter/gpt-4o-mini	“Alex”	Single‑narrator, news‑reader style.
Single‑LLM Multi‑Speaker	Same model, system prompt orchestrates voices	“Dr. Ada” (expert) & “Ben” (layperson)	Friendly banter; cheap & fast.
Multi‑Agent Multi‑Speaker	openrouter/gpt-4o-mini orchestrator + openrouter/deepseek-coder researcher agent	“Dr. Ada”, “Ben”, “Chloe” (fact‑checker)	Richer reasoning; higher latency.

The orchestrator must own summarization; agents may do sub‑tasks (fact extraction, Q&A).

⸻

6  Testing Strategy

Layer	Tooling	Coverage Goals
Unit	pytest, pytest-asyncio, pytest-mock	> 90 % of pure functions, mock network I/O.
Contract	schemathesis against FastAPI OpenAPI spec	Each endpoint accepts/returns expected shapes.
Integration	Spin up Docker Compose (LLM mocked)	Validate CLI ↔ TTS ↔ storage.
E2E	Real LLM (rate‑limited), real Google TTS (short quota)	CI night‑run only; output duration ±5 %.
Frontend	vitest + @testing-library/react	Interactions emit correct fetch calls.

CI matrix: Linux/macOS, Python 3.11 and 3.12.

⸻

7  Environment & Configuration

Variable	Purpose	Default/Fallback
OPENROUTER_API_KEY	Token for OpenRouter models	required unless OpenAI present
OPENROUTER_BASE_URL	Custom proxy endpoint	https://openrouter.ai/api/v1
OPENAI_API_KEY	Used if above absent	—
GOOGLE_TTS_KEY	Google Gemini TTS	Local mock if missing
PODGEN_MAX_TOKENS	Safety cap for each LLM call	4096
PODGEN_TEMP_DIR	Where WAVs/YAML land	./output

All configs flow through one settings.py (Pydantic v2 SettingsConfigDict).

⸻

8  Command‑Line UX (Typer)

research2podcast generate \
  --input doc.pdf \
  --mode multi-agent \
  --duration 300 \
  --out ./output \
  --openrouter-api-key $OPENROUTER_API_KEY

Other sub‑commands:
	•	research2podcast list-voices – prints Google voices & sample URLs
	•	research2podcast play episode01.mp3 – convenience playback (uses pydub)
	•	research2podcast serve – boots the FastAPI + React stack (alias to docker compose up)

All options are mirrored in REST query params and Web UI form inputs.

⸻

9  FastAPI Endpoints (stable v1)

Method	Path	Body / Query	Response
POST	/v1/podcast	JSON: `{input_url	file, mode, duration, voices?}`
GET	/v1/podcast/{id}	—	Poll status. When state=="ready": returns {download_url}
GET	/v1/voices	—	List of supported TTS voices with sample URL.

Async background tasks stream progress events over sse channel /v1/events/{id} for live UI updates.

⸻

10  React Dashboard (Vite, TypeScript)
	•	State: Zustand store; episodes persisted to indexedDB.
	•	Components: DocUploader → ParameterForm → ProgressBar → AudioPlayer.
	•	API Client: api.ts wraps fetch with retry/back‑off.
	•	Styling: Tailwind CSS, accessible color palette (WCAG AA).
	•	Deployment: npm run build && vite preview --port 5173 in Dockerfile.

⸻

11  Key Design Decisions
	1.	Async everywhere: bulky network calls (LLM, TTS, file I/O) run under asyncio, enabling future concurrency (e.g., segment‑level synthesis).
	2.	Pluggable providers: new LLM or TTS requires one subclass and a registry entry – no invasive changes.
	3.	YAML over JSON: easier for humans to post‑edit scripts before synthesis; preserved comments.
	4.	Cost & token accounting: llm_client tracks cumulative usage; surfaces in CLI summary.
	5.	Streaming friendly: both LLM chat and Google TTS support partial responses – design already uses async generators, though first release can buffer entire outputs.
	6.	Five‑minute guarantee: script planner auto‑estimates speech rate (~150 wpm) and adjusts segment lengths to hit ±3 % duration target.

⸻

12  Extensibility Ideas (post‑MVP)
	•	Speaker diarization – split multi‑speaker audio into tracks for post‑mixing.
	•	Music bed – optional intro/outro with CC‑0 clips via pydub.
	•	More TTS engines – ElevenLabs, Azure, Amazon Polly.
	•	Document fetchers – ArXiv, PubMed, or website URL with readability extraction.
	•	Analytics – store episode stats + cost in SQLite, expose Grafana dashboard.

⸻

13  Acceptance Criteria
	1.	Running research2podcast generate --input sample.pdf --duration 300 on a clean clone (with valid keys) produces episode01.mp3 of length 297–303 seconds.
	2.	All non‑CI network calls may be disabled behind --mock flag and still pass all tests.
	3.	Docker Compose (frontend, api, reverse‑proxy) serves the React UI at http://localhost:8080, and generating an episode through the UI produces identical output to the CLI.
	4.	Repository passes ruff, black, isort, and mypy --strict.
	5.	CI finishes in < 15 min with caches and parallel jobs.

