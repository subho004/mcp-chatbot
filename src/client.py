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
from groq import BadRequestError

def _extract_search_query(msg: str) -> str:
    s = msg.strip()
    s = re.sub(r"^(search( the web)?( for)?|find|look up|lookup)\s+", "", s, flags=re.I)
    s = re.sub(r"^for\s+", "", s, flags=re.I)
    s = re.sub(r"^the\s+", "", s, flags=re.I)
    s = re.sub(r"[.?!]+$", "", s)
    return s.strip()

def _needs_web(msg: str) -> bool:
    """
    Heuristic: decide if this user message should force a web search.
    Triggers on queries that likely require up-to-date or external facts.
    """
    m = msg.lower().strip()
    keywords = [
        "latest", "news", "update", "updates", "recent", "trend", "trends",
        "who is", "what is", "when was", "history", "timeline", "background",
        "document", "docs", "documentation", "tutorial", "guide", "how to", "how-to",
        "best", "top", "compare", "vs ", "versus", "review", "reviews",
        "pricing", "price", "specs", "features", "release", "changelog",
        "conference", "paper", "research", "breakthrough", "state of the art",
        "sota", "benchmarks", "dataset", "github", "repo", "repository"
    ]
    # Fast checks
    if any(k in m for k in keywords):
        return True
    # Simple question forms
    if m.endswith("?"):
        return True
    # If the message explicitly asks to search/find/lookup, we already handle elsewhere,
    # but still return True to force web use.
    if re.search(r"\b(search( the web)?( for)?|find|look\s*up|lookup)\b", m):
        return True
    return False

async def _summarize(model, query: str, snippets: str) -> str:
    """
    Summarize the concatenated web_search snippets into a concise, self-contained answer.
    - No raw URLs or link markup.
    - Prefer concrete facts and dates.
    - Keep it short (120–180 words) unless the query explicitly asks for a list.
    """
    sys_msg = SystemMessage(content=(
        "You are a concise summarizer. Read the provided snippets and answer the user's query clearly and briefly. "
        "Do NOT include raw URLs or link markup. If dates are present, keep them. If information is missing, say so."
    ))
    user_msg = HumanMessage(content=f"Query: {query}\n\nSnippets:\n{snippets}")
    try:
        res = await model.ainvoke([sys_msg, user_msg])
        return (res.content or "").strip()
    except Exception as e:
        return f"Summary unavailable: {e}"

async def main():
    BASE_DIR = Path(__file__).resolve().parent
    MATH_SERVER = str(BASE_DIR / "servers" / "mathserver.py")

    os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
    os.environ["MCP_VERBOSE"] = "1"

    client=MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": [MATH_SERVER],  # Ensure correct absolute path
                "transport": "stdio",
            },
            "weather": {
                "url": "http://127.0.0.1:8000/mcp",
                "transport": "streamable_http",
            },
            "search": {
                "command": "python",
                "args": [str(BASE_DIR / "servers" / "search.py")],
                "transport": "stdio",
            }
        }
    )

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
        "Your FINAL answer must be plain natural language with no tool-call tags, XML, or function markup. "
        "CRITICAL: For any request that involves external information or real-world facts (e.g., news, documentation, definitions, background/history, timelines, people/companies/technologies, product info, comparisons, lists like 'top/best X', tutorials/guides/how-tos, or anything that plausibly requires the web), you MUST call the MCP tool `web_search` FIRST—even if the user did not say 'search', 'find', or 'look up'. "
        "If you are uncertain whether the query needs the web, err on the side of calling `web_search` first. "
        "Examples that MUST trigger `web_search`: 'latest AI research breakthroughs', 'top 5 programming tutorials for beginners', 'history of Python programming language', 'who is ...', 'what is ...', 'show recent updates to ...', 'compare X vs Y', 'best libraries for ...'. "
        "When calling `web_search`, pass an integer for `max_results` (e.g., 5), not a string."
    )

    # A batch of user messages; the agent will decide which MCP tool to call per message
    user_messages = [
        # "what's (3 + 5) x 12?",
        # "What's the current weather in San Francisco, US?",
        "Search the web for latest news on AI research breakthroughs.",
        # "Find top 5 programming tutorials for beginners.",
        # "Look up the history of Python programming language.",
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

        # Force web search for queries that likely need external info
        forced_web = False
        forced_result = None
        if _needs_web(msg):
            try:
                search_tool = next(t for t in tools if t.name == "web_search")
                topic = _extract_search_query(msg) or msg
                forced_result = await search_tool.ainvoke({"query": topic, "max_results": 5, "include_content": True})
                forced_web = True
            except Exception as fe:
                print("Forced web_search failed:", fe)
                forced_web = False

        try:
            if forced_web and isinstance(forced_result, str) and forced_result.strip():
                final_text = await _summarize(model_plain, msg, forced_result)
            else:
                result = await agent.ainvoke({"messages": base_messages})
                final_text = result['messages'][-1].content
        except Exception as e:
            # If the agent's tool call failed, try a direct MCP tool fallback for search or weather
            err_txt = str(e)
            print("Agent error:", err_txt)
            final_text = None
            if any(k in msg.lower() for k in ["search", "find", "look up", "news"]):
                # direct search fallback
                try:
                    search_tool = next(t for t in tools if t.name == "web_search")
                    topic = _extract_search_query(msg)
                    sr = await search_tool.ainvoke({"query": topic, "max_results": 5, "include_content": True})
                    final_text = await _summarize(model_plain, msg, sr)
                except Exception as se:
                    final_text = f"Search failed: {se}"
            elif any(k in msg.lower() for k in ["weather", "temperature", "forecast"]):
                try:
                    wtool = next(t for t in tools if t.name == "get_weather")
                    # naive location extraction: use whole message; your agent usually provides city explicitly
                    sr = await wtool.ainvoke({"location": msg})
                    final_text = sr
                except Exception as we:
                    final_text = f"Weather failed: {we}"
            else:
                final_text = "Sorry, I had trouble answering that."

        # Reformat if the model returned tool-call markup
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
            except Exception as e2:
                print("Reformat fallback failed:", e2)
                final_text = re.sub(r"</?function[^>]*>", "", final_text)

        # If we forced a web search and got nothing useful, at least show the results
        if forced_web and (not isinstance(final_text, str) or not final_text.strip()):
            final_text = forced_result or "No results found."

        print(f"Message {i} response:", final_text)

asyncio.run(main())