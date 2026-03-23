---
title: "OCaml Language Interview Guide"
description: "Technical interview preparation for OCaml developer roles: the type system and type inference, algebraic data types and pattern matching, the module system, Jane Street's OCaml ecosystem, and what quantitative finance firms, formal verification tools, and functional programming organizations expect."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# OCaml Language Interview Guide

OCaml is a statically typed functional programming language with a powerful type inference engine, algebraic data types, a sophisticated module system, and efficient native code compilation. Its primary industrial deployment is at Jane Street — one of the world's largest quantitative trading firms — which uses OCaml across its entire trading infrastructure, risk systems, and tooling. The Jane Street OCaml ecosystem (Core, Async, Base, Incremental) is the de facto standard library for production OCaml. Beyond finance, OCaml is used in formal verification tools (Coq's extraction, CVC5), compilers (the ReasonML and Flow JavaScript type checker), and functional programming research.

## OCaml's Core Language

**Static type inference**: OCaml's type inference is the Hindley-Milner algorithm — the compiler infers types for the entire program without explicit annotations. A function `let f x = x + 1` is inferred as `int -> int` without writing the types. Type annotations are optional but used for documentation and occasionally required for polymorphic disambiguation.

**Algebraic data types**: OCaml's most expressive feature. Variant types define sum types: `type shape = Circle of float | Rectangle of float * float | Triangle of float * float * float`. Pattern matching on variants is exhaustive — the compiler warns if any case is unhandled. Record types define product types: `type point = { x: float; y: float }`. Recursive types enable linked lists, trees, and other recursive structures naturally.

**Pattern matching**: `match expr with | pattern -> expr | pattern -> expr`. Patterns can be nested, include guards (`when condition`), and match on tuples, records, variants, and literals. OCaml's pattern matching is exhaustive by default — missing cases generate compiler warnings (or errors with `-warn-error`).

**Immutability by default**: OCaml values are immutable by default. Mutable fields are explicitly marked with `mutable` in record definitions. Reference cells (`ref value`, `!ref` to read, `:= value` to set) provide mutable state when needed. This design makes programs easier to reason about while allowing mutation where genuinely necessary.

**First-class functions and currying**: OCaml is a functional language — functions are values. Multi-argument functions are curried by default: `let add x y = x + y` has type `int -> int -> int`. Partial application is natural: `let increment = add 1` gives a function of type `int -> int`.

## The Module System

OCaml's module system is the language's most distinctive feature at the architectural level. It's more powerful than most language's namespace/module systems:

**Modules as namespaces and types**: Modules group related values, types, and submodules. `List.map`, `String.length` — module-qualified names. `open List` makes the module's names available unqualified (used selectively to avoid shadowing).

**Signatures (interfaces)**: A module signature defines the public interface of a module — what types and values are exported and their types. Signatures enable information hiding (abstract types — callers can't see the implementation) and documentation.

**Functors**: Modules parametrized by other modules. `Map.Make(String)` creates a map module keyed by strings. Functors are OCaml's mechanism for generic programming with module-level abstraction. Jane Street's `Core.Map`, `Core.Set`, and `Core.Hash_set` are all functor-based.

**First-class modules**: OCaml allows storing modules in values and passing them as arguments. This enables patterns like heterogeneous collections of modules satisfying a common signature.

## Jane Street's OCaml Ecosystem

Jane Street has invested heavily in OCaml tooling and open-sources much of it:

**Base and Core**: Jane Street's standard library replacements. `Base` is a lightweight replacement for the OCaml standard library with consistent error handling (no silent exceptions from integer overflow, consistent `option`/`result` usage). `Core` extends Base with I/O, containers, and system interfaces.

**Async**: Jane Street's concurrent I/O library using a Deferred monad (similar to JavaScript's Promises). `Deferred.t` represents a value that will be available in the future. `let%bind result = some_async_operation in ...` for sequential async operations. `Deferred.all_unit` for parallel execution.

**Incremental**: A library for incremental computation — automatically recomputing only the parts of a computation that depend on changed inputs. Used at Jane Street for pricing computations that need to efficiently update when market data changes.

**Sexp (S-expressions)**: Jane Street uses S-expressions for serialization and configuration. `[@@deriving sexp]` automatically generates S-expression serialization for types. This is ubiquitous in Jane Street codebases.

## Interview Patterns at Jane Street

Jane Street's OCaml interviews are notoriously rigorous:

**Functional programming puzzles**: Given a data structure definition, write functions that process it. Pattern matching, recursive functions, higher-order functions.

**Type system questions**: "What's the type of this expression?" "Why does this program fail to type-check?" Genuine type inference reasoning, not just syntax knowledge.

**Module design**: "Design a module that implements this interface." Tests understanding of signatures, information hiding, and how to structure OCaml code.

**Incremental computation**: "Given this streaming data problem, how would you design an efficient incremental computation?" Relevant for trading system roles.

## Who Hires OCaml Engineers

**Jane Street**: The dominant employer. Jane Street actively recruits from functional programming communities and top universities. Their interview process includes OCaml coding challenges and is known for high difficulty.

**Formal verification and compilers**: Tarides (OCaml development company, maintains the OCaml compiler), Meta's Reason/ReScript team, the Flow type checker team, academic verification tool developers.

**Finance and trading**: A small number of HFT and quant firms following Jane Street's lead with OCaml.

OCaml engineering is a small, specialized market where expertise is genuinely rare. Engineers who demonstrate mastery of the type system, module system, and Jane Street's ecosystem are specifically sought by the few companies that use it heavily.
