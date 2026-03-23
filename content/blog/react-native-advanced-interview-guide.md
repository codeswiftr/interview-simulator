---
title: "React Native Advanced Interview Guide: Performance, Native Modules, and Architecture"
description: "Master advanced React Native concepts for senior engineering interviews: New Architecture, performance optimization, native module bridging, and real-world debugging strategies."
date: "2026-03-20"
category: "Technical Skills"
---

# React Native Advanced Interview Guide: Performance, Native Modules, and Architecture

Senior React Native engineering interviews test your understanding of the runtime model, not just your ability to write components. Interviewers at companies like Airbnb, Shopify, and Meta expect you to reason about the JavaScript bridge, rendering pipeline, and memory characteristics. This guide covers the concepts most likely to separate strong candidates from exceptional ones.

## The New Architecture: JSI, Fabric, and TurboModules

The legacy React Native bridge serialized every JS-to-native communication to JSON. This created three problems: it was asynchronous only, it was slow for high-frequency interactions, and it made synchronous native calls impossible.

The New Architecture addresses this with the JavaScript Interface (JSI), which provides a C++ abstraction layer allowing JavaScript to hold direct references to native objects without serialization. This means JS can call native methods synchronously when needed.

**Fabric** is the new rendering system built on JSI. It moves layout calculation to a C++ layer shared across iOS and Android, enabling features like synchronous layout queries and concurrent rendering. The shadow tree — the lightweight representation used for layout — now lives in C++ rather than being duplicated across JS and native.

**TurboModules** replace the old NativeModules system. With legacy NativeModules, all native modules were eagerly loaded at startup. TurboModules are lazily loaded and type-safe through CodeGen, which generates type bindings from TypeScript or Flow specs. The practical interview point: TurboModules eliminate the startup cost of unused native code.

When asked about the New Architecture, explain the problem it solves, not just the feature names. "JSI eliminates JSON serialization" is a complete thought; "we have the New Architecture now" is not.

## Performance Optimization: Lists, Memoization, and the UI Thread

FlatList and SectionList both use VirtualizedList under the hood. The key behavioral difference is that SectionList handles grouped data with section headers, while FlatList works with flat arrays. Both recycle off-screen items, but neither is magic — if your renderItem is expensive, virtualization only helps so much.

Common performance mistakes in senior interviews:

**Inline functions in renderItem** create new function references on every render, breaking PureComponent and React.memo optimization. Extract renderItem to a stable reference outside the component, or use useCallback.

**Missing keyExtractor** forces React Native to use array indices, which breaks efficient reconciliation during mutations. Always provide stable unique keys.

**Images without caching** cause network fetches on every scroll. Libraries like react-native-fast-image handle cache headers correctly and provide priority queuing.

For memoization, the interview question is usually about knowing *when not to use it*. useMemo and useCallback add overhead — the comparison cost plus the closure. They're worth it when the computation is genuinely expensive or when referential stability prevents deep re-renders in child trees.

InteractionManager.runAfterInteractions is the correct pattern for deferring non-urgent work (analytics, lazy loading secondary data) until after animations complete. Using it in interviews demonstrates you understand the JS event loop's relationship with the native animation driver.

## Native Module Bridging

When asked to design a native module, walk through both the old bridge approach and the TurboModule approach. For TurboModules: write a TypeScript spec file using NativeModule, run CodeGen to generate the native stubs, then implement the platform-specific Swift/Kotlin code.

The key insight interviewers probe for: native modules run on a separate thread by default. If you need to update UI from a native module callback, you must dispatch to the main thread. On iOS this means `dispatch_async(dispatch_get_main_queue(), ...)`. Ignoring this causes intermittent crashes — the kind that appear in production but not tests.

For event emission from native to JS, EventEmitter is the standard pattern. Explain the subscription lifecycle: addListener on the JS side, removeListeners on the native side when count reaches zero. Memory leak questions in React Native interviews often center on forgotten EventEmitter subscriptions.

## Debugging Tools and Strategies

Flipper (now largely superseded but still in many codebases), React DevTools, and the Hermes profiler are the main tools. For performance profiling, the Hermes profiler produces a flame graph showing JS execution time. The systrace/Perfetto approach captures the full native+JS timeline.

For memory leaks, the most reliable technique is combining Xcode Instruments (iOS) or Android Studio Memory Profiler with JavaScript heap snapshots. Knowing the difference between a JS heap leak (retained JS objects) and a native memory leak (retained native views) is a genuine senior-level distinction.

## Common Senior Interview Questions

**Q: How does React Native's threading model work?**
Three threads: the JS thread (runs your JavaScript), the main/UI thread (handles native views and touch events), and the shadow thread (calculates layout). Fabric collapses some of this, but the JS thread isolation remains.

**Q: What's the difference between runOnJS and runOnUI in Reanimated?**
runOnJS moves a worklet callback to the JS thread; runOnUI moves a function to the UI thread. This distinction matters because Reanimated worklets run on the UI thread by default for 60/120fps animations.

**Q: When would you choose to write a native module vs. a JS-only solution?**
Native modules for: hardware access (camera, Bluetooth, sensors), CPU-intensive computation that blocks the JS thread, or when a high-quality community library already exists. JS-only is always preferable for maintainability when performance permits.

The best way to prepare for senior React Native interviews is to read the New Architecture RFC documents and the Reanimated source code. Interviewers notice candidates who understand tradeoffs from first principles rather than memorized answers.

---
