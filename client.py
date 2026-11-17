"""Exercise real MCP tool calls without an LLM or API key."""
import asyncio
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).resolve().with_name("server.py"))],
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available tools:", ", ".join(t.name for t in tools.tools))
            for name, arguments in [
                ("search_documents", {"query": "deep learning"}),
                ("search_documents", {"query": "neural networks"}),
                ("search_documents", {"query": "CNN"}),
                ("read_document", {"filename": "machine_learning.txt"}),
            ]:
                result = await session.call_tool(name, arguments)
                if result.isError:
                    raise RuntimeError(str(result.content))
                print(f"\n{name}({arguments}):")
                for block in result.content:
                    if block.type == "text":
                        print(block.text)


if __name__ == "__main__":
    asyncio.run(main())
