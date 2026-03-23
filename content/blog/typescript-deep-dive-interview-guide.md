---
title: "TypeScript Deep Dive Interview Guide"
description: "Advanced TypeScript interview preparation: the type system in depth, generics, conditional types, mapped types, type inference, utility types, and what senior TypeScript roles at companies like Microsoft, Vercel, Airbnb, and large-scale frontend organizations expect."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# TypeScript Deep Dive Interview Guide

TypeScript is now the default choice for production JavaScript — adopted by every major frontend framework (React, Vue, Angular, Svelte), significant backend tooling (NestJS, Prisma, tRPC), and large-scale web applications across the industry. Most TypeScript in the wild uses it at a surface level: basic type annotations, interfaces, and maybe generics. Senior TypeScript roles require depth in the type system that most engineers haven't needed until a specific problem forced them there. This guide focuses on what separates mid-level TypeScript users from engineers who genuinely master the type system.

## The TypeScript Type System: What's Actually Happening

TypeScript has a structural type system, not nominal. Two types are compatible if they have the same structure — not because they share a declaration. `interface Dog { name: string; breed: string }` and `interface Cat { name: string; breed: string }` are structurally identical and interchangeable, which surprises developers coming from Java or C#. Understanding structural typing explains many TypeScript behaviors that otherwise seem arbitrary.

**Assignability and subtyping**: Type A is assignable to type B if A has at least all the properties of B. A `Dog` with `{name, breed, age}` is assignable to `{name, breed}` — a subtype adds properties. This is covariant for object types but the interaction with function argument types (contravariance) is where most engineers get confused.

**The `any` type is a type system escape hatch**: Using `any` disables type checking for that value — it's not "I don't know the type", it's "TypeScript, stop checking." `unknown` is the safer alternative: values of type `unknown` require a type check (narrowing) before use. In senior interviews, using `any` where `unknown` or generics would work is a red flag.

## Advanced Type System Features

**Conditional types**: `T extends U ? X : Y`. These enable types that depend on other types, functioning like ternary expressions at the type level. The `infer` keyword within conditional types extracts type information: `type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never` extracts the return type of any function type. This pattern — using conditional types with `infer` — appears throughout TypeScript's built-in utility types and is a standard interview topic for senior roles.

**Mapped types**: Iterate over the properties of an existing type to produce a new type. `type Partial<T> = { [P in keyof T]?: T[P] }` makes all properties optional. `type Readonly<T> = { readonly [P in keyof T]: T[P] }` makes all properties readonly. Combining mapped types with conditional types enables powerful transformations: `type Required<T> = { [P in keyof T]-?: T[P] }` removes optionality (`-?` removes the optional modifier).

**Template literal types**: `type EventName = `${string}Changed`` creates a type matching any string ending in "Changed". Combining with mapped types enables deriving event handler types from event name unions — a pattern used heavily in DOM typing and event systems.

**Discriminated unions**: A union of object types where each variant has a literal type property that identifies it. `type Shape = { kind: 'circle'; radius: number } | { kind: 'square'; side: number }`. TypeScript narrows the type in `switch`/`if` statements based on the discriminant (`kind`). The exhaustiveness check pattern — using `never` for the default case — ensures all variants are handled when new variants are added.

**Variance in generics**: TypeScript has limited explicit variance annotations (`in`, `out` modifiers in TypeScript 4.7). Understanding covariance (output positions — returning T is safe if T is a subtype) and contravariance (input positions — accepting T is safe if T is a supertype) is essential for understanding why certain generic signatures work and others don't. Why is `(x: Dog) => void` not assignable to `(x: Animal) => void`? Function parameters are contravariant.

## Utility Types and the Standard Library

Every senior TypeScript engineer needs fluency with built-in utility types and the ability to implement them from scratch. This is a common interview task:

- `Partial<T>` / `Required<T>` — optionality
- `Readonly<T>` — immutability
- `Pick<T, K>` / `Omit<T, K>` — property selection
- `Record<K, V>` — creating mapped types from key/value pairs
- `Exclude<T, U>` / `Extract<T, U>` — set operations on unions
- `NonNullable<T>` — remove `null` and `undefined`
- `ReturnType<T>` / `Parameters<T>` / `ConstructorParameters<T>` — function reflection
- `Awaited<T>` — unwrap Promise chains

Being asked to implement `DeepPartial<T>` or `DeepReadonly<T>` (recursive versions) is a common senior interview challenge.

## TypeScript Configuration and Tooling

Senior roles often involve owning the TypeScript configuration for a large project:

**`strict` mode**: Enables `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, and others. Every serious TypeScript project should use `strict: true`. Not using it signals technical debt.

**Declaration files and `@types`**: Understanding `.d.ts` files, how `DefinitelyTyped` works, and how to write type declarations for untyped JavaScript libraries. For library authors, understanding `exports` in `package.json`, `types`/`typings` fields, and dual CJS/ESM publishing with TypeScript.

**Project references**: Large monorepos use TypeScript project references (`references` in `tsconfig.json`) for incremental compilation and correct build ordering. This is operational knowledge for engineering-at-scale roles.

## Interview Patterns by Role Level

**Mid-level TypeScript**: Define an interface, use generics with constraints, write a discriminated union with exhaustiveness check. Basic utility types.

**Senior TypeScript**: Implement a utility type from scratch. Explain why a specific type error occurs (often involves function variance or conditional type distribution). Design a type-safe event system or API client. Diagnose performance issues in the TypeScript compiler on a large codebase (isolatedModules, `skipLibCheck`, project references).

**TypeScript-focused roles (Compiler, Language Services)**: Contribute to TypeScript itself or tooling built on the compiler API (`ts.createProgram`, AST traversal, language service plugins). Knowledge of the checker, binder, and emitter internals.

## Who Hires for TypeScript Depth

**Microsoft**: TypeScript team and teams building TypeScript-heavy products. The TypeScript compiler itself is ~200K lines of TypeScript.

**Vercel, Netlify**: Deep TypeScript expertise in Next.js, SvelteKit, and framework-adjacent tooling. The `next.js` codebase and tRPC are canonical examples of advanced TypeScript.

**Prisma**: ORM where the type system generates query result types from schema at compile time — a tour de force of TypeScript's advanced features.

**Airbnb**: One of the earliest large-scale TypeScript adopters (migrated ~500K lines from Flow). Their JavaScript/TypeScript engineering blog documents hard-won lessons.

**Any company using tRPC, Zod, Effect, or similar**: These libraries are built on advanced TypeScript and attract developers who want to go deep.

TypeScript mastery is increasingly a differentiator for senior frontend and full-stack roles — the gap between "can use TypeScript" and "can design a type-safe system" is large enough to drive significant salary differences.
