"""Interactive document reader using real MCP calls; no model/API key required."""
import asyncio
from pathlib import Path
import re
import sys
import tempfile
import textwrap

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

STOP_WORDS = set("what is are a an the of to in for find documents document related discusses which summarize summary please tell me about does explain".split())


def terms(text):
    return set(re.findall(r"[a-z0-9]+", text.casefold())) - STOP_WORDS


async def call(session, name, arguments):
    result = await session.call_tool(name, arguments)
    if result.isError:
        raise RuntimeError("Document tool failed. Check the server log.")
    return result.structuredContent["result"]


async def answer(session, question):
    """Rank literal term matches and quote source sentences without inventing facts."""
    keywords = terms(question)
    if not keywords:
        return "Please include a topic, such as deep learning or CNN."
    filenames = await call(session, "list_documents", {})
    summaries = bool(re.search(r"\b(summarize|summary)\b", question, re.I))
    matches = []
    for filename in filenames:
        content = await call(session, "read_document", {"filename": filename})
        title, _, body = content.partition("\n")
        sentences = re.split(r"(?<=[.!?])\s+", body.strip())
        title_score = len(keywords & terms(title))
        ranked = [(len(keywords & terms(s)), i, s) for i, s in enumerate(sentences)]
        best = max(ranked, key=lambda item: (item[0], -item[1]), default=(0, 0, ""))
        if best[0] == 0:
            continue
        if summaries:
            excerpt = " ".join(sentences[:3])
        else:
            excerpt = best[2]
        matches.append((title_score, best[0], filename, excerpt))
    if not matches:
        return "No relevant information found in the available documents. Try another topic."
    matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if re.search(r"\b(find|which)\b", question, re.I):
        return "Matching documents:\n" + "\n\n".join(
            f"{filename}\n{textwrap.fill(excerpt, 88)}" for _, _, filename, excerpt in matches
        )
    _, _, filename, excerpt = matches[0]
    label = "Summary (source excerpt)" if summaries else "Answer (source excerpt)"
    return f"{label}:\n{textwrap.fill(excerpt, 88)}\n\nSource: {filename}"


async def main():
    print("Research Document Assistant")
    print("Uses MCP to retrieve text. Answers are source excerpts, not AI-generated.\n")
    print("Try: What is deep learning? | Which document discusses CNN?")
    print("     Summarize the machine learning document.")
    print("Commands: list, help, exit\n")
    params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).resolve().with_name("server.py"))])
    # Keep protocol/server diagnostics out of the question-and-answer display.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
        try:
            async with stdio_client(params, errlog=log) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    while True:
                        try:
                            question = input("You: ").strip()
                        except EOFError:
                            break
                        if question.casefold() in {"exit", "quit"}:
                            break
                        if not question:
                            continue
                        if question.casefold() == "help":
                            print("\nAsk about a topic, find matching documents, or summarize a document.\n")
                        elif question.casefold() == "list":
                            print("\nDocuments:\n" + "\n".join(await call(session, "list_documents", {})) + "\n")
                        else:
                            print("\n" + await answer(session, question) + "\n")
        except Exception:
            log.seek(0)
            print("Unable to complete the MCP session. Server diagnostics:", file=sys.stderr)
            print(log.read(), file=sys.stderr)
            raise
    print("Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
