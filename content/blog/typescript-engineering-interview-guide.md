---
title: "TypeScript Engineering Interview Guide"
description: "What Microsoft, Airbnb, Stripe, and Notion actually ask about TypeScript in technical interviews — type system depth, runtime vs compile-time, migration patterns, and common coding challenges."
date: "2026-03-19"
category: "Frontend Engineering"
---

TypeScript interviews separate engineers who use TypeScript from engineers who understand it. The difference shows up in how you talk about the type system, when you reach for advanced features, and whether you can reason about what happens at runtime versus compile time.

This guide covers the TypeScript-specific material that comes up at companies like Microsoft, Airbnb, Stripe, and Notion — all of which have heavy TypeScript codebases and interview accordingly.

## The Type System: What Interviewers Actually Test

Most TypeScript questions probe whether you understand the type system structurally, not just syntactically. Companies with mature TypeScript codebases — Notion, Stripe, Linear — want engineers who can use the type system as a design tool.

### Generics

Generics questions usually come in two flavors: basic polymorphism and constrained generics with inference.

```typescript
// Basic: write a typed identity function
function identity<T>(value: T): T {
  return value;
}

// Intermediate: constrained generic with keyof
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Hard: generic with conditional return type
function parseInput<T extends string | number>(
  input: T
): T extends string ? string[] : number {
  if (typeof input === "string") {
    return input.split(",") as any;
  }
  return (input * 2) as any;
}
```

The `as any` casts in that last example are intentional — TypeScript's control flow narrowing doesn't propagate through conditional return types without explicit casting. Knowing where the type system falls short is as important as knowing what it can do.

### Conditional Types

Conditional types (`T extends U ? X : Y`) come up frequently at companies that write utility libraries or complex API clients.

```typescript
// Unwrap a Promise type
type Awaited<T> = T extends Promise<infer U> ? U : T;

// Flatten nested arrays
type Flatten<T> = T extends Array<infer Item> ? Item : T;

// Exclude null and undefined
type NonNullable<T> = T extends null | undefined ? never : T;

// Distribute over union types
type ToArray<T> = T extends any ? T[] : never;
// ToArray<string | number> → string[] | number[]
// (NOT (string | number)[])
```

The distribution behavior is a common interview trap. `T extends any ? T[] : never` distributes over unions. To avoid distribution, wrap in a tuple: `[T] extends [any] ? T[] : never`.

### Mapped Types

Mapped types transform the shape of an object type. Interviewers use these to test whether you understand index signatures and modifier keywords.

```typescript
// Make all properties optional (mirrors built-in Partial<T>)
type Optional<T> = {
  [K in keyof T]?: T[K];
};

// Make properties readonly
type Immutable<T> = {
  readonly [K in keyof T]: T[K];
};

// Remove readonly modifier
type Mutable<T> = {
  -readonly [K in keyof T]: T[K];
};

// Remap keys with as clause (TypeScript 4.1+)
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

// Getters<{ name: string }> → { getName: () => string }
```

The `-readonly` and `-?` modifiers (removing readonly and optional) trip up many candidates. Know them.

### Utility Types You Should Know Cold

| Utility Type | What It Does |
|---|---|
| `Partial<T>` | All properties optional |
| `Required<T>` | All properties required |
| `Readonly<T>` | All properties readonly |
| `Pick<T, K>` | Keep only keys K from T |
| `Omit<T, K>` | Remove keys K from T |
| `Record<K, V>` | Object with keys K and values V |
| `Exclude<T, U>` | Remove U from union T |
| `Extract<T, U>` | Keep only U from union T |
| `ReturnType<F>` | Return type of function F |
| `Parameters<F>` | Parameter tuple of function F |
| `InstanceType<C>` | Instance type of constructor C |

Interviewers often ask you to implement these from scratch. `Omit<T, K>` is a common one:

```typescript
type MyOmit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
```

## Runtime vs Compile Time

This is where many TypeScript interviews expose gaps. TypeScript types are erased at runtime. They provide zero runtime guarantees.

```typescript
interface User {
  id: string;
  email: string;
}

function processUser(user: User) {
  // TypeScript is happy. But at runtime, user could be anything.
  console.log(user.email.toUpperCase()); // throws if email is null at runtime
}

// Calling from JavaScript, or from an untyped API response:
processUser({ id: 123, email: null } as any);
```

