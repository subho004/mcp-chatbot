from typing import List
from mcp.server.fastmcp import FastMCP
import requests
import urllib.parse

mcp = FastMCP("Search")

@mcp.tool()
async def web_search(query: str, max_results: int | str = 5) -> str:
    """
    Search the web using DuckDuckGo's unofficial API.
    Returns up to `max_results` results with title and URL.
    """
    print(f"[Search Tool] web_search called with query='{query}', max_results={max_results}")
    try:
        # Coerce and clamp max_results
        try:
            mr = int(max_results)
        except Exception:
            mr = 5
        mr = max(1, min(mr, 10))
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
        resp = requests.get(url, params=params, timeout=12, headers=headers)
        try:
            data = resp.json()
        except Exception as je:
            return f"Error: DuckDuckGo returned non-JSON: {je}"

        results: List[str] = []
        # Prefer 'Results' (sometimes contains direct results)
        for item in data.get("Results", []) or []:
            txt = item.get("Text")
            first = item.get("FirstURL") or item.get("Redirect")
            if txt and first:
                results.append(f"{txt} - {first}")
            if len(results) >= mr:
                break

        # Then 'RelatedTopics'
        if len(results) < mr:
            for topic in data.get("RelatedTopics", []) or []:
                if isinstance(topic, dict):
                    if "Text" in topic and "FirstURL" in topic:
                        results.append(f"{topic['Text']} - {topic['FirstURL']}")
                    elif "Topics" in topic:
                        for sub in topic["Topics"]:
                            if "Text" in sub and "FirstURL" in sub:
                                results.append(f"{sub['Text']} - {sub['FirstURL']}")
                            if len(results) >= mr:
                                break
                if len(results) >= mr:
                    break

        # Fallback to Abstract
        if len(results) == 0:
            abstract = data.get("AbstractText")
            aurl = data.get("AbstractURL")
            if abstract and aurl:
                results.append(f"{abstract} - {aurl}")

        if not results:
            return "No results found."

        return "\n".join(results[:mr])
    except Exception as e:
        return f"Error during search: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")