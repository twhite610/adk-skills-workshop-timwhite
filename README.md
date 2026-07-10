# Gemini ADK Training — Lab Submissions

This repo contains work for a multi-lab Gemini Enterprise / ADK training program.

## Why this isn't all Jupyter notebooks

Lab 1 is a Jupyter notebook, since it's a single self-contained script. Labs 2
onward build ADK agents, which are inherently multi-file projects (agent
definitions, callbacks, sub-agent folders) — that structure doesn't map
cleanly onto a single notebook, so those labs are plain Python files instead,
organized to mirror ADK's own recommended project layout.

## How to inspect each lab

Each lab is preserved as a Git tag at the commit where it was completed.
`main` reflects the latest overall state; check out a tag to see that lab's
code exactly as submitted.

```bash
git clone <repo-url>
cd weather_agent
git checkout lab1-final   # Lab 1
git checkout lab2-final   # Lab 2
git checkout lab3-final   # Lab 3
git checkout main         # back to latest
```

## Environment Setup

### Requirements
- Python 3.12+ (Python 3.9 will fail — ADK's MCP features require 3.10+,
  and some dependencies emit deprecation errors on older versions)
- Homebrew (for installing Python/gcloud on macOS)
- Google Cloud CLI (`gcloud`)

### Virtual environments
- `venv/` — for Lab 1 (Jupyter notebook): `pip install notebook requests python-dotenv`
- `adk-env/` — for Labs 2–3 (ADK agents): `pip install google-adk python-dotenv requests`

### Required environment variables (`.env`, not committed)

Each lab folder expects its own `.env` file:

GOOGLE_GEO_API_KEY=<Google Geolocation/Geocoding API key>
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=<your GCP project ID>
GOOGLE_CLOUD_LOCATION=us-central1

Note: `GOOGLE_GENAI_USE_VERTEXAI` must be the literal string `true`
(not `1` or `0`) — this value is read as a string, and anything else
silently falls back to Gemini's free-tier API-key path, which has a low
daily request quota.

### Google Cloud authentication

This project authenticates via Vertex AI using Application Default
Credentials (ADC) rather than a standalone Gemini API key, due to an org
policy on the training-provided Google account that blocks direct API key
creation for the Gemini API.

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <your-project-id>
gcloud services enable aiplatform.googleapis.com
```

Note: enabling `aiplatform.googleapis.com` requires Owner or
Editor/Service Usage Admin rights on the project. If you hit a
`PERMISSION_DENIED` error, check **IAM & Admin → IAM** in Cloud Console to
confirm which account actually holds Owner on the project — it may differ
from your default `gcloud` login identity.

### Running an agent

```bash
source adk-env/bin/activate
adk run <agent_folder>      # CLI
adk web <agent_folder>      # browser dev UI
```
---

## Lab 1: Weather Notebook

**Tag:** `lab1-final`

A Jupyter notebook that fetches current weather conditions using the
National Weather Service API. Includes two functions:
- `get_current_location()` — detects location via IP-based geolocation
  (Google Geolocation API)
- `get_weather(lat, lon)` — fetches current conditions from NWS for given
  coordinates

## Lab 2: ADK Single Agent

**Tag:** `lab2-final`

An ADK agent (`weather_agent/agent.py`) that wraps the Lab 1 logic as tools
a Gemini model can call: `get_current_location`, `get_coordinates_for_city`
(Google Geocoding API), and `get_weather`.

Adds request/response logging and input validation via chained
`before_model_callback`s in a separate `callbacks.py` file, kept independent
of `agent.py` for clarity:
- `log_before_model` — logs every incoming request
- `validate_input` — blocks requests containing disallowed content,
  returning a fixed rejection message without calling the model
- `log_after_model` — logs the model's response

Authenticates via Vertex AI + Application Default Credentials rather than a
standalone API key, due to org policy on the training-provided Google
account.

## Lab 3: Multi-Agent System

**Tag:** `lab3-final`

A coordinator/sub-agent system under `lab3_multi_agent/root_agent/`,
following ADK's standard multi-agent folder layout:

- **`root_agent`** — receives all user requests, delegates to the
  appropriate sub-agent based on intent
- **`weather_agent`** (sub-agent) — same weather tools as Lab 2
- **`search_agent`** (sub-agent) — answers general questions using ADK's
  built-in `google_search` tool

Delegation uses ADK's `sub_agents` parameter (full handoff — the sub-agent
answers directly once selected, rather than the root agent orchestrating a
blended response).

## Lab 4: Multi-Agent Workflow — Answer Team

**Tag:** `lab4-final`

A multi-agent workflow under `lab4_answer_team/root_agent/` that answers a
question, then verifies and refines the answer before returning it:

- **`root_agent`** (the "Greeter") — handles greetings/small talk directly;
  delegates real questions to `answer_team`
- **`answer_team`** (`SequentialAgent`) — runs three sub-agents in order:
  - **`search_agent`** — finds data to answer the question, using ADK's
    built-in `google_search` tool
  - **`critique_agent`** — reviews the draft answer and suggests specific
    improvements
  - **`refine_agent`** — rewrites the answer based on the critique

Request/response logging (from Lab 2's `callbacks.py`) is wired into all
four agents individually, giving a per-agent debug trace of each turn.

Since ADK's CLI (`adk run`/`adk web`) loads `.env` automatically but a
plain Python script does not, `test_agent.py` calls `load_dotenv()`
explicitly before importing the agent.

### Testing

`test_agent.py` exercises the agent programmatically via ADK's
`InMemoryRunner`, sending a greeting and a real question, and printing each
event (text, tool calls, tool responses, delegation) as it happens — this
demonstrates the sub-agents firing without relying on the interactive CLI.

```bash
cd lab4_answer_team
python3 test_agent.py
```

## Lab 5: Deploying an Agent to Vertex AI Agent Engine

**Tag:** `lab5-final`

A Jupyter notebook (`lab5_agent_deployment/agent_deployment.ipynb`) that
takes the Lab 4 answer-team agent and deploys it to Vertex AI Agent Engine
(referred to in course materials as "Agent Platform"), Google Cloud's
managed runtime for ADK agents.

The notebook:
1. Initializes Vertex AI (`vertexai.init(...)`) with the project, location,
   and a GCS staging bucket
2. Redefines the `root_agent` / `answer_team` pipeline from Lab 4
   (search → critique → refine, with request/response logging)
3. Tests the agent locally via `AdkApp` and `stream_query()` before
   deploying anything
4. Deploys the agent with `agent_engines.create()`, bundling `callbacks.py`
   as an extra package since local files aren't packaged automatically
5. Tests the **deployed remote agent** with `stream_query()`, confirming
   both the greeting path (handled directly by `root_agent`) and the
   delegated research path (search → critique → refine) work identically
   to local testing

### Notable issues resolved along the way

- **Local files aren't auto-bundled:** `callbacks.py` had to be passed via
  `extra_packages=["callbacks.py"]` in `agent_engines.create()`, since only
  installed packages (not local modules) ship with the deployment by
  default.
- **Reserved environment variable name:** attempting to pass
  `GOOGLE_CLOUD_PROJECT` via `env_vars` fails with `FailedPrecondition`,
  since Agent Engine auto-injects this variable itself. Only
  `GOOGLE_GENAI_USE_VERTEXAI` needed to be set explicitly.
- **False-positive content validation:** the Lab 2 input-validation
  callback (blocking the literal word "BAD") was originally applied to
  every agent in the pipeline via `before_model_callback`. Since ordinary
  search results and critiques legitimately contain phrases like "bad
  cholesterol," this caused real answers to be blocked. Fixed by scoping
  `validate_input` to `root_agent` only (the actual user-facing input),
  while keeping `log_before_model` / `log_after_model` on every agent for
  debug visibility.

### Setup notes specific to this lab

- Requires a GCS staging bucket (created once, reused across deployments):
```bash
  gcloud storage buckets create gs://adroit-sol-501711-r0-adk-staging \
    --location=us-central1 --uniform-bucket-level-access
