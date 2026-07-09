import asyncio

from dotenv import load_dotenv
load_dotenv("root_agent/.env")

from google.adk.runners import InMemoryRunner
from google.genai import types
from root_agent.agent import root_agent

from dotenv import load_dotenv
load_dotenv("root_agent/.env")

async def run_query(runner, user_id, session_id, query):
    print(f"\n{'='*60}")
    print(f"USER: {query}")
    print(f"{'='*60}")

    content = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        author = event.author
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"[{author}] TEXT: {part.text[:200]}")
                if part.function_call:
                    print(f"[{author}] TOOL CALL: {part.function_call.name}")
                if part.function_response:
                    print(f"[{author}] TOOL RESPONSE: {part.function_response.name}")
        if event.actions and event.actions.transfer_to_agent:
            print(f"[{author}] TRANSFERRED TO: {event.actions.transfer_to_agent}")


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="lab4_answer_team")

    user_id = "test_user"
    session_id = "test_session"

    await runner.session_service.create_session(
        app_name="lab4_answer_team", user_id=user_id, session_id=session_id
    )

    # Test 1: greeting -> should be handled directly by root_agent
    await run_query(runner, user_id, session_id, "Hi there!")

    # Test 2: real question -> should delegate through answer_team
    await run_query(
        runner, user_id, session_id, "What are the health benefits of green tea?"
    )


if __name__ == "__main__":
    asyncio.run(main())
