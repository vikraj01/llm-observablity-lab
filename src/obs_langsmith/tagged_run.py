"""Run the agent once with metadata, tags, and a run name attached.

Usage:
    uv run python -m src.obs_langsmith.tagged_run "what's 23*7?"

Then in LangSmith: open the trace and find the metadata/tags on it,
and try filtering the project by tag or metadata key. This is how you'd
slice traces by user, session, or feature flag in a real product.
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from ..agent.graph import graph  # noqa: E402


def main() -> None:
    question = " ".join(sys.argv[1:]) or "what's 23*7?"
    result = graph.invoke(
        {"messages": [("user", question)]},
        config={
            "run_name": "obs-lab-tagged-run",
            "tags": ["phase3", "manual-test"],
            "metadata": {
                "user_id": "vikash",
                "session_id": "session-001",
                "app_version": "0.1.0",
            },
        },
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
