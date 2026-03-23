---
title: "Functional Programming Interview Guide: Pure Functions, Immutability, and FP Patterns"
description: "Functional programming concepts for coding interviews — pure functions, higher-order functions, map/filter/reduce, monads, currying, and when FP patterns improve code."
date: "2026-03-20"
category: "Programming Languages"
---

# Functional Programming Interview Guide: Pure Functions, Immutability, and FP Patterns

Functional programming concepts appear in modern interviews even when you're not applying to a Haskell or Clojure role. React (with hooks), Redux, Spark, and many modern Python codebases heavily employ functional patterns. Understanding these concepts makes you a better engineer regardless of language.

## Pure Functions: The Foundation

A pure function has two properties: (1) given the same inputs, always returns the same output; (2) has no side effects (doesn't modify external state, doesn't do I/O).

```python
# Pure function
def add(a, b):
    return a + b

# Impure: depends on external state
total = 0
def add_to_total(x):
    global total
    total += x  # Side effect: modifies external state
    return total
```

Pure functions are: testable (no setup/teardown, just input → output), composable (chain them without worrying about hidden state), parallelizable (no shared state means no race conditions), memoizable (same inputs always produce same outputs — cache freely).

## Higher-Order Functions

A function that takes functions as arguments or returns a function. This is the core mechanism of functional composition.

**Map:** Transform each element.
```python
# Imperative
result = []
for x in numbers:
    result.append(x * 2)

# Functional
result = list(map(lambda x: x * 2, numbers))
# Or more Pythonically:
result = [x * 2 for x in numbers]
```

**Filter:** Select elements matching a predicate.
```python
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

**Reduce:** Fold a collection into a single value.
```python
from functools import reduce
total = reduce(lambda acc, x: acc + x, numbers, 0)
```

Composing these: instead of a nested loop with conditions, you can chain `filter → map → reduce` in a pipeline that's readable and testable in pieces.

## Immutability

Immutable data structures are never modified — operations return new structures with the changes applied. This makes reasoning about state trivial: you know an immutable value never changes, so you don't need to track who might have modified it.

In Python, prefer tuples over lists when modification isn't needed. In JavaScript, `Object.freeze()` or the spread operator for creating modified copies:
```javascript
// Instead of:
user.name = 'Alice';

// Immutable update:
const updatedUser = { ...user, name: 'Alice' };
```

Redux enforces this pattern: the state is immutable, and reducers return new state objects. This enables time-travel debugging (you have every past state).

## Currying and Partial Application

Currying transforms a function of multiple arguments into a sequence of single-argument functions.

```python
# Normal function
def add(a, b):
    return a + b

# Curried
def curried_add(a):
    def inner(b):
        return a + b
    return inner

add5 = curried_add(5)
add5(3)  # 8
add5(10) # 15
```

Partial application: fix some arguments, return a function expecting the rest. Python's `functools.partial` does this. Useful for creating specialized versions of generic functions.

## Closures

A closure is a function that captures variables from its enclosing scope. In Python, JavaScript, and most modern languages, closures are fundamental.

```python
def make_counter(start=0):
    count = start
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

counter = make_counter()
counter()  # 1
counter()  # 2
```

Interviewers test closures because they frequently cause bugs (especially in JavaScript — the classic loop + setTimeout bug). Understanding what variables a closure captures, and when it captures them, is essential.

## Monads (Practical Introduction)

Monads sound intimidating but you use them constantly. A monad is a design pattern for chaining operations that might fail or have effects, while keeping each step pure.

**Maybe/Option monad:** Represents a value that might be absent. Instead of null checks scattered everywhere, operations on Maybe automatically propagate None:
```python
from typing import Optional

def safe_divide(a: float, b: float) -> Optional[float]:
    return None if b == 0 else a / b

# Chaining without explicit null checks (in some languages):
result = (
    safe_divide(10, 2)    # Some(5.0)
    .map(lambda x: x + 1) # Some(6.0) 
    .map(lambda x: x * 2) # Some(12.0)
)
```

**Result/Either monad:** Represents success or failure. Rust's `Result<T, E>` is a monad — the `?` operator chains operations, propagating errors. This is why you should care about monads even in non-functional languages.

## FP Patterns in Real Codebases

**React Hooks:** `useState` and `useReducer` are functional state management. Reducers are pure functions: `(state, action) => newState`.

**Python data pipelines:** A pandas pipeline with method chaining (`df.filter().groupby().agg()`) is functional composition.

**JavaScript array methods:** `array.filter().map().reduce()` is pipeline composition over data.

**Immutable update patterns:** React state updates, Redux reducers, Immer library — all enforce immutable updates.

The interview insight: when you see map/filter/reduce in a problem, that's often a signal that the functional pattern produces cleaner code than imperative loops. Recognizing and applying these patterns fluently signals programming maturity.
