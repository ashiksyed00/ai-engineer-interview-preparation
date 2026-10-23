"""Runnable examples: sync vs async, gather, tasks, semaphores, timeouts, errors.

Network calls are simulated with sleeps, so this runs offline.
Requires Python 3.11+ (TaskGroup, asyncio.timeout).

Run:  python examples.py
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

DELAY = 0.3  # seconds each fake API call "takes"


# ----------------------------------------------------------- fake API calls
def fetch_sync(name: str) -> str:
    time.sleep(DELAY)                       # blocks the whole program
    return f"result-{name}"


async def fetch(name: str, delay: float = DELAY) -> str:
    await asyncio.sleep(delay)              # yields control while "waiting on the network"
    return f"result-{name}"


async def flaky(name: str) -> str:
    await asyncio.sleep(0.05)
    if name == "bad":
        raise ConnectionError(f"{name} failed")
    return f"result-{name}"


# ------------------------------------------------------------ timing helper
class Stopwatch:
    def __enter__(self) -> Stopwatch:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.elapsed = time.perf_counter() - self.start


# ------------------------------------------------------------ demos
def sync_demo() -> None:
    with Stopwatch() as sw:
        results = [fetch_sync(n) for n in "abc"]
    print(f"sync, 3 calls:         {sw.elapsed:.2f}s  {results}")


async def sequential_await_demo() -> None:
    with Stopwatch() as sw:
        results = [await fetch(n) for n in "abc"]      # awaiting one by one = still sequential!
    print(f"async but sequential:  {sw.elapsed:.2f}s  {results}")


async def gather_demo() -> None:
    with Stopwatch() as sw:
        results = await asyncio.gather(*(fetch(n) for n in "abc"))   # run concurrently
    print(f"asyncio.gather:        {sw.elapsed:.2f}s  {results}")


async def task_group_demo() -> None:
    with Stopwatch() as sw:
        async with asyncio.TaskGroup() as tg:          # structured concurrency (3.11+)
            tasks = [tg.create_task(fetch(n)) for n in "abc"]
    print(f"TaskGroup:             {sw.elapsed:.2f}s  {[t.result() for t in tasks]}")


async def blocking_mistake_demo() -> None:
    async def bad_fetch(name: str) -> str:
        time.sleep(DELAY)                              # BLOCKING call inside async def
        return f"result-{name}"

    with Stopwatch() as sw:
        await asyncio.gather(*(bad_fetch(n) for n in "abc"))
    print(f"blocking inside async: {sw.elapsed:.2f}s  (gather can't help: no await point!)")


async def to_thread_demo() -> None:
    with Stopwatch() as sw:
        results = await asyncio.gather(*(asyncio.to_thread(fetch_sync, n) for n in "abc"))
    print(f"to_thread (sync code): {sw.elapsed:.2f}s  {results}")


async def semaphore_demo() -> None:
    sem = asyncio.Semaphore(2)                         # at most 2 calls in flight

    async def limited(name: str) -> str:
        async with sem:
            return await fetch(name)

    with Stopwatch() as sw:
        await asyncio.gather(*(limited(str(i)) for i in range(6)))
    print(f"6 calls, limit 2:      {sw.elapsed:.2f}s  (3 waves x {DELAY}s)")


async def timeout_demo() -> None:
    try:
        async with asyncio.timeout(0.1):               # 3.11+
            await fetch("slow", delay=1.0)
    except TimeoutError:
        print("timeout:               TimeoutError caught after 0.1s")


async def error_demo() -> None:
    results = await asyncio.gather(flaky("a"), flaky("bad"), flaky("c"), return_exceptions=True)
    for r in results:
        print("  ", "ERROR" if isinstance(r, Exception) else "ok   ", r)


async def stream_tokens() -> AsyncIterator[str]:
    """Async generator: like LLM token streaming."""
    for token in ["Hel", "lo", ",", " world"]:
        await asyncio.sleep(0.02)
        yield token


async def stream_demo() -> None:
    chunks = [tok async for tok in stream_tokens()]
    print("stream:                ", "".join(chunks))


async def main() -> None:
    await sequential_await_demo()
    await gather_demo()
    await task_group_demo()
    await blocking_mistake_demo()
    await to_thread_demo()
    await semaphore_demo()
    await timeout_demo()
    print("error handling with return_exceptions=True:")
    await error_demo()
    await stream_demo()


if __name__ == "__main__":
    sync_demo()
    asyncio.run(main())              # the single entry point into async code