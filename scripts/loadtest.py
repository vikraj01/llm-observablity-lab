"""Synthetic ingest benchmark against the local Langfuse.

Trace shape mirrors the real agent: 1 trace -> ~10 observations.
No LLM calls, so this measures Langfuse ingest, not model latency.
"""
import sys, time, pathlib
from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")
from langfuse import get_client

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
lf = get_client()
assert lf.auth_check(), "auth failed"

def one_trace(i: int):
    with lf.start_as_current_observation(name="obs-lab-agent", as_type="agent",
                                         input={"q": f"load test {i}"}) as root:
        for turn in range(2):
            with lf.start_as_current_observation(name="agent", as_type="chain"):
                with lf.start_as_current_observation(
                        name="ChatOpenAI", as_type="generation", model="gpt-4o",
                        input=[{"role": "user", "content": f"load test {i} turn {turn}"}]) as gen:
                    gen.update(output={"content": "ok"},
                               usage_details={"input": 270, "output": 48})
                with lf.start_as_current_observation(name="should_continue", as_type="chain"):
                    pass
        with lf.start_as_current_observation(name="tools", as_type="chain"):
            with lf.start_as_current_observation(name="get_weather", as_type="tool",
                                                 input={"city": "Chennai"}) as t:
                t.update(output="Chennai: 22C, humid")
            with lf.start_as_current_observation(name="calculator", as_type="tool",
                                                 input={"expression": "100/7"}) as t:
                t.update(output="14.2857")
        root.update(output={"answer": "done"})

print(f"pushing {N} traces (~10 observations each = ~{N*10:,} observations)", flush=True)
t0 = time.perf_counter()
for i in range(N):
    one_trace(i)
    if (i + 1) % 250 == 0:
        el = time.perf_counter() - t0
        print(f"  {i+1:>5}/{N}  {(i+1)/el:7.1f} traces/s  ({(i+1)*10/el:8.0f} obs/s)", flush=True)
t_build = time.perf_counter() - t0
print(f"\nbuild+enqueue: {t_build:.1f}s -> {N/t_build:.1f} traces/s", flush=True)
print("flushing to server...", flush=True)
t1 = time.perf_counter(); lf.flush(); t_flush = time.perf_counter() - t1
total = t_build + t_flush
print(f"flush:         {t_flush:.1f}s")
print(f"TOTAL:         {total:.1f}s -> {N/total:.1f} traces/s, {N*10/total:.0f} observations/s")
