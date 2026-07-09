import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

logger = logging.getLogger("weather_agent_callbacks")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler("weather_agent.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)


def _extract_user_text(llm_request: LlmRequest) -> str:
    """Shared helper: pulls the latest user message text out of a request."""
    try:
        last_content = llm_request.contents[-1]
        return "".join(part.text or "" for part in last_content.parts)
    except (IndexError, AttributeError):
        return "<unavailable>"


def log_before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Logs the user-provided request immediately before it's sent to the LLM.
    Always returns None so the chain continues to the next callback.
    """
    user_text = _extract_user_text(llm_request)
    logger.info(
        f"REQUEST | agent={callback_context.agent_name} | "
        f"invocation={callback_context.invocation_id} | "
        f"user_input={user_text!r}"
    )
    return None


def validate_input(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Blocks the request if it violates content guidelines.
    Returning an LlmResponse here short-circuits the chain and the
    actual model call — nothing after this runs.
    """
    user_text = _extract_user_text(llm_request)

    if "BAD" in user_text.upper():
        logger.info(
            f"BLOCKED | agent={callback_context.agent_name} | "
            f"invocation={callback_context.invocation_id} | "
            f"reason=content_guideline_violation"
        )
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Message violates our content guidelines")],
            )
        )

    return None


def log_after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Logs the model's response immediately after it's received.
    """
    try:
        response_text = "".join(part.text or "" for part in llm_response.content.parts)
    except AttributeError:
        response_text = "<unavailable>"

    logger.info(
        f"RESPONSE | agent={callback_context.agent_name} | "
        f"invocation={callback_context.invocation_id} | "
        f"response={response_text!r}"
    )
    return None