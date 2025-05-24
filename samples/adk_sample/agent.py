import datetime

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from samples.common.prompts import coordinator_prompt, developer_prompt, sre_prompt

_APP_NAME = "Retail Store"
_USER_ID = "user"
_SESSION_ID = "session"

def get_system_status(service_name: str) -> dict:
    """Retrieves current status for a specified service.

        Args:
            service_name (str): The name of the service to check

        Returns:
            dict: Service status information
    """

    if service_name.lower() == "kubernetes":
        return {
            "status": "healthy",
            "uptime": "93.7%",
            "last_check": datetime.datetime.now().isoformat(),
            "nodes": 23,
            "pods_running": 145
        }
    else:
        return {
            "status": "unknown",
            "error": f"Service '{service_name}' not found in monitoring system"
        }

async def call_agent_async(query: str, runner, user_id, session_id):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    response = "Agent did not produce a response."
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                response = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                response = "Escalation requested."
            break
    return response

async def main():
    developer_agent = Agent(
        name="developer_agent",
        instruction=developer_prompt,
        description="The developer for the Retail Store application",
        model=LiteLlm("azure/gpt-4o"),
        tools=[
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="npx.cmd",
                    args=["mcp-server-kubernetes"]
                )
            )
        ]
    )
    sre_agent = Agent(
        name="sre_agent",
        model=LiteLlm("azure/gpt-4o"),
        instruction=sre_prompt,
        description="The SRE for the Retail Store application",
        tools=[
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="npx.cmd",
                    args=["mcp-server-kubernetes"]
                )
            ),
            get_system_status
        ]
    )
    coordinator_agent = Agent(
        name="coordinator_agent",
        model=LiteLlm("azure/gpt-4o"),
        instruction=coordinator_prompt,
        description="The SME for the Retail Store application",
        sub_agents=[
            developer_agent,
            sre_agent
        ],
    )
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        user_id=_USER_ID,
        session_id=_SESSION_ID,
        app_name=_APP_NAME,
    )

    runner = Runner(
        agent=coordinator_agent,
        app_name=_APP_NAME,
        session_service=session_service,
    )

    query = input("Enter your query: ")
    while query != "TERMINATE":
        result = await call_agent_async(query, runner, _USER_ID, _SESSION_ID)
        print("Agent response --> ", result)
        query = input("Enter your query: ")

if __name__ == "__main__":
    import asyncio

    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop) # See: https://stackoverflow.com/questions/44633458/why-am-i-getting-notimplementederror-with-async-and-await-on-windows
    asyncio.run(main())