from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
from markitdown import MarkItDown
import sys, re

mcp = FastMCP("Search")

def _log(msg: str):
    # stderr only so we don't break stdio transport
    print(f"[Search Tool] {msg}", file=sys.stderr, flush=True)

def _strip_links(md_text: str) -> str:
    """
    Remove images, markdown links, and bare URLs from Markdown -> plain text.
    (We only regex clean the Markdown that MarkItDown produced, not the HTML.)
    """
    if not md_text:
        return ""
    text = md_text
    # Remove images: ![alt](url)
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    # Replace markdown links [label](url) -> label
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Drop bare URLs
    text = re.sub(r'https?://\S+', '', text)
    # Clean common markdown prefixes (#, >, -, *)
    text = re.sub(r'^[#>\-\*\s]+\s*', '', text, flags=re.MULTILINE)
    # Collapse whitespace/newlines
    text = re.sub(r'[ \t\f\v]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

@mcp.tool()
async def web_search(query: str, max_results: int = 5, include_content: bool | int = True) -> str:
    """
    Minimal web search:
      - DDGS top results
      - MarkItDown -> Markdown
      - Strip links -> plain text
      - Return up to `max_results` blocks (default 1)
    `include_content`:
      - True -> include ~1200 chars per page
      - False/0 -> just the title (no page fetch)
      - int -> that many chars per page (cap ~4000)
    """
    _log(f"Searching: {query} (max_results={max_results}, include_content={include_content})")

    try:
        mr = max(1, min(int(max_results), 10))
    except Exception:
        mr = 1

    if isinstance(include_content, bool):
        content_chars = 1200 if include_content else 0
    else:
        try:
            content_chars = int(include_content)
        except Exception:
            content_chars = 1200
    content_chars = max(0, min(content_chars, 4000))

    # 1) get top results
    results = []
    try:
        with DDGS() as ddg:
            for r in ddg.text(query, region="us-en", safesearch="moderate", max_results=mr * 5):
                title = (r.get("title") or r.get("title_full") or "").strip()
                href = (r.get("href") or r.get("link") or r.get("url") or "").strip()
                if title and href:
                    results.append((title, href))
                if len(results) >= mr * 2:
                    break
    except Exception as e:
        return f"Search error: {e}"

    if not results:
        return "No results found."

    # 2) fetch & convert
    md = MarkItDown()
    out = []
    fetched = 0
    for title, url in results:
        block = [title]  # plain title line

        if content_chars > 0 and fetched < mr:
            try:
                doc = md.convert(url)
                raw = (getattr(doc, "text_content", "") or "").strip()
                text = _strip_links(raw)
                if text:
                    if len(text) > content_chars:
                        text = text[: content_chars - 1].rstrip() + "…"
                    block += ["", text]
                    fetched += 1
            except Exception as fe:
                _log(f"Content fetch skipped for {url}: {fe}")

        out.append("\n".join([b for b in block if b]))
        if len(out) >= mr:
            break

    return "\n\n---\n\n".join(out)

if __name__ == "__main__":
    import sys
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--max", type=int, default=5, help="Max results")
    parser.add_argument("--content", action="store_true", help="Include page content")
    args = parser.parse_args()

    if args.query:
        # Direct run mode
        async def run_direct():
            results = await web_search(
                query=args.query,
                max_results=args.max,
                include_content=args.content
            )
            print(results)

        asyncio.run(run_direct())
    else:
        # MCP server mode
        mcp.run(transport="stdio")