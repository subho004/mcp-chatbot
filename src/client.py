from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import asyncio

async def main():
    BASE_DIR = Path(__file__).resolve().parent
    MATH_SERVER = str(BASE_DIR / "servers" / "mathserver.py")

    client=MultiServerMCPClient(
        {
            "math":{
                "command":"python",
                "args":[MATH_SERVER], ## Ensure correct absolute path
                "transport":"stdio",
            
            },
            "weather": {
                "url": "http://localhost:8000/mcp",  # Ensure server is running here
                "transport": "streamable_http",
            }

        }
    )

    os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")

    tools = await client.get_tools()
    tool_names = ", ".join([t.name for t in tools])
    model = ChatGroq(model="llama-3.1-8b-instant")
    agent = create_react_agent(
        model,
        tools,
    )

    SYSTEM_INSTRUCTION = (
        f"You are a tool-using agent. You may ONLY use the MCP tools provided to you: {tool_names}. "
        "Do NOT call any tool names that are not listed here (e.g., brave_search, web_search, browser, etc.). "
        "For weather questions, ALWAYS call the MCP tool `get_weather`."
        " After using tools, always return a final natural-language answer (not raw tool-call markup)."
    )

    math_response = await agent.ainvoke(
        {"messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": "what's (3 + 5) x 12?"},
        ]}
    )

    print("Math response:", math_response['messages'][-1].content)

    # Call the Weather MCP tool directly so we don't rely on the model choosing a tool
    try:
        weather_tool = next(t for t in tools if t.name == "get_weather")
    except StopIteration:
        print("Weather response: get_weather tool not found. Is the weather server running?")
    else:
        weather_result = await weather_tool.ainvoke({"location": "San Francisco, US"})
        print("Weather response:", weather_result)

asyncio.run(main())