---
title: "TypeScript Advanced Interview Guide: Type System, Generics, and Production Patterns"
description: "Advanced TypeScript interview preparation — conditional types, mapped types, template literal types, type inference, variance, declaration merging, and TypeScript-specific design patterns for senior roles."
date: "2026-03-20"
category: "Programming Languages"
---

# TypeScript Advanced Interview Guide: Type System, Generics, and Production Patterns

Senior TypeScript interviews don't test whether you can add `: string` to variables — they test whether you understand the type system deeply enough to model complex domains correctly, write maintainable generics, and know when TypeScript's guarantees break down.

## The Type System: Structural Typing

TypeScript uses structural (duck) typing, not nominal typing. Two types are compatible if they have the same shape, regardless of name.

```typescript
interface Point { x: number; y: number; }
interface Coordinate { x: number; y: number; }

const p: Point = { x: 1, y: 2 };
const c: Coordinate = p; // valid — same shape
```

This is different from Java/C# where two classes are incompatible even if they have the same members (unless one extends the other). Structural typing enables duck typing patterns and makes TypeScript interoperate with JavaScript's conventions naturally.

**Freshness checking:** Object literals are checked for excess properties. `const p: Point = { x: 1, y: 2, z: 3 }` is an error. But `const obj = { x: 1, y: 2, z: 3 }; const p: Point = obj` is valid — widening through an intermediate variable bypasses freshness checking.

## Conditional Types

Conditional types enable type-level if/else:

```typescript
type IsString<T> = T extends string ? true : false;
type Unwrap<T> = T extends Promise<infer U> ? U : T;
```

The `infer` keyword extracts types from within generic types. Key uses: `ReturnType<T>`, `Parameters<T>`, `InstanceType<T>` are all built on conditional types + infer.

**Distributive conditional types:** When the check type is a bare type parameter, conditional types distribute over unions:

```typescript
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]
```

To prevent distribution, wrap in a tuple: `type ToArray<T> = [T] extends [any] ? T[] : never` produces `(string | number)[]` instead.

## Mapped Types

Mapped types transform the properties of a type:

```typescript
type Readonly<T> = { readonly [P in keyof T]: T[P] };
type Optional<T> = { [P in keyof T]?: T[P] };
type Nullable<T> = { [P in keyof T]: T[P] | null };
```

The `+`/`-` modifiers add or remove `readonly` and `?`:

```typescript
type Mutable<T> = { -readonly [P in keyof T]: T[P] };
type Required<T> = { [P in keyof T]-?: T[P] };
```

**Key remapping (TypeScript 4.1+):**

```typescript
type Getters<T> = {
  [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P]
};
// Getters<{name: string}> = { getName: () => string }
```

## Template Literal Types

TypeScript 4.1 added template literal types that construct string types:

```typescript
type EventName = 'click' | 'focus' | 'blur';
type Handler = `on${Capitalize<EventName>}`; // 'onClick' | 'onFocus' | 'onBlur'
```

Combined with mapped types, this enables strongly-typed event system APIs, path-based type inference (for routing), and SQL query builders.

## Variance and Type Compatibility

Understanding variance is necessary for explaining why certain type assignments work or fail.

**Covariance:** If `A extends B`, then `Container<A> extends Container<B>`. Arrays in TypeScript are covariant (unsafely): `string[] extends object[]`.

**Contravariance:** Function parameters are contravariant. If `A extends B`, then `(b: B) => void extends (a: A) => void`. A function accepting a broader type is safely assignable to a function expecting a narrower type.

**Bivariance vs strict function types:** TypeScript historically treated method types bivariantly (for compatibility). With `--strictFunctionTypes`, function type aliases and function call signatures are checked contravariantly. Method shorthand syntax remains bivariant.

## The `unknown` vs `any` vs `never` Triangle

**`any`:** Opt out of type checking. Assignable to anything, anything is assignable to it. Safety escape hatch.

**`unknown`:** Type-safe any. You don't know what's in it, but you must narrow it before use. Forces you to write type guards. Use for external data (API responses, `JSON.parse`).

**`never`:** The empty type — no value exists of type `never`. Bottom of the type hierarchy. Use cases: functions that never return (throw or infinite loop), exhaustiveness checking in discriminated unions.

```typescript
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`);
}

type Shape = Circle | Square;
function area(s: Shape) {
  if (s.kind === 'circle') { ... }
  if (s.kind === 'square') { ... }
  return assertNever(s); // TypeScript error if s can be anything other than never here
}
```

## Declaration Merging

TypeScript merges multiple declarations of the same name in specific ways:

**Interface merging:** Multiple interface declarations with the same name are combined. Useful for extending third-party types.

**Module augmentation:** Extend existing module types:

```typescript
// Augment Express's Request type
declare module 'express' {
  interface Request {
    user?: User;
  }
}
```

**Namespace merging with classes/functions:** Namespaces can add properties to classes and functions (used in declaration files for library interop).

## Type Guards and Narrowing

TypeScript narrows types based on control flow:

```typescript
function process(value: string | number) {
  if (typeof value === 'string') {
    // TypeScript knows value is string here
    value.toUpperCase();
  }
}
```

**Custom type guards:**

```typescript
function isUser(obj: any): obj is User {
  return typeof obj.name === 'string' && typeof obj.email === 'string';
}
```

**Discriminated unions:** The cleanest pattern for modeling variants:

```typescript
type Result<T> = 
  | { success: true; data: T }
  | { success: false; error: string };

function handle<T>(result: Result<T>) {
  if (result.success) {
    result.data; // T — TypeScript narrows correctly
  } else {
    result.error; // string
  }
}
```

## Performance Considerations in the Type System

Complex types can make TypeScript's type checker slow. Signs: slow IDE, long `tsc` compilation. Causes: deep recursive types, complex conditional types, large union types.

`type-coverage` and `tsc --diagnostics` help diagnose performance issues. Simplifying recursive types and breaking up large union types usually helps.

The `satisfies` operator (TypeScript 4.9): validates that an expression satisfies a type without widening to that type. Useful for object literals where you want inference to keep the literal type but still validate the shape.

