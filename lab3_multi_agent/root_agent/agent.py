from google.adk.agents import Agent
from sub_agents.weather_agent.agent import weather_agent
from sub_agents.search_agent.agent import search_agent

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="Coordinates user requests, delegating to specialized sub-agents.",
    instruction=(
        "You are a coordinating agent. You do not answer questions yourself. "
        "Delegate to the appropriate sub-agent based on the user's request:\n"
        "- If the user asks about weather or current conditions in a location, "
        "delegate to weather_agent.\n"
        "- If the user asks a general knowledge question, or asks something "
        "that requires searching the web for current information, delegate "
        "to search_agent.\n"
        "Choose exactly one sub-agent per request based on intent."
    ),
    sub_agents=[weather_agent, search_agent],
)
