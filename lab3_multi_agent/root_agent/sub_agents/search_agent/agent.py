from google.adk.agents import Agent
from google.adk.tools import google_search

search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Answers general knowledge questions and looks up current information using web search.",
    instruction=(
        "You answer general questions by searching the web for relevant, "
        "up-to-date information. Summarize findings clearly and concisely."
    ),
    tools=[google_search],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
