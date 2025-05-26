import sys
import asyncio
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, SseServerParams, mcp_server_tools, SseMcpToolAdapter

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

print("Starting client...")

def extract_text_content(content) -> str:
    if isinstance(content, list) and len(content) > 0:
        first_item = content[0]
        if hasattr(first_item, 'content'):
            return first_item.content
        elif hasattr(first_item, 'text'):
            return first_item.text
        elif isinstance(first_item, dict) and 'text' in first_item:
            return first_item['text']
        else:
            print(f"[WARNING] Unexpected content type in first item: {type(first_item)}. Attempting string conversion.")
            return str(first_item)
    elif content is None:
        return ""
    elif hasattr(content, 'content'):
        return content.content
    else:
        return str(content)

async def main():
    SERVER_URL = "http://localhost:7000/sse"
    print(f"[DEBUG] Connecting to MCP server via SSE at {SERVER_URL}")
    server_params = SseServerParams(
        url=SERVER_URL,
        timeout=300,
        sse_read_timeout=600
    )
    try:
        print("[DEBUG] Initializing McpWorkbench...")
        async with McpWorkbench(server_params=server_params) as workbench:
            print("[DEBUG] McpWorkbench initialized. Connected to MCP server.")
            tools = await workbench.list_tools()
            print("[DEBUG] Tools received:", [tool["name"] for tool in tools])
            print("\nType a coding problem or 'quit' to exit.")
            while True:
                user_query = input("\nQuery: ").strip()
                if user_query.lower()=="quit":
                    print("Exiting client...")
                    break
                try:
                    print(f"\n[DEBUG] Calling get_planning_steps with user query")
                    planning_result_raw = await workbench.call_tool("get_planning_steps",{"user_query":user_query})
                    planning_steps_text = extract_text_content(planning_result_raw.result)
                    print("[DEBUG] Planning steps received.")
                    print("\nPLANNED STEPS:\n")
                    print(planning_steps_text)
                    print("\n[DEBUG] Calling generate_code_from_plan with steps")
                    code_result_raw = await workbench.call_tool("generate_code_from_plan", {"steps": planning_steps_text})
                    generated_code_text = extract_text_content(code_result_raw.result)
                    print("[DEBUG] Code generated")
                    print("\nGENERATED CODE:\n")
                    print(generated_code_text)
                except Exception as e:
                    print(f"[ERROR] Error during tool calls: {e}")
    except Exception as e:
        print(f"[ERROR] Error setting up McpWorkbench or connecting to the server: {e}") 


asyncio.run(main())