```
- Requires the Vertex AI SDK with deployment extras, plus Jupyter:
```bash
  pip install "google-cloud-aiplatform[adk,agent_engines]" notebook
```

## Case Study: ReadyNow! — FEMA Emergency Preparedness Agent

**Tag:** `case-study-final`

A capstone multi-agent system (`case_study_readynow/`) built for a
simulated FEMA emergency preparedness use case. Combines patterns from
Labs 1–5 into a single system, plus two new pieces: Google Maps-based
routing and a Colab Enterprise notebook environment (rather than local
Jupyter).

**Architecture:** see `case_study_readynow/readynow_architecture.svg`.

- **`root_agent`** — describes its own capabilities on request, enforces
  mission-scope refusal (declines off-topic requests via its own
  instructions rather than a keyword filter), and delegates to exactly
  one specialist team per request
- **Four specialist teams**, each a `SequentialAgent` of
  specialist → critique → refine:
  - **`weather_team`** — real-time conditions and active alerts (NWS API,
    reused from Labs 1–2)
  - **`search_team`** — current disaster/news search (`google_search`,
    reused from Lab 4)
  - **`routes_team`** — evacuation routes via the Google Routes API
    (new; called directly via `requests`, no client library)
  - **`qa_team`** — general safety/preparedness Q&A
- **Callbacks** — request/response logging on every agent; input
  validation scoped to `root_agent` only (the true user-facing boundary),
  per the lesson learned in Lab 5

### Notable issues found and fixed

- **Critique/refine can introduce errors, not just catch them:**
  `search_critique` initially assumed any date past its training cutoff
  must be fabricated, and rejected accurate, correctly-dated live search
  results — on one pass, `search_refine` even silently rewrote a correct
  date to a wrong one to "resolve" the inconsistency. Fixed by explicitly
  stating today's actual date as verified ground truth in both agents'
  instructions, rather than relying on a general "trust the search tool"
  instruction.
- **ADK version mismatch on deployment:** deploying without pinning
  `google-adk` let pip resolve a newer version at deploy time than what
  was installed locally. The newer remote `Runner` expected an
  `agent.mode` attribute that didn't exist on the `LlmAgent` class used
  to pickle the agent locally, causing `stream_query` to fail silently
  (0 events, no client-side exception) — the real error only appeared in
  Cloud Logging (`resource.type="aiplatform.googleapis.com/ReasoningEngine"`,
  log `...%2Freasoning_engine_stderr`). Fixed by pinning
  `google-adk==<exact local version>` in the deployment's `requirements`.
- **Local files aren't auto-bundled:** as in Lab 5, tool and callback
  functions had to be written to disk (`%%writefile tools.py`,
  `%%writefile callbacks.py`) and passed via `extra_packages` for
  deployment, since Agent Engine only bundles files, not in-memory
  notebook objects.

### Environment notes specific to this case study

- Built and run in **Colab Enterprise** (Google Cloud console →
  Vertex AI), not local Jupyter — authenticates via browser sign-in
  rather than local `gcloud` ADC.
- Requires the **Routes API** enabled on the project, with the API key
  used for `GOOGLE_GEO_API_KEY` explicitly granted access to it (separate
  from project-level enablement).
- The Setup cell sets `GOOGLE_GEO_API_KEY` directly via `os.environ`
  rather than `.env`/`load_dotenv()`, since Colab Enterprise doesn't have
  access to the local filesystem's `.env` files. **Replace the
  placeholder key value in that cell with your own key before running.**