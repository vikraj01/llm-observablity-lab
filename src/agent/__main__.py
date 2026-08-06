"""CLI entry point.

Usage:
    python -m src.agent "what's the weather in Chennai and what's 100/7?"
"""

import sys
import time
import uuid

import structlog
from dotenv import load_dotenv

load_dotenv()  # must happen before any client is created

from ..obs_logging import configure_logging  # noqa: E402
from .graph import graph  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python -m src.agent "your question"')
        raise SystemExit(1)

    configure_logging()
    log = structlog.get_logger()

    # ONE run_id per invocation, bound via contextvars: every log line
    # emitted anywhere during this run (tools, graph, here) carries it
    # automatically. This is hand-rolled context propagation -- remember
    # the pain; OTel does this for you in Phase 5.
    run_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(run_id=run_id)

    question = " ".join(sys.argv[1:])
    log.info("run_started", question=question)

    started = time.perf_counter()
    result = graph.invoke({"messages": [("user", question)]})

    answer = result["messages"][-1].content
    log.info(
        "run_finished",
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
        answer=answer,
        total_messages=len(result["messages"]),
    )

    print("\n=== final answer ===")
    print(answer)


if __name__ == "__main__":
    main()
