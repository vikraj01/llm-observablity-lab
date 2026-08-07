# LLM Observability Lab

A deliberately small LangGraph agent, instrumented four different ways, so the
observability layers can be compared on **identical code**. The agent never
changes between phases — only what watches it does.

See [comparison/](comparison/README.md) for the LangSmith vs Langfuse verdict.

---

## The agent under test

One ReAct-style LangGraph loop ([src/agent/graph.py](src/agent/graph.py)):

```
START -> agent -> (tool calls?) -> tools -> agent -> ... -> END
              |
              +-- no tool calls --> END
```

Three tools ([src/agent/tools.py](src/agent/tools.py)), each chosen to produce a
different *shape* of trace:

| Tool | What it does | Why it's here |
|---|---|---|
| `calculator` | AST-walks a arithmetic expression (no `eval`) | Fast, always succeeds — the boring baseline |
| `get_weather` | Fake data, **fails 20% of the time on purpose** | Generates errors worth tracing |
| `search_docs` | Tiny RAG over `docs/*.md` via `InMemoryVectorStore` | Adds an embedding call + a slow cold start |

The model is `gpt-4o` behind an **Azure AI Foundry** OpenAI-compatible endpoint,
reached through `langchain-openai` by pointing `base_url` at Foundry
([src/agent/llm.py](src/agent/llm.py)).

### The 20% failure is intentional

```python
# tools.py:83
if random.random() < 0.2:
    raise RuntimeError(f"weather service timeout for city={city!r}")
```

This is the single most confusing thing about the lab, so: **it is not a bug.**
Measured over 40 calls it fires at exactly 20%. Two failures in a row is a 4%
coincidence and will happen to you. A real timeout would burn seconds; this one
shows `0.00s` latency in the trace, which is how you tell them apart.

---

## Quick start

Three commands and one file to fill in.

```bash
uv sync                   # install dependencies
cp .env.example .env      # then open .env and paste your keys
uv run python -m src.agent "what's the weather in Chennai and what's 100/7?"
```

Only the four `LLM_*` variables are required. Leave the LangSmith and Langfuse
blocks empty and Phases 1 and 2 still work; fill them in when you want tracing.

| Variable | Required | What it is |
|---|:---:|---|
| `LLM_BASE_URL` | yes | Any OpenAI-compatible endpoint. Built against Azure AI Foundry, but `https://api.openai.com/v1` works too. |
| `LLM_API_KEY` | yes | Key for that endpoint |
| `LLM_CHAT_MODEL` | yes | e.g. `gpt-4o` |
| `LLM_EMBEDDING_MODEL` | yes | e.g. `text-embedding-3-small`, used by `search_docs` |
| `LANGSMITH_TRACING` | no | Set to `true` to turn on Phase 3 tracing |
| `LANGSMITH_API_KEY` | no | From smith.langchain.com |
| `LANGFUSE_HOST` | no | `http://localhost:3000` once the Docker stack is up |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | no | Langfuse Settings, API Keys |

> [!NOTE]
> If you got this as a zip rather than a git clone, it is the same thing minus
> `.venv/`, `.git/` and the Langfuse server clone. `uv sync` rebuilds the
> environment from `uv.lock`, so you get identical package versions.

`load_dotenv()` must run **before** any client is constructed, which is why every
entry point calls it at import time above the other imports with `# noqa: E402`.
That is deliberate, not lint debt.

