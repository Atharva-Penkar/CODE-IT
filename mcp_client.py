import sys
import asyncio
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

print("Starting client...")

def extract_text_content(content) -> str:
    """
    Extracts the plain string text from various content formats returned by agents or tools.
    Assumes content might be a list containing objects/dicts with a 'text' attribute/key,
    or a direct string.
    Now also handles autogen_core.tools._workbench.TextResultContent.
    """
    if isinstance(content, list) and len(content) > 0:
        first_item = content[0]
        # NEW: Check for 'content' attribute first, as seen in TextResultContent
        if hasattr(first_item, 'content'):
            return first_item.content
        elif hasattr(first_item, 'text'):
            return first_item.text
        elif isinstance(first_item, dict) and 'text' in first_item:
            return first_item['text']
        else:
            # Fallback if structure is unexpected
            print(f"[WARNING] Unexpected content type in first item: {type(first_item)}. Attempting string conversion.")
            return str(first_item)
    elif content is None:
        return "" # Handle cases where content might be None
    # NEW: Handle if the content itself is a TextResultContent object (not wrapped in a list)
    elif hasattr(content, 'content'):
        return content.content
    else:
        # If it's not a list, assume it's already a string or something directly convertible
        return str(content)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    server_script = sys.argv[1]
    print(f"[DEBUG] Using server script: {server_script}")
    server_params = StdioServerParams(
        command="python",
        args=[server_script],
        read_timeout_seconds=60,
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
                    print(f"[DEBUG] Calling get_planning_steps with user query")
                    planning_result_raw = await workbench.call_tool("get_planning_steps",{"user_query":user_query})
                    planning_steps_text = extract_text_content(planning_result_raw.result)
                    print("[DEBUG] Planning steps received.")
                    print("\nPlanning steps:")
                    print(planning_steps_text)
                    print("\n[DEBUG] Calling generate_code_from_plan with steps")
                    code_result_raw = await workbench.call_tool("generate_code_from_plan", {"steps": planning_steps_text})
                    generated_code_text = extract_text_content(code_result_raw.result)
                    print("[DEBUG] Code generated")
                    print("\nGenerated code:")
                    print(generated_code_text)
                except Exception as e:
                    print(f"[ERROR] Error during tool calls: {e}")
    except Exception as e:
        print(f"[ERROR] Error setting up McpWorkbench or connecting to the server: {e}")


asyncio.run(main())