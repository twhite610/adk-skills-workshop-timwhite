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

## Lab 4: *(pending)*

## Lab 5: *(pending)*