Companies like Stripe, which process financial data, ask specifically about runtime validation. The expected answer involves a validation layer — Zod, io-ts, or manual guards — rather than trusting TypeScript alone.

```typescript
import { z } from "zod";

const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
});

type User = z.infer<typeof UserSchema>; // Types derived from runtime schema

function processUser(rawInput: unknown): void {
  const user = UserSchema.parse(rawInput); // throws ZodError if invalid
  console.log(user.email.toUpperCase()); // safe
}
```

Type guards are the manual version of this pattern:

```typescript
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as any).id === "string" &&
    typeof (value as any).email === "string"
  );
}
```

## When TypeScript Helps vs Hurts

This question comes up in engineering culture interviews at Airbnb and Notion, which have both done significant TypeScript migrations.

**TypeScript accelerates development when:**
- Working across large teams with shared types (API contracts, domain models)
- Refactoring — rename a field and the compiler finds every broken reference
- IDE tooling — autocomplete and inline docs from types, not comments
- Long-lived codebases where human memory of an API degrades over time

**TypeScript creates friction when:**
- Prototyping — type errors slow down exploratory work
- Complex third-party integrations with poor type definitions
- Over-engineered generic constraints that make simple operations verbose
- Teams with inconsistent TypeScript skill levels (some write `any` everywhere, defeating the purpose)

The honest answer for interviews: TypeScript's ROI scales with project size and team size. For a solo side project or a 2-week prototype, it's often overhead. For a 100k+ line codebase with 20 engineers, it's essential.

## JavaScript to TypeScript Migration

Microsoft (obviously), Airbnb, and Slack have all documented large-scale TypeScript migrations publicly. Interviewers at these companies — and companies that went through similar migrations — want to know you've thought about this practically.

The standard migration approach:
1. Add `tsconfig.json` with `"allowJs": true` and `"checkJs": false`
2. Rename files from `.js` to `.ts` incrementally, not all at once
3. Start with utility functions and shared types — the foundation that everything imports from
4. Use `// @ts-nocheck` at file tops as a temporary escape hatch, not a permanent solution
5. Enable stricter compiler options progressively (`strict`, `noImplicitAny`, `strictNullChecks`)

The common mistake: trying to get to `strict: true` on day one of a migration. The right approach is `strict: false` during migration, then tighten incrementally.

## Common TypeScript Coding Challenges

### Implement a typed event emitter

```typescript
type EventMap = {
  connect: { userId: string };
  message: { text: string; timestamp: number };
  disconnect: void;
};

class TypedEmitter<T extends Record<string, any>> {
  private listeners: Partial<{
    [K in keyof T]: Array<(data: T[K]) => void>;
  }> = {};

  on<K extends keyof T>(event: K, listener: (data: T[K]) => void): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(listener);
  }

  emit<K extends keyof T>(event: K, data: T[K]): void {
    this.listeners[event]?.forEach((fn) => fn(data));
  }
}

const emitter = new TypedEmitter<EventMap>();
emitter.on("message", ({ text }) => console.log(text)); // correctly typed
emitter.emit("message", { text: "hello", timestamp: Date.now() });
```

### Deep readonly type

```typescript
type DeepReadonly<T> = T extends (infer U)[]
  ? ReadonlyArray<DeepReadonly<U>>
  : T extends object
  ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
  : T;
```

### Extract function overload types

```typescript
// Given a function with overloads, extract all parameter/return combinations
type Overloads<T extends (...args: any[]) => any> =
  T extends { (...args: infer A1): infer R1; (...args: infer A2): infer R2 }
    ? [(...args: A1) => R1, (...args: A2) => R2]
    : [T];
```

## Interview Strategy

TypeScript interviews at Microsoft focus on type system correctness and edge cases. Airbnb and Stripe care more about pragmatic usage — knowing when to use `unknown` vs `any`, how to type API responses, and runtime validation patterns. Notion tends to ask about collaborative code patterns — how types communicate intent across a team.

When you write TypeScript in an interview: use types to communicate, not just to satisfy the compiler. Explicit return types on public functions, named types instead of inline objects for complex shapes, and a validation layer at trust boundaries — these are the signals that separate senior TypeScript engineers from engineers who just learned to use TypeScript.
