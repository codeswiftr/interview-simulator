---
title: "Vue 3 Composition API: Production Patterns"
description: "Advanced Vue 3 Composition API patterns for production applications—composables, reactive state management, provide/inject patterns, and the idioms that make Vue 3 codebases maintainable at scale."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Vue 3 Composition API: Production Patterns

Vue 3's Composition API is a fundamental shift from the Options API. While the Options API is still supported, modern Vue 3 applications use the Composition API with `<script setup>` for better TypeScript support, reusability, and organization. This guide covers production patterns.

## Composables: The Key Pattern

Composables are functions that encapsulate reactive state and logic — Vue's equivalent of React hooks:

```typescript
// composables/useUser.ts
import { ref, computed, readonly } from 'vue';

interface User {
    id: number;
    name: string;
    email: string;
}

export function useUser(userId: number) {
    const user = ref<User | null>(null);
    const loading = ref(false);
    const error = ref<Error | null>(null);

    const displayName = computed(() => user.value?.name ?? 'Anonymous');

    async function fetchUser() {
        loading.value = true;
        error.value = null;
        try {
            const response = await fetch(`/api/users/${userId}`);
            user.value = await response.json();
        } catch (e) {
            error.value = e as Error;
        } finally {
            loading.value = false;
        }
    }

    // Don't expose internal mutations directly
    return {
        user: readonly(user),
        loading: readonly(loading),
        error: readonly(error),
        displayName,
        fetchUser
    };
}
```

Usage in component:
```vue
<script setup lang="ts">
import { useUser } from '@/composables/useUser';

const props = defineProps<{ userId: number }>();
const { user, loading, error, displayName, fetchUser } = useUser(props.userId);

// Lifecycle
onMounted(() => fetchUser());
</script>

<template>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error.message }}</div>
    <div v-else>
        <h1>{{ displayName }}</h1>
        <p>{{ user?.email }}</p>
    </div>
</template>
```

## Reactivity Deep Dive

Understanding when to use `ref` vs `reactive`:

```typescript
// ref: for primitives and when you need to replace the value
const count = ref(0);
const user = ref<User | null>(null);
count.value++;
user.value = newUser; // can replace entirely

// reactive: for objects when you don't need to replace the whole object
const state = reactive({
    count: 0,
    name: '',
    items: [] as string[]
});
state.count++; // no .value needed for nested access
```

**Pitfall**: Destructuring reactive loses reactivity:
```typescript
const state = reactive({ count: 0, name: 'Alice' });

// WRONG — loses reactivity
const { count, name } = state;

// CORRECT — use toRefs
import { toRefs } from 'vue';
const { count, name } = toRefs(state);
count.value++; // reactive
```

## Global State with Pinia

Pinia is Vue 3's official state management library (replaces Vuex):

```typescript
// stores/user.ts
import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', () => {
    // State
    const currentUser = ref<User | null>(null);
    const isAuthenticated = computed(() => currentUser.value !== null);

    // Actions
    async function login(email: string, password: string) {
        const user = await authApi.login(email, password);
        currentUser.value = user;
    }

    function logout() {
        currentUser.value = null;
    }

    return { currentUser, isAuthenticated, login, logout };
});
```

Usage:
```vue
<script setup>
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();
// Access state, computed, and actions the same way
</script>
```

## Provide/Inject for Dependency Injection

For sharing state deeply without prop-drilling:

```typescript
// Parent component or plugin
import { provide, InjectionKey, Ref } from 'vue';

interface ThemeContext {
    theme: Ref<'light' | 'dark'>;
    toggleTheme: () => void;
}

export const ThemeKey: InjectionKey<ThemeContext> = Symbol('theme');

// In parent
const theme = ref<'light' | 'dark'>('light');
provide(ThemeKey, {
    theme,
    toggleTheme: () => {
        theme.value = theme.value === 'light' ? 'dark' : 'light';
    }
});

// In any child
import { inject } from 'vue';
const themeContext = inject(ThemeKey);
if (!themeContext) throw new Error('ThemeKey not provided');
const { theme, toggleTheme } = themeContext;
```

The `InjectionKey<T>` creates a typed injection key, giving TypeScript type information to `inject()`.

## Async Components and Suspense

```vue
<script setup>
import { defineAsyncComponent } from 'vue';

const HeavyComponent = defineAsyncComponent(() =>
    import('./HeavyComponent.vue')
);
</script>

<template>
    <Suspense>
        <template #default>
            <HeavyComponent />
        </template>
        <template #fallback>
            <LoadingSpinner />
        </template>
    </Suspense>
</template>
```

## Custom Directives

Extend Vue's template syntax for DOM manipulation patterns:

```typescript
// directives/tooltip.ts
import { Directive } from 'vue';

export const vTooltip: Directive<HTMLElement, string> = {
    mounted(el, binding) {
        el.setAttribute('title', binding.value);
        // Or integrate with a tooltip library
    },
    updated(el, binding) {
        el.setAttribute('title', binding.value);
    }
};

// Register globally
app.directive('tooltip', vTooltip);
```

```html
<button v-tooltip="'Delete this item'">Delete</button>
```

## Interview Tips

Vue 3 interview topics in 2026:

1. **Composables vs Options API mixins** — explain why composables are superior (explicit reactivity, TypeScript support, no naming conflicts)
2. **ref vs reactive** — when to use each and the pitfall of destructuring reactive
3. **Pinia vs Vuex** — why Pinia is the recommended store (Composition API support, better TypeScript, simpler API)
4. **provide/inject** — typed injection with InjectionKey
5. **Performance**: `shallowRef`, `shallowReactive`, `v-memo` for optimizing large lists

The most important Vue 3 concept for interviews: composables as the primary code reuse mechanism. Be able to write a composable from scratch and explain its advantages over mixins.
