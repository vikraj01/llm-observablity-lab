"""Phase 2: structured logging with structlog.

One function to configure, one decorator to instrument tools.

Key ideas this module demonstrates:
- JSON logs: every line is a machine-parseable event, not prose.
- Context propagation: bind run_id ONCE per invocation via contextvars,
  and every log line emitted anywhere in the run carries it automatically.
  (This is a hand-rolled version of what OpenTelemetry calls "context".)
"""

import functools
import logging
import time

import structlog


def configure_logging() -> None:
    """Configure structlog for JSON output. Call once, at startup."""
    structlog.configure(
        processors=[
            # merge in whatever was bound via structlog.contextvars.* (run_id!)
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger()


def logged_tool(fn):
    """Decorator: log start/finish/failure + duration of a tool function.

    Apply UNDER the @tool decorator, i.e.:

        @tool
        @logged_tool
        def calculator(expression: str) -> str: ...
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        log.info("tool_started", tool=fn.__name__, tool_args=kwargs or list(args))
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            log.error(
                "tool_failed",
                tool=fn.__name__,
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
                error=f"{type(exc).__name__}: {exc}",
            )
            raise
        log.info(
            "tool_finished",
            tool=fn.__name__,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
            result_preview=str(result)[:120],
        )
        return result

    return wrapper