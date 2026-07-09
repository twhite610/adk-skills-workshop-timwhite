from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search
from .callbacks import log_before_model, validate_input, log_after_model

GEMINI_MODEL = "gemini-2.5-flash"

STATE_SEARCH_RESULT = "search_result"
STATE_CRITIQUE = "critique"


# --- Search agent: finds data to answer the question ---
search_agent = Agent(
    name="search_agent",
    model=GEMINI_MODEL,
    description="Searches the web to find information needed to answer the question.",
    instruction=(
        "Search the web for information that answers the user's question. "
        "Provide a clear, factual draft answer based on what you find."
    ),
    tools=[google_search],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key=STATE_SEARCH_RESULT,
    before_model_callback=[log_before_model, validate_input],
    after_model_callback=log_after_model,
)

# --- Critique agent: reviews the draft and suggests improvements ---
critique_agent = Agent(
    name="critique_agent",
    model=GEMINI_MODEL,
    description="Reviews the draft answer and suggests specific improvements.",
    instruction=(
        f"Review this draft answer:\n\n{{{STATE_SEARCH_RESULT}}}\n\n"
        "Identify anything missing, unclear, inaccurate, or poorly explained. "
        "Provide specific, actionable suggestions for improvement. "
        "Do not rewrite the answer yourself — only critique it."
    ),
    output_key=STATE_CRITIQUE,
    before_model_callback=[log_before_model, validate_input],
    after_model_callback=log_after_model,
)

# --- Refine agent: rewrites the answer based on the critique ---
refine_agent = Agent(
    name="refine_agent",
    model=GEMINI_MODEL,
    description="Rewrites the draft answer based on the critique's suggestions.",
    instruction=(
        f"Original draft answer:\n{{{STATE_SEARCH_RESULT}}}\n\n"
        f"Critique and suggested improvements:\n{{{STATE_CRITIQUE}}}\n\n"
        "Rewrite the answer, applying the suggested improvements. "
        "Output ONLY the final, polished answer — no explanations or "
        "meta-commentary about the changes you made."
    ),
    before_model_callback=[log_before_model, validate_input],
    after_model_callback=log_after_model,
)

# --- The answer pipeline: search -> critique -> refine, in order ---
answer_team = SequentialAgent(
    name="answer_team",
    description="Answers a question by searching for data, critiquing the draft, and refining it.",
    sub_agents=[search_agent, critique_agent, refine_agent],
)

# --- Root agent: the "Greeter" — handles small talk, delegates real questions ---
root_agent = Agent(
    name="root_agent",
    model=GEMINI_MODEL,
    description="Greets the user and routes real questions to the answer team.",
    instruction=(
        "You are a friendly greeter. If the user is just greeting you or "
        "making small talk, respond warmly and briefly yourself.\n\n"
        "If the user asks an actual question that needs a researched answer, "
        "delegate to answer_team — do not try to answer it yourself."
    ),
    sub_agents=[answer_team],
    before_model_callback=[log_before_model, validate_input],
    after_model_callback=log_after_model,
)
