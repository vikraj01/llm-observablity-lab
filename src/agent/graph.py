
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from .llm import get_llm
from .tools import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are a helpful assistant with three tools: a calculator, a weather "
    "lookup, and a local docs search. Use tools whenever they apply instead "
    "of guessing. If a tool fails, tell the user honestly and retry at most "
    "once. Keep final answers short."
)


def agent_node(state: MessagesState) -> dict:
    """Call the LLM (with tools bound) on the conversation so far."""
    llm_with_tools = get_llm().bind_tools(ALL_TOOLS)
    messages = [("system", SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: MessagesState) -> str:
    """After the agent speaks: run tools if it asked for them, else finish."""
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def build_graph():
    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")
    return builder.compile()


graph = build_graph()
