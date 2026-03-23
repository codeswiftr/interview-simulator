---
title: "React Native Engineer Interview Guide: What to Expect and How to Prepare"
description: "From the JavaScript bridge to Fabric architecture, Hermes engine, and performance optimization — everything you need to ace a React Native mobile interview."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# React Native Engineer Interview Guide: What to Expect and How to Prepare

React Native interviews occupy a unique space: they test mobile engineering concepts alongside web React knowledge, plus platform-specific understanding of iOS and Android. Companies hiring for cross-platform mobile roles expect more than knowing how to write components — they want engineers who understand the architecture well enough to debug production issues and make informed performance tradeoffs.

## The JavaScript Bridge and Hermes Engine

The most fundamental architecture question in a React Native interview is: "How does React Native actually work?" The answer requires understanding the bridge — the asynchronous communication channel between the JavaScript thread and the native thread.

In the classic architecture, all communication between JS and native code passed through a serialization layer: JS would serialize method calls to JSON, send them across the bridge, and native code would deserialize and execute them. This created measurable latency, and any heavy computation on the JS thread would block UI updates. Interviewers will probe whether you understand the implications: why you shouldn't do expensive work synchronously, why `InteractionManager.runAfterInteractions` exists, and why animations should be offloaded to the native thread with `useNativeDriver: true`.

**Hermes** is the JavaScript engine Facebook built specifically for React Native. The key things to know: Hermes compiles JavaScript to bytecode ahead of time (at build time, not at runtime), which improves startup performance significantly. It also has a more efficient garbage collector tuned for mobile memory constraints. Know the tradeoffs — not all JavaScript features were initially supported, and some third-party libraries had Hermes compatibility issues that required workarounds.

Interview questions to expect: "What's the difference between the main thread, the JS thread, and the native modules thread?" and "Why would you see dropped frames even in a purely React Native app with no custom native code?"

## Fabric Architecture and Native Modules

The new architecture (Fabric + JSI + TurboModules) is now the default for new projects and increasingly tested in interviews, especially at companies that have already migrated.

**JSI (JavaScript Interface)** replaces the bridge with a direct reference-based connection between JavaScript and C++. JS objects can hold direct references to native objects, eliminating serialization overhead. This is the foundational change that enables everything else.

**Fabric** is the new rendering system built on JSI. Unlike the old bridge-based renderer, Fabric allows synchronous operations between JS and native — critical for things like measuring layout during gesture handling. It also enables concurrent rendering, aligning React Native with React 18's concurrent features.

**TurboModules** replace the old NativeModules system. In the old system, all native modules were loaded eagerly at startup; TurboModules are loaded lazily and have type-safe interfaces generated from TypeScript/Flow specs.

When asked to compare old vs. new architecture, frame it around three axes: performance (latency and throughput of cross-thread calls), developer experience (type safety, code generation), and React alignment (concurrent features, Suspense).

## Performance Optimization in Practice

Performance questions in React Native interviews almost always involve FlatList and rendering optimization. Know these patterns cold:

**FlatList over ScrollView:** ScrollView renders all children at once. FlatList renders only what's visible (plus a configurable window). The key props interviewers ask about: `getItemLayout` (avoids dynamic height measurement, critical for large lists), `keyExtractor` (enables efficient reconciliation), `initialNumToRender`, `maxToRenderPerBatch`, and `windowSize`.

**`useMemo` and `useCallback`:** These matter more in React Native than in web React because reconciliation overhead is more visible. A parent component that passes new function references on every render forces child PureComponent or React.memo comparisons to fail. Know when memoization actually helps vs. when it's premature optimization that adds complexity without benefit.

**Avoiding JS thread blocking:** Heavy computations should use `InteractionManager` to yield to animations, or be moved to a native module. For truly CPU-intensive work (image processing, cryptography), running in a separate thread via a native module is the right answer.

**Memory management:** Image caching is a common interview topic. Know that React Native's default Image component doesn't cache aggressively, and libraries like `react-native-fast-image` exist to address this. Understand why memory leaks in React Native often show up as iOS/Android memory warnings rather than JS heap issues.

## Key Differences from Web React

Interviewers at companies that work across web and mobile want to know you understand where the platforms diverge:

**No DOM:** There's no `<div>`, no CSS (though StyleSheet looks similar), no browser APIs. Flexbox works differently — the default `flexDirection` is `column`, not `row`. Styling is applied via inline objects, not class names.

**Navigation:** React Navigation (or the older NavigatorIOS) is fundamentally different from React Router. It's stack-based with native gesture recognition rather than URL-based routing. Screen mounting/unmounting behavior differs from web page transitions.

**Platform-specific code:** You can write `Platform.select`, use `.ios.js` and `.android.js` file extensions, or use conditional imports for platform-specific behavior. Interviewers may ask how you'd handle a component that needs completely different behavior on each platform.

**Lifecycle differences:** Background/foreground transitions, deep linking, push notifications, and permissions don't exist in the web world. Know how `AppState` works for handling background transitions.

## Debugging Tools and Development Workflow

React Native debugging questions test practical experience:

**Flipper** (and its successor tooling) provides a desktop debugging interface: network request inspection, layout inspection, React DevTools, and a JavaScript debugger. Know what each panel is used for.

**Reactotron** is a popular alternative for state management debugging, especially with Redux.

**Metro bundler:** Understand that Metro is the development bundler (not webpack), that it watches for file changes and serves bundles to the simulator, and that bundle splitting works differently from web.

**Common production debugging:** Sentry for error tracking, source maps for symbolication, and how to read a React Native crash report from Crashlytics or Firebase — these come up in senior interview discussions.

The best way to prepare is to build and ship something. Engineers who have debugged real performance issues or integrated a complex native module answer these questions with the kind of specificity that interviewers remember.