### Self-hosting Langfuse

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse && docker compose up -d
```

Six containers. Host ports claimed: **3000** web, 3030 worker, **5432** postgres,
8123 + 9000 clickhouse, 9090 + 9091 minio, 6379 redis.

> [!NOTE]
> Postgres on `5432` is the one that collides in practice — any other local
> Postgres (in this environment, the `scout` project's `scout-db-1`) will make
> `docker compose up` abort with `Bind for 127.0.0.1:5432 failed: port is
> already allocated`. Either stop the other container, or drop a
> `docker-compose.override.yml` into the clone remapping the host side only
> (Langfuse's own services reach Postgres over the compose network as
> `postgres:5432`, so remapping the host port breaks nothing):
>
> ```yaml
> services:
>   postgres:
>     ports: !override
>       - 127.0.0.1:5433:5432
> ```
>
> The `!override` tag matters — without it Compose *appends* to the ports list
> and you keep the conflicting 5432 binding.

The clone is ~261 MB and currently sits untracked inside this repo. Consider
adding `langfuse/` to `.gitignore` or moving it outside the project.

---

## Phases

Each phase is one commit and adds exactly one layer.

### Phase 1 — baseline agent

```bash
uv run python -m src.agent "what's the weather in Chennai and what's 100/7?"
```

No instrumentation. `print()` and a full message dump. The point is to feel the
absence: when the weather tool fails you get a 60-line LangGraph traceback whose
only useful line is the last one.

### Phase 2 — structured logging (`structlog`)

[src/obs_logging/](src/obs_logging/) — one `configure_logging()` and one
`@logged_tool` decorator applied *under* `@tool`.

Two ideas worth stealing:

- **JSON events, not prose.** `tool_failed` carries `tool`, `duration_ms`, `error`
  as fields you can filter on.
- **Context propagation by hand.** A single `run_id` is bound once per invocation
  via `structlog.contextvars`, and every line emitted anywhere in the run carries
  it automatically. This is a hand-rolled version of what OpenTelemetry calls
  "context" — worth doing once so you appreciate why OTel exists.

> [!NOTE]
> `configure_logging()` is only called from [src/agent/__main__.py](src/agent/__main__.py).
> The Phase 3 and Phase 4 entry points never call it, so they fall back to
> structlog's default pretty console renderer. The "logs are JSON" property only
> holds for `python -m src.agent`.

### Phase 3 — LangSmith (hosted)

```bash
uv run python -m src.obs_langsmith.tagged_run "what's 23*7?"   # tags + metadata
uv run python -m src.obs_langsmith.dataset                     # create golden set (idempotent)
uv run python -m src.obs_langsmith.evaluate                    # LLM-as-judge experiment
```

Tracing is **ambient**: set `LANGSMITH_TRACING=true` and every LangChain/LangGraph
call is captured with zero code changes.

### Phase 4 — Langfuse (self-hosted)

```bash
uv run python -m src.obs_langfuse.traced_run "what's the weather in Chennai and what's 100/7?"
uv run python -m src.obs_langfuse.dataset      # mirrors the SAME 4 examples
uv run python -m src.obs_langfuse.evaluate     # same agent, same judge model
```

Tracing is **explicit**: you pass a `CallbackHandler()` per invocation. More
typing, but nothing is captured unless you asked for it.

[src/obs_langfuse/dataset.py](src/obs_langfuse/dataset.py) imports `EXAMPLES`
directly from the LangSmith module, so both platforms are graded on byte-identical
cases. That's what makes the comparison in [comparison/](comparison/README.md) fair.

> [!TIP]
> With both sets of env vars populated, a single run lands in **both** tools
> simultaneously. Worth doing once — same trace, two UIs, side by side.

---

## Reading traces in the Langfuse UI

The default Tracing table lists **observations** (one row per span), so eight runs
show up as ~68 rows and the same timestamp repeats down the page. To get one row
per run, either:

- filter `Is Root Observation = True`, or
- switch to the **Traces** table, or
- use **Sessions** — [traced_run.py](src/obs_langfuse/traced_run.py) already sets
  `langfuse_session_id`, which threads runs together.

The search bar takes `level:ERROR` to isolate the runs where the weather dice
came up bad.

> [!NOTE]
> `langfuse_session_id` is hardcoded to `"session-001"` and `langfuse_user_id` to
> `"vikash"`, so every run ever executed piles into one session. Fine for a lab;
> for anything real, generate one per conversation (the `run_id` already built in
> [__main__.py](src/agent/__main__.py) is the natural candidate).

---

## Known rough edges

Things confirmed by running the code, not by reading it. None are fixed except
where noted.

| Where | Issue |
|---|---|
| `.env.example` | **Fixed.** Used to declare `SCOUT_LLM_*` while the code read `LLM_*`, which guaranteed a `KeyError: 'LLM_CHAT_MODEL'` on the first run for anyone who copied it. |
| `pyproject.toml` | `langsmith` is not an explicit dependency — it works only because `langchain` pulls it in transitively. Phase 3 would break on a dependency bump. |
| [graph.py:60](src/agent/graph.py#L60) | `ToolNode(ALL_TOOLS)` uses the default error handler, which only swallows `ToolInvocationError`. A tool raising in its *body* kills the whole process, so the 20% weather failure takes down the run — and the model never gets to honour the system prompt's "if a tool fails, tell the user honestly and retry at most once". Fix is `ToolNode(ALL_TOOLS, handle_tool_errors=True)`. |
| [obs_langsmith/evaluate.py:51](src/obs_langsmith/evaluate.py#L51) | `outputs["answer"]` is unguarded, so when the target fails the evaluator throws a *second*, cascading `KeyError('answer')`. See [comparison/02-evaluation.md](comparison/02-evaluation.md). |
| [traced_run.py:47](src/obs_langfuse/traced_run.py#L47) | `get_client().flush()` is unreachable if `graph.invoke()` raises. In practice traces still arrive — Langfuse 4.x rides on the OpenTelemetry SDK, which registers its own `atexit` flush — so the explicit call is belt-and-braces, not load-bearing. A `try/finally` would make the intent honest. |
| [obs_langfuse/dataset.py:24](src/obs_langfuse/dataset.py#L24) | **Fixed.** Called `create_dataset(dataset_name=...)`; the langfuse 4.14 signature is `create_dataset(name=...)`. Hard `TypeError`. Note `create_dataset_item(dataset_name=...)` *is* correct — the two differ. |
| `docker-compose` | Host port 5432 collides with any other local Postgres. See above. |

### Cold start

The first `search_docs` call embeds all five files in `docs/` and took **11.9s**;
subsequent calls in the same process took **1.4s**. The vector store is process-local
and rebuilt on every run — expect one slow item per experiment.

---

## Versions

Pinned at the time these notes were written and verified:

```
python 3.12          langgraph 1.2.10       langfuse 4.14.3 (server v4.6.0 OSS)
uv 0.11.26           langchain 1.3.14       langsmith 0.10.16
                     langchain-core 1.5.3   structlog 26.1.0
                     langchain-openai 1.4.1  openai 2.53.0
```

`langchain` (the umbrella package) is required by Langfuse — `langfuse.langchain.CallbackHandler`
imports it at module load, and `langchain-core` alone is not enough.
