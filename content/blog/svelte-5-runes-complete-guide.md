---
title: "Svelte 5 Runes: Complete Guide"
description: "Everything you need to know about Svelte 5's runes system—$state, $derived, $effect, $props, how they replace reactive declarations, and what changes in the mental model."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Svelte 5 Runes: Complete Guide

Svelte 5 introduces runes — a new reactive primitive system that replaces Svelte 4's implicit reactivity with explicit, compiler-aware signals. Runes change how you write Svelte components in fundamental ways while making the reactive model more predictable and TypeScript-friendly.

## What Are Runes?

Runes are special functions (starting with `$`) that signal to the Svelte compiler how variables should be treated reactively. They're not functions you import — they're compiler directives.

```svelte
<script>
    // Svelte 4: implicit reactivity
    let count = 0; // reactive because it's a top-level let

    // Svelte 5: explicit reactivity with runes
    let count = $state(0); // explicitly reactive state
</script>
```

## $state: Reactive State

```svelte
<script>
    let count = $state(0);
    let user = $state({ name: 'Alice', age: 30 });

    function increment() {
        count++;  // updates trigger re-render
    }

    function birthday() {
        user.age++;  // nested property updates also trigger re-render
    }
</script>

<p>Count: {count}</p>
<p>{user.name} is {user.age}</p>
<button onclick={increment}>+</button>
<button onclick={birthday}>Birthday</button>
```

`$state` creates deeply reactive state. Nested object/array mutations trigger updates.

## $derived: Computed Values

```svelte
<script>
    let count = $state(0);
    let doubled = $derived(count * 2);
    let message = $derived(count > 10 ? 'big' : 'small');

    // Complex derivations
    let items = $state(['apple', 'banana', 'cherry']);
    let filtered = $derived(
        items.filter(item => item.startsWith('a'))
    );
</script>

<p>Count: {count}, Doubled: {doubled}</p>
<p>Items starting with 'a': {filtered.join(', ')}</p>
```

`$derived` replaces Svelte 4's `$: derivedValue = ...` reactive declarations.

## $effect: Side Effects

```svelte
<script>
    let count = $state(0);

    $effect(() => {
        // Runs when count changes
        document.title = `Count: ${count}`;

        // Return cleanup function
        return () => {
            document.title = 'Default Title';
        };
    });

    $effect.pre(() => {
        // Runs before DOM update (equivalent to Svelte 4's beforeUpdate)
        console.log('About to update');
    });
</script>
```

`$effect` replaces `$: sideEffect()` patterns and `onMount` + reactive subscriptions.

## $props: Component Props

```svelte
<script>
    // Svelte 4
    export let name: string;
    export let age = 0; // with default

    // Svelte 5
    let { name, age = 0 }: { name: string; age?: number } = $props();
</script>

<p>{name} is {age} years old</p>
```

`$props` allows proper TypeScript typing and destructuring with defaults.

## $bindable: Two-Way Binding

```svelte
<!-- Child.svelte -->
<script>
    let { value = $bindable() } = $props();
</script>

<input bind:value={value} />
```

```svelte
<!-- Parent.svelte -->
<script>
    let text = $state('');
</script>

<Child bind:value={text} />
<p>Text: {text}</p>
```

`$bindable` explicitly marks which props support two-way binding.

## Stores Still Work (But Runes Are Preferred)

Svelte stores remain compatible:

```typescript
// store.ts
import { writable } from 'svelte/store';
export const count = writable(0);
```

```svelte
<script>
    import { count } from './store';
    // $count still works for store subscriptions in Svelte 5
</script>
<p>{$count}</p>
```

But for new code, use `$state` + module-level exports instead of stores:

```typescript
// state.svelte.ts
export let userCount = $state(0);
export function incrementCount() { userCount++; }
```

## Migration from Svelte 4

Key changes:

| Svelte 4 | Svelte 5 |
|----------|----------|
| `let x = 0` (reactive) | `let x = $state(0)` |
| `$: y = x * 2` | `let y = $derived(x * 2)` |
| `$: console.log(x)` | `$effect(() => console.log(x))` |
| `export let prop` | `let { prop } = $props()` |
| Svelte stores | `$state` in .svelte.ts files |

Svelte 5 ships with a migration tool: `npx svelte-migrate@latest svelte-5`

## Performance Implications

Svelte 5 runes compile to fine-grained reactive updates (similar to Solid.js signals). This means:
- Only the specific DOM nodes that depend on changed state update
- No virtual DOM diffing required
- Better performance than Svelte 4 for large component trees

Benchmark results show Svelte 5 as 10-30% faster than Svelte 4 on typical applications.

## Interview Tips

Svelte 5 interview questions in 2026:

1. Explain `$state` vs `$derived` vs `$effect` — when to use each
2. Why runes are more explicit than Svelte 4's implicit reactivity
3. `$bindable` for two-way binding with props
4. Migration path from Svelte 4
5. Performance model: fine-grained reactive updates vs virtual DOM

The core insight: runes make reactive dependencies explicit and compiler-trackable, enabling better tree-shaking, better TypeScript integration, and more predictable behavior.
