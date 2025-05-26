import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from autogen_agentchat.agents import AssistantAgent, BaseChatAgent
from autogen_agentchat.messages import TextMessage, StopMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMessageTermination, MaxMessageTermination, ExternalTermination
from autogen_agentchat.base import Response

from autogen_ext.models.ollama import OllamaChatCompletionClient

from autogen_core.code_executor import CodeBlock
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Python-code-runner")

ollama_model_client = OllamaChatCompletionClient(model="llama3.1:8b")

@mcp.tool(name="get_planning_steps")
async def get_planning_steps(user_query: str) -> str:
    planning_template=f"""You are a helpful Planning Assistant.
    Based on the query of the user, you will provide the steps required to solve the problem in the form of a list.

    USER QUERY:
    {user_query}

    - The steps will only tell how to solve the problem and nothing else.
    - Return only the steps and nothing else.
    - If there are multiple alternatives, return the most optimized one.
    - Do not hallucinate.
    - Do not return TERMINATE
    """
    planning_message = TextMessage(source="user", content=planning_template)
    planning_agent = AssistantAgent(
        name="planning_agent",
        model_client=ollama_model_client,
        description="A planning assistant which provides a list of steps to follow for better approach, to solve the problem."
    )
    result = await planning_agent.on_messages(messages=[planning_message], cancellation_token=None)
    return result.chat_message.content

@mcp.tool(name="generate_code_from_plan")
async def generate_code_from_steps(steps: str) -> str:
    initial_code_template = f"""You are a helpful Coding Assistant. 
    You will be given the steps to solve a coding problem by the planning agent.

    STEPS:
    {steps}

    - Follow the steps to solve the problem.
    - Generate code only and nothing else.
    - Return only the code and nothing else.
    - If there are multiple possible codes, return the most optimized code.
    - Return only one code.
    - Do not return TERMINATE
    """
    code_message = TextMessage(source="planner", content=initial_code_template)
    code_generator = AssistantAgent(
        name="inital_code_generator",
        model_client=ollama_model_client,
        description="A Coding assistant which provides code according to the steps given"
    )
    result = await code_generator.on_messages(messages=[code_message], cancellation_token=None)
    return result.chat_message.content

if __name__=="__main__":
    mcp.run()