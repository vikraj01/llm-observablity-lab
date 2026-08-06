import ast
import operator
import random
from pathlib import Path

from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore

from .llm import get_embeddings

# --------------------------------------------------------------------------
# 1. calculator
# --------------------------------------------------------------------------

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    """Recursively evaluate an arithmetic AST. Anything non-arithmetic raises."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


@tool
def calculator(expression: str) -> str:
    """Evaluate a plain arithmetic expression and return the result.

    Supports +, -, *, /, //, %, ** and parentheses. Numbers only --
    no variables, no functions. Example: "23 * 7" or "(100 / 7) + 2".
    """
    result = _safe_eval(ast.parse(expression.strip(), mode="eval"))
    # return ints cleanly (7.0 -> "7")
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return str(result)


# --------------------------------------------------------------------------
# 2. get_weather (fake + flaky on purpose)
# --------------------------------------------------------------------------

_CONDITIONS = ["sunny", "cloudy", "light rain", "humid", "windy"]


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city: temperature in Celsius and conditions.

    Use this whenever the user asks about weather, temperature, or conditions
    in any city.
    """
    # Deliberate flakiness: ~20% of calls fail. This simulates a real,
    # unreliable upstream service and gives us errors worth tracing.
    if random.random() < 0.2:
        raise RuntimeError(f"weather service timeout for city={city!r}")
    # Deterministic-per-city fake data so answers look plausible.
    rng = random.Random(city.strip().lower())
    temp = rng.randint(18, 38)
    condition = rng.choice(_CONDITIONS)
    return f"{city}: {temp}°C, {condition}"


# --------------------------------------------------------------------------
# 3. search_docs (tiny RAG over docs/)
# --------------------------------------------------------------------------

_DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
_vector_store: InMemoryVectorStore | None = None


def _get_vector_store() -> InMemoryVectorStore:
    """Build the vector store on first use (embeds every file in docs/)."""
    global _vector_store
    if _vector_store is None:
        store = InMemoryVectorStore(get_embeddings())
        texts, metadatas = [], []
        for path in sorted(_DOCS_DIR.glob("*.md")):
            texts.append(path.read_text(encoding="utf-8"))
            metadatas.append({"source": path.name})
        store.add_texts(texts, metadatas=metadatas)
        _vector_store = store
    return _vector_store


@tool
def search_docs(query: str) -> str:
    """Search the local engineering notes (markdown docs) and return the most
    relevant excerpts.

    Use this when the user asks what "the docs" or "my notes" say about a
    topic, e.g. retries, timeouts, rate limits, circuit breakers.
    """
    results = _get_vector_store().similarity_search(query, k=2)
    if not results:
        return "No matching documents found."
    return "\n\n---\n\n".join(
        f"[{doc.metadata['source']}]\n{doc.page_content}" for doc in results
    )


ALL_TOOLS = [calculator, get_weather, search_docs]
