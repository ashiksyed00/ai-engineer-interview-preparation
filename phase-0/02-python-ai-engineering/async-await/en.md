# Python · Sync vs Async Execution

> **Goal:** Understand synchronous vs. asynchronous execution and use `async`/`await` to make many network/API calls concurrently without blocking.

Runnable demo of everything below (simulated API calls, works offline): [`examples.py`](./examples.py)

```bash
python examples.py        # needs Python 3.11+
```

Sample output (each fake call takes 0.3s):

```
sync, 3 calls:         0.90s
async but sequential:  0.90s
asyncio.gather:        0.30s
TaskGroup:             0.30s
blocking inside async: 0.90s   (gather can't help: no await point!)
to_thread (sync code): 0.30s
6 calls, limit 2:      0.90s   (3 waves x 0.3s)
```

## Contents

1. [Sync vs. async: the idea](#1-sync-vs-async-the-idea)
2. [`async` / `await` basics](#2-async--await-basics)
3. [Running things concurrently](#3-running-things-concurrently)
4. [Real HTTP calls with `httpx`](#4-real-http-calls-with-httpx)
5. [Controlling concurrency: limits, timeouts, errors](#5-controlling-concurrency-limits-timeouts-errors)
6. [Streaming with async generators](#6-streaming-with-async-generators)
7. [Pitfalls](#7-pitfalls)
8. [Async vs. threads vs. processes](#8-async-vs-threads-vs-processes)
9. [Exercise](#9-exercise)
10. [Self-check](#10-self-check)

---

## 1. Sync vs. async: the idea

**Synchronous:** one thing at a time. While waiting on a network response, your program sits idle.

```
sync:   [call A ......][call B ......][call C ......]      total = 3 x wait
async:  [call A ......]
        [call B ......]        (all waiting at the same time)
        [call C ......]        total = 1 x wait
```

**Key insight:** async doesn't make any single call faster. It lets you **overlap the waiting**. That's why it shines for **I/O-bound** work (HTTP/API calls, database queries, file/network I/O) and does nothing for **CPU-bound** work (number crunching).

**Why AI engineers care:** calling an LLM API takes seconds. 100 sync calls ≈ minutes; 100 concurrent calls ≈ seconds (within rate limits). Async is also how FastAPI, streaming responses, and agents handle many users at once.

**How it works:** a single-threaded **event loop** runs coroutines. When one hits `await`, it pauses and hands control back to the loop, which runs another coroutine that is ready.

---

## 2. `async` / `await` basics

```python
import asyncio

async def fetch(name: str) -> str:        # `async def` creates a coroutine function
    await asyncio.sleep(1)                # `await` = "pause me here, let others run"
    return f"result-{name}"

result = asyncio.run(fetch("a"))          # the entry point into async code
```

Rules:
- Calling `fetch("a")` does **not** run it. It returns a **coroutine object**. You must `await` it or schedule it.
- `await` is only allowed inside `async def`.
- Use `asyncio.run(main())` **once**, at the top level of your program.
- Only `await` things that are awaitable: coroutines, tasks, futures.
- In Jupyter notebooks, use top-level `await fetch("a")` directly (a loop is already running; `asyncio.run` fails there).

```python
fetch("a")              # coroutine object, nothing happened (RuntimeWarning: never awaited)
await fetch("a")        # actually runs
```

---

## 3. Running things concurrently

### The beginner trap: awaiting in a loop is still sequential

```python
# 0.9s: each await finishes before the next starts
results = [await fetch(n) for n in "abc"]
```

### `asyncio.gather`: run many, collect results in order

```python
results = await asyncio.gather(fetch("a"), fetch("b"), fetch("c"))     # 0.3s
results = await asyncio.gather(*(fetch(n) for n in names))             # from a list
```

### `TaskGroup` (3.11+): safer, "structured" concurrency

```python
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(fetch(n)) for n in names]
# leaving the block waits for all tasks; if one fails, the rest are cancelled
results = [t.result() for t in tasks]
```

### `create_task`: start now, await later

```python
task = asyncio.create_task(fetch("a"))      # starts running in the background
other_work = await fetch("b")
a_result = await task                       # collect it when needed
```

| Tool | Use when |
|------|----------|
| `await coro` | one thing, in sequence |
| `gather(...)` | many independent calls, want results in order |
| `TaskGroup` | many calls, want all-or-nothing cancellation (preferred in 3.11+) |
| `create_task` | fire a background job and continue |

---

## 4. Real HTTP calls with `httpx`

> This snippet needs `pip install httpx` and internet access, so it is **not** part of `examples.py` (and was not executed when writing these notes).

```python
import asyncio
import httpx

async def get_json(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url, timeout=10)
    response.raise_for_status()                 # raises on 4xx/5xx
    return response.json()

async def main() -> None:
    urls = [f"https://httpbin.org/delay/1?i={i}" for i in range(5)]
    async with httpx.AsyncClient() as client:   # reuse ONE client (connection pooling)
        results = await asyncio.gather(*(get_json(client, u) for u in urls))
    print(len(results))                          # ~1s total, not ~5s

asyncio.run(main())
```

Notes:
- Use an **async** library (`httpx.AsyncClient`, `aiohttp`). The classic `requests` library is **blocking**.
- Most LLM SDKs ship an async client (e.g. `AsyncOpenAI`, `AsyncAnthropic`) used the same way: `await client.<call>(...)`. Check the SDK docs for exact names.

---

## 5. Controlling concurrency: limits, timeouts, errors

### Limit concurrent calls (respect rate limits)

```python
sem = asyncio.Semaphore(5)                  # at most 5 in flight

async def limited(name: str) -> str:
    async with sem:
        return await fetch(name)

results = await asyncio.gather(*(limited(n) for n in names))
```

Firing 1,000 requests at once will hit rate limits (HTTP 429). Always cap concurrency.

### Timeouts

```python
try:
    async with asyncio.timeout(5):          # 3.11+
        result = await fetch("slow")
except TimeoutError:
    result = None
```

Or: `await asyncio.wait_for(fetch("slow"), timeout=5)`.

### Error handling

```python
# Default: first exception propagates out of gather()
# return_exceptions=True: failures come back as values, so one failure doesn't lose the rest
results = await asyncio.gather(*calls, return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        logger.warning("call failed: %s", r)
```

### Async retry with backoff

```python
async def retry(fn, attempts=3, base_delay=0.5):
    for attempt in range(attempts):
        try:
            return await fn()
        except (ConnectionError, TimeoutError):
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(base_delay * 2 ** attempt)   # 0.5s, 1s, 2s...
```

Use `await asyncio.sleep`, **never** `time.sleep`, inside async code.

---

## 6. Streaming with async generators

Streaming LLM output yields chunks as they arrive. The pattern is `async for`:

```python
async def stream_tokens():
    for token in ["Hel", "lo", ",", " world"]:
        await asyncio.sleep(0.02)
        yield token                          # `yield` inside `async def` = async generator

async def main():
    async for token in stream_tokens():
        print(token, end="", flush=True)

    # collect into a list
    chunks = [tok async for tok in stream_tokens()]
```

Related (generators are covered in [data-structures](../data-structures/README.md)): `async with` for async context managers (like `httpx.AsyncClient()`), and `async for` for async iterators.

---

## 7. Pitfalls

| Pitfall | Why it hurts | Fix |
|---------|--------------|-----|
| Calling blocking code (`time.sleep`, `requests.get`, heavy loops) in `async def` | Freezes the **entire** event loop. `gather` can't help (see the 0.90s demo line) | Use async libraries, or `await asyncio.to_thread(blocking_fn, ...)` |
| Awaiting in a loop | Sequential, not concurrent | `gather` / `TaskGroup` |
| Forgetting `await` | You get a coroutine object, and the work never runs | Look for `RuntimeWarning: coroutine ... was never awaited` |
| Unbounded concurrency | Rate limits, timeouts, memory blowup | `Semaphore` |
| Fire-and-forget `create_task` with no reference | Task can be garbage-collected mid-run; exceptions vanish | Keep a reference; prefer `TaskGroup` |
| `asyncio.run()` inside a running loop | `RuntimeError` | Use `await` (notebooks, FastAPI handlers) |
| Shared mutable state across tasks | Interleaving at each `await` can cause races | Keep tasks independent; use `asyncio.Lock` if needed |
| Swallowing `CancelledError` | Breaks timeouts and shutdown | Re-raise it (or don't catch bare `Exception` around awaits carelessly) |
| Using async for CPU-bound work | No speedup | Use `multiprocessing` / `ProcessPoolExecutor` |

Bridging sync code:

```python
result = await asyncio.to_thread(blocking_function, arg)    # run sync code in a worker thread
```

---

## 8. Async vs. threads vs. processes

| | **asyncio** | **threads** | **processes** |
|---|---|---|---|
| Best for | many I/O waits (APIs, sockets) | I/O with sync-only libraries | CPU-heavy work |
| Parallel CPU? | No | No (GIL) | **Yes** |
| Overhead | very low (thousands of tasks) | moderate | high |
| Switching | explicit, at `await` | OS decides, any time | OS |
| Python tool | `asyncio` | `ThreadPoolExecutor` | `ProcessPoolExecutor` |

**Rule of thumb:** waiting on the network → `asyncio`. Waiting on a sync-only library → threads (`to_thread`). Crunching numbers → processes.

The **GIL** (Global Interpreter Lock) lets only one thread run Python bytecode at a time, which is why threads don't speed up CPU work in standard CPython.

---

## 9. Exercise

Create `exercises.py` in this folder:

1. Write `async def fake_llm(prompt: str) -> str` that sleeps 0.5s and returns `f"answer to {prompt}"`.
2. Time 10 prompts called **sequentially** vs. with **`gather`**. Print both timings.
3. Add a `Semaphore(3)` and predict the total time before you run it (10 calls, 3 at a time, 0.5s each).
4. Make `fake_llm` raise `ConnectionError` for one prompt. Handle it with `return_exceptions=True` and print which prompts failed.
5. Wrap calls in `asyncio.timeout(0.3)` and watch them all time out.
6. Add the `retry` helper and make `fake_llm` fail the first two attempts for each prompt.
7. Write an async generator that streams the answer word by word, and print it with `async for`.
8. Stretch: replace `fake_llm` with a real `httpx.AsyncClient` call to a public API, and compare with the sync `requests` version.

---

## 10. Self-check

- [ ] I can explain why async speeds up I/O-bound work but not CPU-bound work
- [ ] I know calling an `async def` function returns a coroutine and does nothing until awaited
- [ ] I know `await` in a loop is sequential and `gather` / `TaskGroup` is concurrent
- [ ] I use `asyncio.run()` once, at the entry point
- [ ] I never call blocking code in `async def` (and know `to_thread` as the escape hatch)
- [ ] I cap concurrency with `Semaphore` and add timeouts and retries for API calls
- [ ] I can handle partial failures with `return_exceptions=True`
- [ ] I can read an `async for` / async generator for streaming
- [ ] I can choose between asyncio, threads, and processes for a given problem