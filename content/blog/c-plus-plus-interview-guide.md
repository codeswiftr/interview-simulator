---
title: "C++ Interview Guide: Memory Management, STL, and Modern C++20 Features"
description: "A comprehensive guide to C++ interviews for software engineers — covering memory management fundamentals, smart pointers, STL containers, move semantics, templates, and modern C++20 features that interviewers actually test."
date: "2026-03-20"
category: "Programming Languages"
---

# C++ Interview Guide: Memory Management, STL, and Modern C++20 Features

C++ interviews are uniquely demanding because the language rewards deep knowledge. You can write C++ for years and still find yourself surprised by undefined behavior, object lifetime issues, or template instantiation rules. This guide focuses on what interviewers actually test and what understanding you need to answer confidently.

## Memory Management: The Foundation

C++ gives you manual control over memory, which means interviews test whether you actually understand what's happening.

### Stack vs Heap

Stack allocation is automatic and fast — the compiler manages it via the stack pointer. Objects on the stack have automatic storage duration: they're destroyed when they go out of scope. Stack size is limited (~1-8 MB typically on Linux).

Heap allocation (`new`/`delete`) is manual. You control when objects are created and destroyed. Incorrect management leads to:
- **Memory leaks:** Allocated memory never freed
- **Dangling pointers:** Using a pointer after the pointed-to object is freed
- **Double free:** Calling `delete` twice on the same pointer (undefined behavior)
- **Buffer overflow:** Writing past the end of an allocated block

### Smart Pointers (Modern C++)

The correct answer to "how do you manage heap memory?" is: use smart pointers, avoid raw `new`/`delete`.

**`std::unique_ptr<T>`** — sole ownership. When the unique_ptr goes out of scope, the object is destroyed. Zero overhead over raw pointer.

```cpp
// Prefer make_unique over new
auto ptr = std::make_unique<Widget>(42);
// ptr is destroyed when it goes out of scope
// Can transfer ownership with std::move
auto ptr2 = std::move(ptr);  // ptr is now null
```

**`std::shared_ptr<T>`** — shared ownership via reference counting. Object destroyed when last shared_ptr goes out of scope. Small overhead: reference count allocation, atomic increment/decrement.

```cpp
auto sp1 = std::make_shared<Widget>(42);
auto sp2 = sp1;  // refcount = 2
// Object destroyed when both sp1 and sp2 go out of scope
```

**`std::weak_ptr<T>`** — non-owning observer to a shared_ptr. Does not increment refcount. Use to break circular references (a common cause of shared_ptr memory leaks).

```cpp
// Tree node with parent pointer — use weak_ptr to avoid cycle
struct Node {
    std::shared_ptr<Node> left, right;
    std::weak_ptr<Node> parent;  // weak to avoid cycle
};
```

**Interview question:** "What's the difference between unique_ptr and shared_ptr?" Beyond ownership semantics, unique_ptr has zero overhead; shared_ptr has the reference count allocation and atomic operations. For single-owner scenarios, always prefer unique_ptr.

## Move Semantics: C++11's Most Important Feature

Before C++11, returning large objects from functions caused expensive copies. Move semantics allow "stealing" resources from temporary objects (rvalues).

```cpp
std::vector<int> create_large_vector() {
    std::vector<int> v(1000000);
    // ...fill v...
    return v;  // Move semantics: no copy of 1M elements
}

auto vec = create_large_vector();  // Move, not copy
```

**Rvalue references (`T&&`)** bind to temporaries. The move constructor and move assignment operator "steal" resources:

```cpp
class Buffer {
    std::unique_ptr<char[]> data;
    size_t size;
public:
    // Move constructor: steal data from other
    Buffer(Buffer&& other) noexcept
        : data(std::move(other.data)), size(other.size) {
        other.size = 0;  // Leave other in valid but empty state
    }
};
```

**`std::move` doesn't move anything** — it's a cast to rvalue reference that enables the move constructor/assignment to be called. The actual "moving" is done by the constructor/assignment operator.

**The Rule of Five (modern):** If you define any of destructor, copy constructor, copy assignment, move constructor, move assignment — define all five. Or better: design your class so you don't need to define any (Rule of Zero) by using smart pointers as members.

## STL Containers: Choosing Correctly

