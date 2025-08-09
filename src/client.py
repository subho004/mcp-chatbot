from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import re
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
    print("Loaded tools:", [t.name for t in tools])
    tool_names = ", ".join([t.name for t in tools])
    model = ChatGroq(model="llama-3.3-70b-versatile")
    model_plain = ChatGroq(model="llama-3.3-70b-versatile")
    agent = create_react_agent(
        model,
        tools,
    )

    SYSTEM_INSTRUCTION = (
        f"You are a strict tool-using agent. You may ONLY use the MCP tools provided to you: {tool_names}. "
        "Do NOT call any tool names that are not listed here (e.g., brave_search, web_search, browser, etc.). "
        "If a tool exists that can answer the user's question, you MUST call that tool before answering. "
        "For any query about weather, temperature, forecast, conditions, humidity, wind, or a city/location, you MUST call the MCP tool `get_weather` with a `location` argument. "
        "Never nest tool calls inside another tool's parameters. Use multiple sequential tool calls instead (e.g., call `add` to get a number, then call `multiple` with that result). "
        "Your FINAL answer must be plain natural language with no tool-call tags, XML, or function markup."
    )

    # A batch of user messages; the agent will decide which MCP tool to call per message
    user_messages = [
        "what's (3 + 5) x 12?",
        "What's the current weather in San Francisco, US?",
        # add more items here; the agent will pick tools as needed
    ]

    for i, msg in enumerate(user_messages, start=1):
        base_messages = [
            {"role": "system", "content": (
                SYSTEM_INSTRUCTION +
                " If a tool exists that can answer the user's question, you MUST call that tool. "
                "Do not guess about real-world data when a tool is available."
            )},
            {"role": "user", "content": msg},
        ]
        result = await agent.ainvoke({"messages": base_messages})
        final_text = result['messages'][-1].content
        # Fallback: if the model returned tool-call markup, ask it to reformat
        if isinstance(final_text, str) and "<function=" in final_text:
            try:
                reformatted = await model_plain.ainvoke([
                    SystemMessage(content=(
                        "Rewrite the assistant's last message as a final natural-language answer. "
                        "Do NOT call tools or include any tool-call markup. If arithmetic is implied, compute it and provide the final number."
                    )),
                    HumanMessage(content=msg),
                    AIMessage(content=final_text),
                ])
                final_text = reformatted.content
            except Exception as e:
                print("Reformat fallback failed:", e)
                # Very basic sanitization: strip tool tags if present
                final_text = re.sub(r"</?function[^>]*>", "", final_text)
        print(f"Message {i} response:", final_text)

asyncio.run(main())