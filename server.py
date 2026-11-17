"""Research document tools exposed through MCP over standard input/output."""
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DOCUMENT_DIR = Path(__file__).resolve().parent / "research_documents"
mcp = FastMCP("Research Document Assistant")


@mcp.tool()
def list_documents() -> list[str]:
    """List available UTF-8 text research documents."""
    return sorted(p.name for p in DOCUMENT_DIR.glob("*.txt") if p.is_file())


@mcp.tool()
def search_documents(query: str) -> list[dict[str, str]]:
    """Find documents containing a case-insensitive literal phrase; return full text.

    Use concise topic phrases such as 'deep learning', 'neural networks', or 'CNN'.
    An empty or whitespace-only query returns no matches.
    """
    phrase = query.strip().casefold()
    if not phrase:
        return []
    results = []
    for filename in list_documents():
        content = read_document(filename)
        if phrase in content.casefold():
            results.append({"file": filename, "content": content})
    return results


@mcp.tool()
def read_document(filename: str) -> str:
    """Read a listed text document by basename, for example machine_learning.txt.

    Paths outside the research document directory are rejected.
    """
    if not filename or Path(filename).name != filename or "\\" in filename:
        raise ValueError("Use a document basename from list_documents().")
    path = (DOCUMENT_DIR / filename).resolve()
    if path.parent != DOCUMENT_DIR.resolve() or path.suffix != ".txt":
        raise ValueError("Only text files inside research_documents are allowed.")
    if not path.is_file():
        raise ValueError(f"Document not found: {filename}")
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