| Container | Underlying Structure | Access | Insert/Delete | Use When |
|-----------|---------------------|--------|---------------|----------|
| `vector<T>` | Dynamic array | O(1) random | O(1) amortized end; O(n) middle | Default sequence container |
| `list<T>` | Doubly linked list | O(n) | O(1) anywhere | Frequent mid-sequence insertion |
| `deque<T>` | Chunked array | O(1) random | O(1) at ends | Queue/stack with random access |
| `unordered_map<K,V>` | Hash table | O(1) avg | O(1) avg | Key-value lookup, no ordering needed |
| `map<K,V>` | Red-black tree | O(log n) | O(log n) | Ordered key-value, range queries |
| `set<T>` | Red-black tree | O(log n) | O(log n) | Unique elements, ordered |
| `unordered_set<T>` | Hash table | O(1) avg | O(1) avg | Unique elements, no ordering |
| `priority_queue<T>` | Heap | O(1) top | O(log n) push/pop | Min/max heap operations |

**Interview gotcha:** `unordered_map` has O(1) average but O(n) worst-case due to hash collisions. In adversarial inputs (or DoS scenarios), this matters. `map` has guaranteed O(log n).

**`vector` vs `array`:** `std::array<T, N>` is a fixed-size stack-allocated container with zero overhead over a raw array. Use it when size is known at compile time.

## Templates and Generic Programming

Templates allow writing type-generic code without runtime overhead (the compiler generates type-specific code at compile time).

```cpp
// Function template
template<typename T>
T max_of(T a, T b) {
    return a > b ? a : b;
}

// Class template
template<typename T>
class Stack {
    std::vector<T> data;
public:
    void push(T val) { data.push_back(std::move(val)); }
    T pop() {
        T val = std::move(data.back());
        data.pop_back();
        return val;
    }
};
```

**SFINAE (Substitution Failure Is Not An Error):** Templates are instantiated by substituting types. If substitution fails (e.g., T doesn't have a required method), that template overload is silently dropped rather than causing an error. This enables template specialization based on type properties.

**C++20 Concepts** replace complex SFINAE with readable constraints:

```cpp
// C++20: require T to support operator<
template<typename T>
requires std::totally_ordered<T>
T max_of(T a, T b) {
    return a > b ? a : b;
}

// Abbreviated form
auto max_of(std::totally_ordered auto a, std::totally_ordered auto b) {
    return a > b ? a : b;
}
```

## Modern C++20 Features

**Ranges library:** Composable, lazy sequence transformations:

```cpp
#include <ranges>
#include <algorithm>

std::vector<int> nums = {1, 2, 3, 4, 5, 6};
// Filter even numbers, multiply by 2 — lazy, no intermediate vector
auto result = nums 
    | std::views::filter([](int n) { return n % 2 == 0; })
    | std::views::transform([](int n) { return n * 2; });
// result is a view, not materialized until iterated
```

**Coroutines:** Suspend/resume execution for generators and async code:

```cpp
#include <coroutine>
#include <generator>  // C++23, but concept is C++20

std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;  // Suspend and yield value
        auto next = a + b;
        a = b;
        b = next;
    }
}
```

**`std::span<T>`** — non-owning view over contiguous data. Replace `(T* ptr, size_t len)` function parameters:

```cpp
void process(std::span<const int> data) {
    for (int val : data) { /* ... */ }
}
// Works with vector, array, raw pointer+size
```

## Common Interview Questions and Answers

**"What is undefined behavior?"** C++ has operations that the standard leaves intentionally undefined (dereferencing null, signed integer overflow, accessing freed memory). The compiler assumes UB never occurs and may optimize code in ways that produce surprising results. Sanitizers (ASAN, UBsan) detect UB at runtime.

**"Explain the copy-and-swap idiom."** Implement operator= using the copy constructor and swap. Handles self-assignment correctly, provides strong exception safety, and eliminates code duplication.

**"What's the difference between `const T*`, `T* const`, and `const T* const`?"** 
- `const T*` — pointer to const T (can't modify through pointer, can reassign pointer)
- `T* const` — const pointer to T (can modify T, can't reassign pointer)
- `const T* const` — const pointer to const T (neither)

**"When would you use `virtual` functions and when wouldn't you?"** Virtual functions enable runtime polymorphism via vtable lookup — tiny overhead per call, but functions can't be inlined. For hot paths, prefer templates (compile-time polymorphism). For extensible hierarchies where types aren't known at compile time, use virtual.

C++ interviews reward engineers who understand the "why" — why move semantics were added, why smart pointers solve the problems they solve, why undefined behavior exists in a performance-focused language. That depth of understanding is what separates strong C++ candidates.
