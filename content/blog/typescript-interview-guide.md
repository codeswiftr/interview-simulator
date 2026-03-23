---
title: "TypeScript Technical Interview Guide: Types, Generics, and Advanced Patterns"
description: "A deep-dive guide to TypeScript technical interviews. Covers the type system, generics, union and intersection types, type guards, utility types, conditional types, and strict mode—with company-specific guidance."
date: "2025-11-05"
category: "Technical Skills Guides"
---
# TypeScript Technical Interview Guide: Types, Generics, and Advanced Patterns

TypeScript has moved from a nice-to-have to a near-universal standard in frontend and full-stack engineering. Companies that adopted it early—Airbnb, Stripe, Slack, Microsoft—have made TypeScript fluency a baseline expectation for senior engineers. But TypeScript interviews reveal a wide capability gap: many candidates can write basic type annotations while struggling with generics, type narrowing, or the deeper features that make TypeScript genuinely powerful.

This guide covers what interviewers actually test, from type system fundamentals to advanced patterns, and which companies care most about TypeScript depth.

## Type System Fundamentals

The foundation of any TypeScript interview is understanding the type system's structure. TypeScript uses a **structural type system**, not a nominal one. Two types are compatible if they have the same shape—regardless of their declared names. This is a common gotcha for candidates coming from Java or C#, where types must explicitly declare compatibility.

**Primitive types and literal types** are baseline knowledge. Know the difference between `string` (any string) and `"foo"` (only that exact value), and how literal types combine to form union types. Interviewers often use literal type unions to model state machines, and expect candidates to recognize the pattern.

**`unknown` vs `any`** is a question that separates candidates who understand TypeScript's safety model from those who just add type annotations to JavaScript. `any` disables type checking entirely. `unknown` forces you to narrow the type before using it—it is the type-safe counterpart to `any`. Strong candidates prefer `unknown` for values of uncertain origin (API responses, error catches) and explain why.

**`never`** represents the type of something that can never occur—the return type of a function that always throws, or the result of narrowing that exhausts all possibilities. Understanding `never` is critical for exhaustive checks in discriminated unions.

## Generics and Constraints

Generics are where many TypeScript interviews separate mid-level from senior candidates. A generic function or type is parameterized over a type, allowing it to work with many different types while preserving type information.

Basic generic syntax (`function identity<T>(arg: T): T`) is table stakes. Interviewers push into **constraints** (`<T extends SomeType>`) to test whether candidates understand how to restrict what types a generic can accept. Common patterns: requiring an object with a specific key (`<T extends { id: number }>`), requiring a constructor (`<T extends new (...args: any[]) => any>`), or constraining one type parameter based on another (`<T, K extends keyof T>`).

**Generic utility types** are tested because they show practical fluency. Know the built-in utilities—`Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`, `Record<K, V>`, `ReturnType<F>`, `Parameters<F>`, `Awaited<T>`—and be prepared to implement simpler ones from scratch. Implementing `Pick` or `Partial` is a common whiteboard exercise.

## Union Types, Intersection Types, and Type Guards

**Union types** (`A | B`) represent values that can be one of several types. The challenge is consuming them safely. TypeScript narrows union types through control flow analysis, and interviewers test whether candidates can read and write narrowing logic correctly.

**Discriminated unions** (also called tagged unions or algebraic data types) are one of TypeScript's most powerful patterns. A discriminated union is a union of types that each have a common literal property (the discriminant). Pattern: `type Result = { kind: 'ok'; value: Data } | { kind: 'error'; message: string }`. Once you check `result.kind`, TypeScript narrows the type in each branch. Expect to implement a discriminated union and write an exhaustive switch with a `never` check.

**Intersection types** (`A & B`) combine types, requiring all properties of both. They are commonly used to compose mixins or extend third-party types. Know when intersection types produce `never` (when intersecting incompatible primitives like `string & number`).

**Type guards** are the mechanism for narrowing. Know the three forms: `typeof` guards (narrows primitives), `instanceof` guards (narrows class instances), and **custom type guard functions** (`function isFoo(x: unknown): x is Foo { ... }`). Interviewers often ask candidates to write a type guard for an API response shape.

## Conditional Types and Advanced Patterns

**Conditional types** (`T extends U ? X : Y`) allow types to branch based on whether a condition holds. They are the basis for many advanced utility types. `NonNullable<T>` is implemented as `T extends null | undefined ? never : T`. `Exclude<T, U>` is `T extends U ? never : T`.

**`infer`** within conditional types extracts type information from a type expression. `ReturnType<F>` is implemented as `F extends (...args: any[]) => infer R ? R : never`. Being able to read and write `infer` expressions is a reliable signal of TypeScript depth.

**Declaration merging** and **module augmentation** appear in interviews for roles working with large TypeScript codebases or library authoring. Declaration merging allows multiple `interface` declarations with the same name to merge into one—which is how Express, for example, allows extending the `Request` type.

**Strict mode** (`"strict": true` in tsconfig) enables a bundle of compiler options including `strictNullChecks`, `noImplicitAny`, and `strictFunctionTypes`. Know what each does and why `strictFunctionTypes` makes function types contravariant in parameter types.

## Which Companies Test TypeScript Deeply

Microsoft (obviously), Stripe, Vercel, Linear, and Figma test TypeScript at a deep level—expect advanced generics and type system questions. Companies using Next.js or large React codebases (most modern product companies) expect practical fluency: typing API responses, building reusable component prop types, and avoiding `any`.

For staff and principal roles at any company, expect questions about type-level programming, performance implications of complex types (the TypeScript compiler can slow significantly with deeply recursive types), and making type-safe abstractions that do not leak implementation details.

The best preparation is reading the TypeScript Handbook's advanced sections, implementing utility types from scratch, and contributing to or reading a well-typed open source TypeScript project. Real-world TypeScript is messier than tutorials suggest—exposure to that mess is what interviewers are evaluating.
