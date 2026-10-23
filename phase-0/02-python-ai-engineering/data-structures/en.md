# Python · Core Data Structures

> **Goal:** Reason confidently about lists, tuples, sets, dictionaries, iterators, and generators, and pick the right one for the job.

Runnable demo of everything below: [`examples.py`](./examples.py)

```bash
python examples.py
```

## Contents

1. [Cheat sheet: which one do I use?](#1-cheat-sheet-which-one-do-i-use)
2. [Lists](#2-lists)
3. [Tuples](#3-tuples)
4. [Sets](#4-sets)
5. [Dictionaries](#5-dictionaries)
6. [Iterators & generators](#6-iterators--generators)
7. [Useful extras: `collections`](#7-useful-extras-collections)
8. [Exercise](#8-exercise)
9. [Self-check](#9-self-check)

---

## 1. Cheat sheet: which one do I use?

| Structure | Ordered | Mutable | Duplicates | Use it for |
|-----------|:------:|:-------:|:----------:|------------|
| `list` | Yes | Yes | Yes | A sequence you add to, sort, or loop over |
| `tuple` | Yes | **No** | Yes | A fixed record (`(x, y)`), dict keys, returning multiple values |
| `set` | No | Yes | **No** | Uniqueness, fast membership tests, set math |
| `dict` | Yes (insertion) | Yes | Keys unique | Lookup by key, counting, grouping, JSON-like data |
| generator | n/a | n/a | n/a | Large or infinite streams, processed lazily |

### Time complexity (Big-O) you should remember

| Operation | list | set / dict | deque |
|-----------|:----:|:----------:|:-----:|
| Index `x[i]` | O(1) | n/a | O(n) middle |
| Append at end | O(1) | n/a | O(1) |
| Insert/pop at **front** | **O(n)** | n/a | **O(1)** |
| `x in collection` | **O(n)** | **O(1)** | O(n) |
| Lookup by key | n/a | **O(1)** | n/a |
| Sort | O(n log n) | n/a | n/a |

**Decision shortcuts**
- Need to check "is it in there?" repeatedly → **set** (or dict).
- Need to look something up by name/ID → **dict**.
- Data shouldn't change, or needs to be a dict key → **tuple**.
- Need order + changes → **list**.
- Data too big for memory, or infinite → **generator**.
- Need a queue (pop from front) → **`collections.deque`**.

---

## 2. Lists

```python
nums = [5, 2, 9, 1]
nums.append(7)              # add to end
nums.extend([3, 4])         # add many
nums.insert(0, 10)          # add at index (O(n))
nums.pop()                  # remove & return last
nums.remove(9)              # remove first matching value
nums.sort()                 # in place, returns None
sorted(nums, reverse=True)  # new list, original untouched

nums[1:3]    # slice [start:stop)
nums[::-1]   # reversed copy
nums[-1]     # last item
```

Sorting with a key:

```python
people = [("Ada", 36), ("Bob", 25)]
people.sort(key=lambda p: p[1])           # sort by age
```

### Gotchas (interview favourites)

```python
# 1. Assignment does not copy
a = [1, 2, 3]
b = a            # same object
c = a.copy()     # new list (or list(a), or a[:])

# 2. Shallow copy shares nested objects
import copy
deep = copy.deepcopy(nested)    # fully independent

# 3. Repeating mutable items shares them
bad  = [[0] * 2] * 2                     # both rows are the SAME list
good = [[0] * 2 for _ in range(2)]       # independent rows

# 4. Never modify a list while looping over it; build a new one
evens = [x for x in nums if x % 2 == 0]
```

---

## 3. Tuples

Immutable sequences. Think "record", not "collection".

```python
point = (3, 4)
x, y = point                    # unpacking
def min_max(xs): return min(xs), max(xs)   # returns a tuple
lo, hi = min_max([3, 1, 2])

single = (1,)                   # the comma makes it a tuple, not the parentheses
```

Because tuples are **hashable**, they work as dict keys and set members:

```python
grid = {(0, 0): "start", (2, 3): "goal"}
```

Prefer a **`NamedTuple`** (or dataclass) when fields need names:

```python
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float

p = Point(1.0, 2.0)
p.x   # readable, unlike p[0]
```

---

## 4. Sets

Unordered collections of **unique, hashable** items.

```python
a, b = {1, 2, 3, 4}, {3, 4, 5}
a | b       # union          {1, 2, 3, 4, 5}
a & b       # intersection   {3, 4}
a - b       # difference     {1, 2}
a ^ b       # symmetric diff {1, 2, 5}
a <= b      # subset?

s = set()          # NOT {}  (that creates an empty dict)
s.add(1)
s.discard(99)      # no error if missing (remove() raises KeyError)
```

**Why sets matter:** membership is O(1) vs O(n) for lists. In `examples.py`, 200 lookups in a 100k list take ~0.1s vs ~0.00001s with a set.

```python
# Deduplicate (order NOT preserved)
unique = list(set(items))
# Deduplicate and keep order
unique = list(dict.fromkeys(items))

# Common use: filter against a blocklist
banned = {"spam", "scam"}
clean = [w for w in words if w not in banned]
```

Set items must be hashable: lists and dicts can't go in a set, but tuples can.

---

## 5. Dictionaries

Key → value mapping. Insertion-ordered (Python 3.7+). Keys must be hashable.

```python
user = {"name": "Ada", "age": 36}

user["name"]                    # KeyError if missing
user.get("email", "n/a")        # safe lookup with default
user.setdefault("tags", [])     # insert default if missing, return value
user.pop("age", None)           # remove, with default
"name" in user                  # key membership, O(1)

for key, value in user.items():  # iterate pairs
    ...
list(user.keys()); list(user.values())

merged = user | {"age": 37}      # merge, right side wins (3.9+)
user |= {"city": "London"}       # update in place
inverted = {v: k for k, v in user.items()}   # dict comprehension
```

### Counting and grouping (very common)

```python
from collections import Counter, defaultdict

Counter("banana").most_common(2)      # [('a', 3), ('n', 2)]

groups = defaultdict(list)
for word in words:
    groups[len(word)].append(word)    # no key-exists check needed
```

### Nested data (JSON-style)

```python
config = {"model": {"name": "gpt", "params": {"temp": 0.7}}}
temp = config.get("model", {}).get("params", {}).get("temp", 1.0)
```

---

## 6. Iterators & generators

### Iterable vs. iterator

- **Iterable:** anything you can loop over (list, str, dict, file). It has `__iter__`.
- **Iterator:** an object that produces the next item with `__next__` and raises `StopIteration` when done.

```python
it = iter([10, 20])
next(it)   # 10
next(it)   # 20
next(it)   # StopIteration
```

A `for` loop is just: call `iter()`, then `next()` until `StopIteration`.

### Generators: the easy way to write iterators

A function with `yield` returns a generator. It computes **one value at a time**, pausing between them.

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

list(countdown(3))      # [3, 2, 1]

def fib():              # infinite, and perfectly safe because it's lazy
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

from itertools import islice
list(islice(fib(), 10))  # first 10 values
```

**Generator expression** (like a list comprehension, but lazy):

```python
total = sum(x * x for x in range(1_000_000))   # no giant list in memory
```

### Why you care (AI engineering)

- Stream huge files/datasets line by line without loading everything.
- Yield **batches** for training or API calls.
- LLM **streaming** responses are consumed with `for chunk in stream:`.

```python
def batches(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]

def read_lines(path):
    with open(path) as f:
        for line in f:           # file objects are lazy iterators
            yield line.strip()
```

### Gotchas

```python
gen = (x * x for x in range(3))
list(gen)   # [0, 1, 4]
list(gen)   # []   generators are single-use!
```

| Use a **list** when… | Use a **generator** when… |
|----------------------|---------------------------|
| You need indexing, `len()`, or multiple passes | You need one pass |
| Data is small | Data is large or infinite |

---

## 7. Useful extras: `collections`

```python
from collections import deque

q = deque(maxlen=3)      # sliding window: old items fall off
for i in range(5):
    q.append(i)          # deque([2, 3, 4], maxlen=3)

q.appendleft(99)         # O(1) at both ends
q.popleft()              # O(1), ideal for queues / BFS
```

Also worth knowing: `Counter`, `defaultdict`, `namedtuple`, and `heapq` (priority queue).

---

## 8. Exercise

Create `exercises.py` in this folder:

1. `dedupe(items)` returns unique items **preserving order**.
2. `word_freq(text)` returns the top 5 words (use `Counter`).
3. `group_by_length(words)` returns `dict[int, list[str]]` (use `defaultdict`).
4. `common_items(a, b)` returns items present in both lists (use sets).
5. `batches(items, size)` is a generator yielding chunks.
6. `read_large_file(path)` is a generator yielding one stripped line at a time.
7. Predict the output before running:

```python
x = [[1, 2]] * 2
x[0].append(3)
print(x)
```

Stretch: time `item in list` vs. `item in set` for 1 million items using `time.perf_counter()`.

---

## 9. Self-check

- [ ] I can explain list vs. tuple vs. set vs. dict in one sentence each
- [ ] I know why `in` on a set is fast and on a list is slow
- [ ] I can explain alias vs. shallow copy vs. deep copy
- [ ] I know which objects are hashable and why that matters
- [ ] I use `.get()`, `Counter`, and `defaultdict` instead of manual key checks
- [ ] I can explain the difference between an iterable, an iterator, and a generator
- [ ] I know generators are lazy and single-use
- [ ] I reach for `deque` when I need a queue
