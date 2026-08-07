"""Run the agent once with Langfuse tracing (plus session/user/tags).

Usage:
    uv run python -m src.obs_langfuse.traced_run "what's 23*7?"

Contrast with LangSmith: there, tracing was ambient (env var, zero code).
Here we pass an explicit CallbackHandler per invocation. More typing,
but nothing gets traced unless you asked for it -- note the difference
in COMPARISON.md.

If LangSmith env vars are still set, the same run lands in BOTH tools.
That's worth doing at least once: same run, two UIs, compare directly.
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client  # noqa: E402
from langfuse.langchain import CallbackHandler  # noqa: E402

from ..agent.graph import graph  # noqa: E402


def main() -> None:
    question = " ".join(sys.argv[1:]) or "what's 23*7?"

    handler = CallbackHandler()  # reads LANGFUSE_* from env
    result = graph.invoke(
        {"messages": [("user", question)]},
        config={
            "callbacks": [handler],
            "run_name": "obs-lab-agent",
            # special metadata keys the Langfuse handler picks up:
            "metadata": {
                "langfuse_session_id": "session-001",
                "langfuse_user_id": "vikash",
                "langfuse_tags": ["phase4", "manual-test"],
            },
        },
    )
    print(result["messages"][-1].content)

    # short-lived script: make sure buffered events reach the server
    get_client().flush()


if __name__ == "__main__":
    main()
