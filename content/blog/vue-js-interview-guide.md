---
title: "Vue.js Interview Guide: Reactivity System, Composition API, and Senior-Level Questions"
description: "Complete Vue.js interview preparation — Vue 3 reactivity system, Composition API vs Options API, Pinia state management, performance optimization, SSR with Nuxt, and advanced Vue patterns for senior roles."
date: "2026-03-20"
category: "Programming Languages"
---

# Vue.js Interview Guide: Reactivity System, Composition API, and Senior-Level Questions

Vue.js interviews test whether you understand the framework deeply, not just whether you can write templates. This guide covers Vue 3 internals, the Composition API, state management, and the questions that appear in senior Vue engineer interviews.

## Vue 3 Reactivity System

Vue 3's reactivity is built on ES6 Proxies. When you create a reactive object with `ref()` or `reactive()`, Vue wraps it in a Proxy that intercepts property access (get) and mutations (set).

**How it works:**
- **Track:** When a computed property or `watchEffect` reads a reactive value, Vue registers the current effect as a subscriber to that value (tracked via a `get` trap on the Proxy)
- **Trigger:** When a reactive value is mutated, Vue triggers all subscribed effects to re-run

This is a significant improvement over Vue 2's `Object.defineProperty` approach, which had limitations: it couldn't detect property additions to objects or index-based changes to arrays.

**`ref` vs `reactive`:**
- `ref`: wraps a primitive or object; accessed via `.value` in JavaScript, auto-unwrapped in templates
- `reactive`: wraps only objects (not primitives); no `.value` wrapper; cannot be destructured without losing reactivity

The reason `ref` needs `.value`: JavaScript proxies can't intercept primitive reassignments (`let x = 1; x = 2` — no proxy trap fires on this). Wrapping in an object `{ value: 1 }` allows the proxy to intercept `.value` assignment.

## Composition API vs Options API

**Options API:** Organizes code by option type — `data()`, `computed`, `methods`, `watch`, lifecycle hooks. Familiar, easy to learn, but logic for one feature is spread across multiple options.

**Composition API:** Organizes code by logical concern. All code for a feature (state, computed, methods, watchers) lives together in `setup()`. Enables reusable composables — logic extracted into functions.

When asked why Vue 3 introduced the Composition API: large codebases with the Options API became hard to maintain because related logic was fragmented across options. The Composition API enables extracting reusable logic into composable functions — similar to React hooks.

**Composables:**
```javascript
// useCounter.js
import { ref } from 'vue'
export function useCounter(initial = 0) {
  const count = ref(initial)
  const increment = () => count.value++
  const decrement = () => count.value--
  return { count, increment, decrement }
}
```
This composable can be used in any component and tested independently.

## Key Lifecycle Hooks

In the Composition API (using `on` prefix): `onMounted`, `onUpdated`, `onUnmounted`, `onBeforeMount`, `onBeforeUpdate`, `onBeforeUnmount`.

Critical interview question: "What's the difference between `onMounted` and `onBeforeMount`?" Answer: `onBeforeMount` fires before the component's DOM is created — you can't access DOM elements. `onMounted` fires after the component is mounted and DOM is available. Most DOM manipulation and API calls go in `onMounted`.

**`onUnmounted` is important for cleanup:** Remove event listeners, cancel pending requests, clear timers. Forgetting to clean up causes memory leaks in single-page apps where components are frequently mounted/unmounted.

## `computed` and `watch`

**`computed`:** Derived state. Cached — only re-evaluates when dependencies change. Use for values derived from reactive state. Read-only by default; can define getter + setter.

**`watch`:** Side effects in response to reactive changes. Runs asynchronously (after component updates). Options: `immediate` (run on creation), `deep` (watch nested properties).

**`watchEffect`:** Like `watch` but automatically tracks dependencies — no need to specify what to watch. Runs immediately. Less explicit than `watch` — prefer `watch` when you need control over when to run and what triggered the effect.

## Pinia State Management

Pinia replaced Vuex as the official Vue state management library. Key differences from Vuex: no mutations (direct state modification), better TypeScript support, no modules (stores are flat), devtools integration built-in.

```javascript
// stores/counter.js
import { defineStore } from 'pinia'
export const useCounterStore = defineStore('counter', {
  state: () => ({ count: 0 }),
  getters: {
    doubled: (state) => state.count * 2,
  },
  actions: {
    increment() { this.count++ },
    async fetchCount() {
      this.count = await api.getCount()
    }
  }
})
```

Actions can be async — no separate action/mutation split required.

## Performance Optimization

**`v-once`:** Render element only once, never re-render. Use for static content.

**`v-memo`:** Memoize a subtree. Re-renders only when specified dependencies change. Vue 3.2+.

**`shallowRef` / `shallowReactive`:** Only the top level is reactive. Use when you have large objects where only top-level properties change — avoids deep proxy traversal.

**`defineAsyncComponent`:** Lazy load components — only bundled when actually used. Combined with `Suspense` for loading states.

**Virtual scrolling:** For long lists, render only visible items. `vue-virtual-scroller` is the standard library. The interview question: "How would you render a list of 100,000 items performantly?" — virtual scrolling, never DOM rendering all 100K.

## Vue Router

**Navigation guards:** `beforeEach`, `afterEach`, per-route guards (`beforeEnter`), in-component guards (`beforeRouteEnter`, `beforeRouteLeave`). Common use case: auth guards that redirect unauthenticated users to login.

**Lazy loading routes:**
```javascript
const UserProfile = () => import('./pages/UserProfile.vue')
```
Each route becomes a separate chunk, loaded only when navigated to. Critical for performance in large applications.

## SSR with Nuxt

Nuxt.js is the standard SSR framework for Vue. Key concepts:

- **`useFetch` / `useAsyncData`:** Isomorphic data fetching — runs on server during SSR, runs on client for SPA navigation
- **File-based routing:** Pages in `pages/` directory auto-generate routes
- **Server routes:** API endpoints in `server/api/` run exclusively on the server
- **`useState`:** Shared state between server and client (serialized in HTML payload)

SSR interview question: "What's the difference between `useFetch` and `$fetch` in Nuxt?" Answer: `useFetch` is composable, deduplicated, returns pending/error state. `$fetch` is a direct fetch call without deduplication or composable features — use in server routes and event handlers.

