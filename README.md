# mcp-chatbot

> **🔊 Note:** This demo video includes narration — turn on your sound for the full experience.

https://github.com/user-attachments/assets/d9e2ba2b-66d0-4825-a1f0-53260f79a8a1

`mcp-chatbot` is a modular chatbot framework using **LangChain MCP** (Multi-Component Protocol) that supports:

- Math calculations
- Weather queries (via WeatherAPI.com)
- Web search fetching HTML content, parsing with markitdown, enforcing English results, and defaulting to top 3 results
- Extendable tools via MCP servers

## Features

- **Multiple MCP servers** (`weather.py`) — mathserver and search are integrated tools
- Easy to extend with new tools
- Async agent orchestration using LangGraph + LangChain
- Environment variable support via `.env`

---

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/mcp-chatbot.git
   cd mcp-chatbot
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Mac/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root:

   ```env
   GROQ_API_KEY=your_groq_api_key
   WEATHER_API_KEY=your_weatherapi_key_here
   ```

   You can get a free Groq API key from: [https://console.groq.com/keys](https://console.groq.com/keys)
   You can get a free WeatherAPI key from: [https://www.weatherapi.com/](https://www.weatherapi.com/)

---

## ▶️ Running the MCP Servers

Only the weather tool needs to be run as an MCP server. The mathserver and search tools are integrated directly as tools within the client and do not require separate servers.

**Weather Server**

```bash
python src/servers/weather.py
```

**Search Tool**

The search tool is integrated directly within the client and does not require a separate server. However, you can run it standalone for testing purposes:

```bash
python src/servers/search.py
```

---

## 🤖 Running the Client

Once your MCP servers are running, start the chatbot client:

```bash
python src/client.py
```

The client will:

- Connect to the running MCP weather server
- Use integrated math and search tools directly
- Pass user messages to the agent, which decides whether to call math, weather, or search tools
- Summarize search results for user-friendly responses

---

## 💡 Example Usage

```
User: What is (3 + 5) * 12?
Bot: The result of (3 + 5) x 12 is 96.

User: What's the weather in San Francisco?
Bot: Weather in San Francisco, CA, USA:
Condition: Clear
Temperature: 20°C (feels like 19°C)
Humidity: 60%
Wind: 10 km/h NW

User: Search the web for history of Python programming language
Bot: Python is a high-level, interpreted programming language known for its readability and versatility. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms and has a large standard library.
```

---

## 🛠 Adding New Tools

1. Create a new file in `src/servers/` (e.g., `newtool.py`)
2. Initialize it with:

   ```python
   from mcp.server.fastmcp import FastMCP
   mcp = FastMCP("NewTool")

   @mcp.tool()
   async def my_tool(param1: str) -> str:
       return f"You passed {param1}"

   if __name__ == "__main__":
       mcp.run(transport="stdio")
   ```

3. Start the server in a new terminal.
4. Update `client.py` to load your new MCP tool.

---

## 🧪 Development Notes

- Ensure each server is running before starting the client.
- MCP uses standard input/output or HTTP transport — keep ports unique if using HTTP.
- For debugging, `print()` statements in server functions appear in the terminal running that server.
- The search tool uses the `ddgs` library and markitdown to fetch and parse HTML content, enforces English language results, strips links, and returns only the top 3 results by default.
