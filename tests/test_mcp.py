import unittest
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


class MCPIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_workflow(self):
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")], cwd="/tmp")
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                self.assertEqual({t.name for t in tools.tools}, {"list_documents", "search_documents", "read_document"})
                listing = await session.call_tool("list_documents", {})
                self.assertFalse(listing.isError)
                self.assertIn("ai.txt", str(listing.content))
                for phrase, expected in [("CNN", "deep_learning.txt"), ("NEURAL NETWORKS", "machine_learning.txt"), ("deep learning", "deep_learning.txt")]:
                    result = await session.call_tool("search_documents", {"query": phrase})
                    self.assertFalse(result.isError)
                    self.assertIn(expected, str(result.content))
                for phrase in ["   ", "a-topic-that-does-not-exist"]:
                    result = await session.call_tool("search_documents", {"query": phrase})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.structuredContent, {"result": []})
                result = await session.call_tool("read_document", {"filename": "machine_learning.txt"})
                self.assertFalse(result.isError)
                self.assertIn("Supervised learning", str(result.content))
                for filename in ["../server.py", str(ROOT / "server.py"), "missing.txt", "..\\server.py"]:
                    result = await session.call_tool("read_document", {"filename": filename})
                    self.assertTrue(result.isError, filename)


if __name__ == "__main__":
    unittest.main()
