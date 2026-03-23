---
title: "TypeScript Advanced Patterns: Interview Guide"
description: "Advanced TypeScript patterns for senior engineering interviews—conditional types, mapped types, template literal types, discriminated unions, and the type utilities that demonstrate TypeScript mastery."
date: "2026-03-21"
category: "Language Deep Dives"
---

# TypeScript Advanced Patterns: Interview Guide

TypeScript proficiency has become a requirement for senior frontend and fullstack roles. Basic TypeScript (interface, enum, generics) is table stakes. This guide covers the advanced patterns that distinguish senior candidates in technical interviews and code reviews.

## Utility Types: What Every Senior Should Know

```typescript
// Partial — all properties optional
type PartialUser = Partial<User>;

// Required — all properties required
type RequiredUser = Required<User>;

// Pick — select specific properties
type UserPreview = Pick<User, 'id' | 'name'>;

// Omit — exclude specific properties
type UserWithoutPassword = Omit<User, 'password' | 'salt'>;

// Record — typed dictionary
type UserMap = Record<string, User>;

// ReturnType — extract function return type
async function getUser(): Promise<User> { /* ... */ }
type UserResult = Awaited<ReturnType<typeof getUser>>; // User
```

## Conditional Types

Conditional types enable type-level branching:

```typescript
type IsArray<T> = T extends Array<infer Item> ? Item : never;

type StringItem = IsArray<string[]>; // string
type NumberItem = IsArray<number[]>; // number
type NotArray = IsArray<string>;     // never

// Practical use: flatten nested types
type Flatten<T> = T extends Array<infer Item> ? Flatten<Item> : T;
type NestedArray = number[][][];
type FlatType = Flatten<NestedArray>; // number
```

## Mapped Types

Transform every property in a type:

```typescript
// Make all properties nullable
type Nullable<T> = {
    [K in keyof T]: T[K] | null;
};

// Deep readonly
type DeepReadonly<T> = {
    readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

// Transform property names
type WithGetters<T> = {
    [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type User = { name: string; age: number };
type UserGetters = WithGetters<User>;
// { getName: () => string; getAge: () => number }
```

## Template Literal Types

String manipulation at the type level:

```typescript
type EventName = 'click' | 'focus' | 'blur';
type EventHandler = `on${Capitalize<EventName>}`; // 'onClick' | 'onFocus' | 'onBlur'

// Type-safe CSS property names
type CSSProperty = 'margin' | 'padding' | 'border';
type CSSDirection = 'top' | 'right' | 'bottom' | 'left';
type CSSDirectionalProperty = `${CSSProperty}-${CSSDirection}`;
// 'margin-top' | 'margin-right' | ... | 'border-left'
```

## Discriminated Unions for State Machines

The most underused TypeScript pattern in production code:

```typescript
type LoadingState = { status: 'loading' };
type SuccessState = { status: 'success'; data: User };
type ErrorState = { status: 'error'; error: Error };

type FetchState = LoadingState | SuccessState | ErrorState;

function render(state: FetchState) {
    switch (state.status) {
        case 'loading':
            return <Spinner />;
        case 'success':
            // TypeScript narrows: state.data is available here
            return <UserCard user={state.data} />;
        case 'error':
            return <ErrorMessage error={state.error} />;
    }
}
```

The discriminant field (`status`) allows TypeScript to narrow the union type in each branch.

## Infer for Type Extraction

```typescript
// Extract promise resolve type
type Unwrap<T> = T extends Promise<infer R> ? R : T;
type Result = Unwrap<Promise<string>>; // string

// Extract function parameter types
type Parameters<T> = T extends (...args: infer P) => any ? P : never;

// Extract constructor parameter types
type ConstructorParameters<T> = T extends new (...args: infer P) => any ? P : never;
```

## Branded Types for Type Safety

Prevent mixing semantically different values of the same underlying type:

```typescript
type UserId = string & { readonly _brand: 'UserId' };
type OrderId = string & { readonly _brand: 'OrderId' };

function createUserId(id: string): UserId {
    return id as UserId;
}

function getUser(id: UserId): User { /* ... */ }

const userId = createUserId("user-123");
const orderId = "order-456" as OrderId;

getUser(userId); // OK
getUser(orderId); // TYPE ERROR — prevents mixing IDs!
```

## Builder Pattern with TypeScript

Type-safe fluent interfaces:

```typescript
class QueryBuilder<T, Selected extends keyof T = keyof T> {
    select<K extends keyof T>(...fields: K[]): QueryBuilder<T, K> {
        return this as any;
    }

    where(field: keyof T, value: T[typeof field]): this {
        return this;
    }

    build(): Pick<T, Selected>[] {
        return [];
    }
}

interface User {
    id: number;
    name: string;
    email: string;
    password: string;
}

const results = new QueryBuilder<User>()
    .select('id', 'name', 'email')  // TypeScript knows selected fields
    .where('id', 1)
    .build();
// results: Pick<User, 'id' | 'name' | 'email'>[]
```

## Type Guards

Narrow types at runtime:

```typescript
// Type predicate function
function isUser(obj: unknown): obj is User {
    return (
        typeof obj === 'object' &&
        obj !== null &&
        'id' in obj &&
        'name' in obj
    );
}

// Using the guard
const data: unknown = fetchData();
if (isUser(data)) {
    console.log(data.name); // TypeScript knows this is User
}

// Using assertion functions (throws if wrong)
function assertUser(obj: unknown): asserts obj is User {
    if (!isUser(obj)) {
        throw new Error('Expected User');
    }
}
```

## Interview Tips

TypeScript interview questions are increasingly common at senior levels:

1. **Conditional types** — interviewers ask you to implement utility types from scratch
2. **Discriminated unions** — the right pattern for API response types and state machines
3. **Type narrowing** — explain how TypeScript narrows types in if/switch statements
4. **Template literal types** — type-safe event systems and property transformations
5. **Branded types** — explain why `string` alone isn't type-safe for IDs

The most impressive TypeScript knowledge to demonstrate: understanding how the TypeScript compiler uses control flow analysis to narrow types, and being able to write type-level logic that compiles correctly.
