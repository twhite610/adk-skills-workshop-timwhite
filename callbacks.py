import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse

# Build a dedicated logger with its own file handler, independent of
# whatever the ADK framework does to the root logger.
logger = logging.getLogger("weather_agent_callbacks")
logger.setLevel(logging.INFO)
logger.propagate = False  # don't let messages bubble up to ADK's root handlers

if not logger.handlers:
    file_handler = logging.FileHandler("weather_agent.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)


def log_before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Logs the user-provided request immediately before it's sent to the LLM.
    Returning None allows the model call to proceed unmodified.
    """
    try:
        last_content = llm_request.contents[-1]
        user_text = "".join(part.text or "" for part in last_content.parts)
    except (IndexError, AttributeError):
        user_text = "<unavailable>"

    logger.info(
        f"REQUEST | agent={callback_context.agent_name} | "
        f"invocation={callback_context.invocation_id} | "
        f"user_input={user_text!r}"
    )
    return None


def log_after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Logs the model's response immediately after it's received.
    Returning None allows the original response to be used unmodified.
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