import os
from typing import List

import yaml
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_core.models import ChatCompletionClient
from autogen_core.tools import Tool
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from samples.common.prompts import developer_prompt, sre_prompt

_ADDITIONAL_FILE_SURFER_MESSAGE = "\n. Use the file surfer for querying about all the services documentation."
_SELECTOR_PROMPT = """\
Select an agent to perform task.

{roles}

Current conversation context:
{history}

Read the above conversation, then select an agent from {participants} to perform the next task.
Make sure the planner agent has assigned tasks before other agents start working.
Only select one agent.
"""

async def _load_tools() -> List[Tool]:
    kubernetes_params = StdioServerParams(
        command="npx",
        args=["mcp-server-kubernetes"],
    )
    tools = await mcp_server_tools(server_params=kubernetes_params)
    return tools

def _get_model_client(base_path: str  = '.local') -> ChatCompletionClient:
    print(os.getcwd())
    with open(f"{base_path}/model_config.yaml") as f:
        model_config = yaml.safe_load(f)
    return ChatCompletionClient.load_component(model_config)

async def get_team(file_surfer_base_path: str = ".") -> SelectorGroupChat:
    tools = await _load_tools()
    model_client = _get_model_client()
    developer_agent = AssistantAgent(
        "developer_agent",
        system_message=developer_prompt + _ADDITIONAL_FILE_SURFER_MESSAGE,
        description="The developer for the Retail Store application",
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True
    )
    sre_agent = AssistantAgent(
        "sre_agent",
        system_message=sre_prompt + _ADDITIONAL_FILE_SURFER_MESSAGE,
        description="The SRE for the Retail Store application",
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True
    )
    user_proxy = UserProxyAgent(
        name="user_proxy",
        description="A human user that approves or rejects all the operations that all the agents are performing. ",
        input_func=input
    )
    file_surfer = FileSurfer(
        name="file_surfer",
        model_client=model_client,
        description="You have complete access to all the technical and non-technical information about the application.",
        base_path=file_surfer_base_path
    )
    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=25)
    termination = text_mention_termination | max_messages_termination
    team = SelectorGroupChat(
        [developer_agent, sre_agent, user_proxy, file_surfer],
        model_client=model_client,
        termination_condition=termination,
        #selector_prompt=coordinator_prompt + "\n" + _SELECTOR_PROMPT,
        allow_repeated_speaker=True
    )
    return team

async def main() -> None:
    team = await get_team(file_surfer_base_path=f"{os.getcwd()}/docs")

    await Console(team.run_stream(task=input("Enter the task:")))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())