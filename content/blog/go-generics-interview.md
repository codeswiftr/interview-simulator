---
title: "Go Generics Interview Guide: Type Parameters, Constraints, and Patterns"
description: "Go generics (1.18+) for senior engineering interviews — type parameters, interface constraints, comparable, ordered constraints, generic data structures, and when generics improve vs. hurt Go code."
date: "2026-03-20"
category: "Programming Languages"
---

# Go Generics Interview Guide: Type Parameters, Constraints, and Patterns

Go generics, introduced in Go 1.18, changed how idiomatic Go handles type-agnostic code. Senior Go engineers are expected to understand the type parameter system, know when generics improve code vs. when they add unnecessary complexity, and be able to use common patterns from the standard library. This guide covers what interviewers probe.

## Type Parameters: The Basic Syntax

```go
// Generic function: T is a type parameter
func Min[T constraints.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

// Generic struct: Stack of any type
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.items) == 0 {
        return zero, false
    }
    item := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return item, true
}
```

Type parameters appear in square brackets after the function/type name. `[T any]` constrains T to any type; `[T constraints.Ordered]` constrains T to types that support `<`, `>`, etc.

## Constraints: Defining What a Type Parameter Can Do

A constraint is an interface that specifies what methods and operators a type parameter must support.

**Built-in constraints:**
- `any`: No restrictions (same as `interface{}`)
- `comparable`: Supports `==` and `!=` (can be map keys)

**`golang.org/x/exp/constraints` package:**
- `constraints.Ordered`: Integer, float, or string — supports `<`, `>`, `<=`, `>=`
- `constraints.Integer`: All integer types
- `constraints.Float`: All float types

**Custom constraints:**

```go
// Constraint using a union
type Number interface {
    ~int | ~int32 | ~int64 | ~float32 | ~float64
}

// ~ means "or any type whose underlying type is"
// ~int includes type MyInt int, not just int

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}
```

The `~` prefix is important: `~int` matches both `int` and any named type with underlying type `int` (like `type Celsius float64`).

## Common Generic Patterns

**Map, Filter, Reduce for slices:**

```go
func Map[T, U any](slice []T, f func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = f(v)
    }
    return result
}

func Filter[T any](slice []T, pred func(T) bool) []T {
    var result []T
    for _, v := range slice {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

func Reduce[T, U any](slice []T, initial U, f func(U, T) U) U {
    result := initial
    for _, v := range slice {
        result = f(result, v)
    }
    return result
}

// Usage:
doubled := Map([]int{1, 2, 3}, func(n int) int { return n * 2 })
evens := Filter([]int{1, 2, 3, 4}, func(n int) bool { return n%2 == 0 })
sum := Reduce([]int{1, 2, 3}, 0, func(acc, n int) int { return acc + n })
```

**Generic set:**

```go
type Set[T comparable] map[T]struct{}

func NewSet[T comparable](items ...T) Set[T] {
    s := make(Set[T])
    for _, item := range items {
        s.Add(item)
    }
    return s
}

func (s Set[T]) Add(item T) { s[item] = struct{}{} }
func (s Set[T]) Contains(item T) bool { _, ok := s[item]; return ok }
func (s Set[T]) Remove(item T) { delete(s, item) }
```

**Note the `comparable` constraint:** Map keys must be comparable. Without this, the compiler rejects `map[T]struct{}`.

## When Generics Help vs. Hurt

**Generics help when:**
- Writing reusable data structures (stacks, queues, sets, trees)
- Writing algorithms that work on multiple types (sort, search, map/filter)
- Replacing repeated type-specific code with a single generic implementation

**Generics hurt when:**
- The behavior should differ per type — that's a signal for interfaces, not type parameters
- The function is only called with one type in practice — the generics cost isn't worth it
- You're tempted to use generics to avoid thinking about types — interface{} antipattern with extra syntax
- Code becomes harder to read without significant reuse benefit

**The interface vs. generics question:** Use interfaces when you want runtime polymorphism (different behavior per type, determined at runtime). Use generics when you want compile-time specialization (same behavior, any type, zero overhead).

```go
// This should be an interface (behavior varies by type):
type Animal interface {
    Sound() string
}

// This should be generic (same behavior, any type):
func Contains[T comparable](slice []T, item T) bool {
    for _, v := range slice {
        if v == item { return true }
    }
    return false
}
```

## Interview Questions on Generics

**"Why does Go require `comparable` for map keys?"** Type parameters with `any` constraint could be slices or maps, which aren't comparable in Go. The `comparable` constraint ensures the type supports `==` and `!=`, which maps require for key operations.

**"What's the difference between `any` and `interface{}`?"** They're identical — `any` is a type alias for `interface{}` introduced in Go 1.18. `any` is preferred stylistically in modern Go code.

**"When would you use a constraint with `~`?"** When you want to work with named types whose underlying type matches. `type Celsius float64` has underlying type `float64`. A function constrained to `~float64` accepts both `float64` and `Celsius`, enabling libraries to work transparently with domain-typed values.

**"What's a type inference limitation in Go generics?"** Go can infer type parameters for functions but not for types. `Map(slice, func)` infers T and U from arguments. But `Stack[int]{}` must specify the type explicitly — you can't write `Stack{}` and let Go infer it from usage.

## Standard Library Generic Functions (Go 1.21+)

The `slices` and `maps` packages in Go 1.21 provide generic operations:

```go
import "slices"
import "maps"

slices.Contains([]int{1,2,3}, 2)  // true
slices.Sort([]int{3,1,2})         // sorts in place
slices.Max([]int{1,5,3})          // 5
maps.Keys(map[string]int{"a":1})  // []string{"a"}
```

Knowing these exists signals familiarity with modern Go idioms in interviews.
