# React Native / Mobile Engineer Interview Guide 2024: Cross-Platform at Scale

React Native interviews have matured. In 2024, hiring managers at companies with serious mobile apps are no longer satisfied with candidates who can build a counter app with useState. They want engineers who understand why the JavaScript thread locks up, how Fabric differs from the old bridge, and when to reach for a native module versus a third-party library. This guide covers everything you need to walk into a React Native interview ready to go deep on architecture, performance, testing, and platform-specific behavior.

---

## Understanding the Architecture: Old vs. New

This is the single most differentiating topic in a React Native interview. Most candidates know that React Native uses JavaScript. Very few can explain what happens between JavaScript and the native layer in precise terms.

### The Old Architecture: Bridge

The original React Native architecture routes all communication between JavaScript and native through an asynchronous, serialized bridge. The JavaScript thread serializes messages to JSON, passes them across the bridge, and waits. Native code deserializes them, executes, serializes a response, and sends it back.

The fundamental limitations of this design:

- **Asynchronous by necessity.** The bridge cannot make synchronous calls. This means gestures, animations, and layout calculations that require synchronous access to native values are inherently laggy unless you find workarounds.
- **Serialization overhead.** Every interaction crosses a JSON serialization boundary. For frequent updates (animations running at 60fps, scroll events), this overhead accumulates.
- **Thread contention.** Three threads: the JS thread, the native UI thread, and the Shadow thread (layout). Blocking the JS thread drops frames even if the UI thread is idle.

The JSI (JavaScript Interface) was introduced as a bridge replacement — it allows JavaScript to hold direct references to C++ host objects, enabling synchronous calls. But JSI alone was not the full solution; it required Fabric and TurboModules to be useful in practice.

### The New Architecture: Fabric + TurboModules + JSI

The New Architecture, stable as of React Native 0.73, replaces every layer of the old system:

**JSI (JavaScript Interface):** A C++ layer that allows the JS engine to hold direct references to native objects. No serialization. No asynchronous round trips. JavaScript can call into native synchronously when needed.

**TurboModules:** The replacement for Native Modules. Instead of eagerly initializing all native modules at startup, TurboModules are lazy — they are only loaded when accessed. This dramatically reduces app launch time. They use JSI for communication, so calls are synchronous and type-safe.

**Fabric:** The new rendering system. The old renderer lived entirely on the native thread and communicated with JS only through the bridge. Fabric introduces a shared C++ layer (the Shadow Tree) that runs on multiple threads simultaneously, enabling features like concurrent rendering and proper interoperability with React's concurrent mode.

**Codegen:** Generates type-safe native code from TypeScript interfaces, eliminating runtime type mismatches between JS and native.

When you get asked "what do you know about the New Architecture," the answer they are looking for covers these four pieces and why each one matters.

---

## iOS vs. Android Platform Differences in a React Native Context

React Native abstracts most platform differences, but knowing where the abstraction leaks is critical.

**Navigation and gestures:** The back gesture on Android is a system-level event (`BackHandler`). iOS has a swipe-back gesture tied to the navigation stack. On Android you must handle the hardware back button explicitly. Forgetting this is a common bug.

**Text rendering:** Font metrics differ between iOS and Android. A `lineHeight` that looks perfect on iOS often clips descenders on Android. Using `includeFontPadding: false` on Android is a common fix.

**Shadow props:** iOS supports full box-shadow equivalents on View. Android requires `elevation` for shadows, which also affects z-index stacking. You cannot achieve identical shadows cross-platform without platform-specific code.

**Permissions:** iOS asks for permissions lazily (first use). Android can ask at any time, and permissions must be declared in `AndroidManifest.xml`. Runtime permissions have different flows across Android versions. Libraries like `react-native-permissions` unify the API but you still need to understand the underlying platform behavior.

**StatusBar:** `StatusBar` behaves differently. On Android, `translucent` mode affects how content is positioned under the status bar. Getting the status bar right typically requires `react-native-safe-area-context`.

**Keyboard behavior:** `KeyboardAvoidingView` with `behavior="padding"` works on iOS. On Android, the window soft input mode in `AndroidManifest.xml` interacts with the layout system differently. Many teams end up writing platform-specific keyboard handling.

---

## Performance Optimization

Performance questions in React Native interviews almost always center on list rendering, JavaScript thread usage, and animation smoothness.

### FlatList vs. ScrollView

`ScrollView` renders all children immediately. For short, static lists it is fine. For anything dynamic or long, `FlatList` is required because it virtualizes — only rendering items near the viewport.

Key `FlatList` props interviewers ask about:

- `keyExtractor`: Tells React how to identify items for reconciliation. Using the array index as a key is a performance anti-pattern.
- `getItemLayout`: Skips async layout measurement by pre-computing item dimensions. Critical for large lists with uniform item heights.
- `windowSize`: Controls how many viewports worth of content are rendered. Default is 21 (10 above, 10 below, 1 visible). Reducing this saves memory but increases blank content on fast scroll.
- `removeClippedSubviews`: Detaches off-screen views from the native view hierarchy. Reduces memory but can cause visual glitches if item heights are variable.
- `initialNumToRender`: How many items to render on first paint. Keep it low enough to not block the initial render.

### useCallback and useMemo in RN Context

The same React rules apply, but the impact is amplified because re-rendering components in a long list can cause noticeable frame drops. Memoize callback props passed to list items. Use `React.memo` on list item components. The rule: if a component renders in a FlatList and receives functions as props, those functions should be stable references.

### InteractionManager

`InteractionManager.runAfterInteractions` defers work until all animations and gestures have completed. Use it for expensive post-navigation data fetching that would otherwise compete with the transition animation for the JS thread.

```javascript
useEffect(() => {
  const interaction = InteractionManager.runAfterInteractions(() => {
    fetchHeavyData();
  });
  return () => interaction.cancel();
}, []);
```

### Hermes Engine

Hermes is a JavaScript engine optimized for React Native. Key properties:

- Compiles JavaScript to bytecode at build time, reducing parse time at runtime.
- Lower memory footprint than V8 or JavaScriptCore.
- Enabled by default since React Native 0.70.

When asked about Hermes, discuss the build-time compilation advantage, the fact that it does not have a JIT compiler (which makes it faster to start but potentially slower on sustained compute-heavy workloads), and the debugging improvements it enables via Chrome DevTools Protocol.

### Flipper Debugging

Flipper is the debugging platform for React Native. Know the key plugins: React DevTools (component tree inspection), Network inspector (HTTP requests), Redux DevTools (if using Redux), and Hermes Debugger (breakpoints and profiling). For performance investigation, the Hermes Profiler shows CPU flame graphs segmented by JS thread activity.

---

## Native Modules and Bridging

When third-party libraries do not exist or cannot meet your needs, you write native modules.

A native module exposes a native class to JavaScript. In the old architecture, you annotate a class with `@ReactModule` on Android (Java/Kotlin) or implement `RCTBridgeModule` on iOS (Objective-C/Swift). In the New Architecture, you define a TypeScript specification using Codegen, and Turbo Module infrastructure generates the bridge boilerplate.

Common use cases: biometric authentication, Bluetooth, custom camera pipelines, NFC, deep device integrations that existing libraries handle poorly.

Interview questions often involve tradeoffs: "When would you write a native module vs. using a community library?" The answer should address maintenance burden, security, performance requirements, and whether the library is actively maintained and supports the New Architecture.

---

## Animations

### Animated API (Core)

The built-in Animated API runs on the JS thread by default, which means complex animations compete with render cycles. The key optimization is `useNativeDriver: true`, which offloads the animation to the native thread for transform and opacity animations only. Layout properties (width, height, position) cannot use the native driver.

### Reanimated

React Native Reanimated moves animation logic to a worklet that runs on the UI thread via JSI. This eliminates JS thread involvement entirely for animation-critical code. Reanimated 2+ uses a worklet syntax with `useSharedValue`, `useAnimatedStyle`, and `runOnJS`/`runOnUI` for crossing thread boundaries.

For production apps with gesture-driven animations (drag-to-dismiss, swipe interactions, physics-based springs), Reanimated is the correct choice. The `react-native-gesture-handler` library is its standard companion.

### Lottie

Lottie renders After Effects animations exported as JSON. The renderer runs natively on both platforms. Use it for micro-animations, onboarding illustrations, and loading states where the design team wants precise control. The tradeoff is bundle size and the requirement for design assets.

---

## Offline-First Patterns

Offline support is a common system design question in mobile interviews: "Design an offline-capable note-taking app."

### MMKV

MMKV is a key-value store backed by memory-mapped files. It is 30x faster than AsyncStorage for synchronous reads. Use it for persisting user preferences, auth tokens, and small state slices. It is synchronous, which means no async overhead for reads in hot paths.

### SQLite

For relational data with queries (filtering, sorting, joins), use SQLite via `expo-sqlite` or `@op-engineering/op-sqlite`. Design your schema to support the offline use case: timestamps for sync, soft-delete fields, and a sync queue table that tracks mutations made while offline.

### Apollo Cache

If your app uses GraphQL, Apollo Client's normalized cache can persist via `apollo3-cache-persist`. The normalized cache deduplicates entities by type and ID, so updates in one query automatically reflect in other queries that reference the same entity. Combine with optimistic updates for offline writes.

### Sync Strategy

Interviewers want to hear about conflict resolution. The common patterns are last-write-wins (simple, lossy), vector clocks (complex, accurate), and operational transforms (used in real-time collaborative editors). For most mobile apps, last-write-wins with a server timestamp is sufficient and worth defending.

---

## Push Notifications: APNs vs. FCM

APNs (Apple Push Notification service) handles iOS. FCM (Firebase Cloud Messaging) handles Android and can proxy to APNs for iOS through Firebase.

Key interview points:

- APNs requires a certificate or token-based authentication. Tokens (JWT, using a `.p8` key file) are preferred because they do not expire.
- FCM data messages vs. notification messages: notification messages are displayed automatically when the app is in the background; data messages are always delivered to your handler for custom processing.
- Deep linking from notification taps requires handling both cold start (app launched from terminated state) and warm start (app in background) cases separately.
- Notification permissions on iOS require explicit user consent. Handle the permission-denied case gracefully.

---

## Crash Reporting: Sentry and Bugsnag

Both Sentry and Bugsnag capture native crashes, JS exceptions, and ANRs (Application Not Responding on Android). Key capabilities to know:

- **Source maps:** Without source maps, JS stack traces point to minified bundle line numbers. Uploading source maps at build time makes traces readable.
- **Breadcrumbs:** Automatic capture of navigation events, network requests, and user interactions before a crash.
- **Release tracking:** Tag crashes to release versions to understand whether a new version regressed stability.
- **Native crash symbolication:** iOS crash reports contain memory addresses that must be symbolicated using dSYM files. Both tools handle this automatically when you upload dSYMs.

---

## App Store Deployment Pipeline

A mature deployment pipeline for React Native includes:

1. **Fastlane** for automating certificate management (match), building, and uploading to TestFlight/Play Store Internal Testing.
2. **CodePush / EAS Update** for OTA (over-the-air) JavaScript bundle updates that bypass the app store review cycle. Critical constraint: OTA updates can only change the JS bundle, not native code.
3. **CI/CD:** GitHub Actions or Bitrise running lint, tests, and builds on every pull request. Native builds are expensive (30-60 minutes); cache node modules and CocoaPods aggressively.
4. **Environment configuration:** Separate `.env` files for development, staging, and production. Libraries like `react-native-config` make environment variables available in native code.

---

## Common Interview Questions

### Design a Real-Time Chat UI

Cover: FlatList inverted (newest messages at bottom), optimistic message insertion (show the message immediately, mark as "sending"), WebSocket or long-polling for message delivery, handling connection loss gracefully (offline queue), pagination strategy for loading older messages.

### Design an Offline-Capable App

Cover: local persistence layer (SQLite or MMKV), sync queue for mutations made offline, conflict resolution strategy, network state detection (`@react-native-community/netinfo`), user feedback during sync, optimistic UI updates.

### Optimize a Slow List

Walk through: identify the bottleneck using Hermes profiler or Flipper, check `keyExtractor` is using a stable unique ID, verify list items are wrapped in `React.memo`, verify callback props are stable references via `useCallback`, check `getItemLayout` is implemented, evaluate `windowSize` and `removeClippedSubviews`, check if heavy computation in render should be moved to a background worker.

---

## The Tradeoffs Question: RN vs. Native vs. Flutter

This is almost always asked. Have a structured answer.

**React Native:** Best when the team has strong JavaScript/React skills, the app is primarily UI-driven with standard interactions, and sharing logic with a web app is valuable. Weaknesses: native module complexity, architecture migration debt, bridging overhead for high-frequency native APIs.

**Native (Swift/Kotlin):** Best when the app requires deep platform integration (ARKit, custom camera pipelines, Bluetooth), when you need maximum performance for graphics-heavy or computation-heavy features, or when the team already has native expertise. Cost: two codebases, two teams, no shared logic.

**Flutter:** Best when pixel-perfect custom UI is required, when targeting multiple platforms including desktop and web, or when starting fresh with no existing native expertise. Weaknesses: different rendering model (does not use native widgets), Dart language learning curve, third-party library ecosystem smaller than React Native.

The right answer in an interview is "it depends on team expertise, feature requirements, and timeline constraints" followed by specific tradeoffs. Avoid declaring a winner.

---

## Testing in React Native

### Jest + React Native Testing Library

Unit and integration tests use Jest. React Native Testing Library (RNTL) renders components in a simulated environment and provides queries that mirror how users interact with the app (`getByText`, `getByRole`, `getByTestId`).

Key principles: test behavior, not implementation. Do not test that `setState` was called. Test that the UI updates correctly when an action is taken. Mock native modules that are not available in the Jest environment.

```javascript
test('shows loading state while fetching', async () => {
  render(<UserProfile userId="123" />);
  expect(screen.getByText('Loading...')).toBeTruthy();
  await waitForElementToBeRemoved(() => screen.queryByText('Loading...'));
  expect(screen.getByText('John Doe')).toBeTruthy();
});
```

### Detox for E2E Testing

Detox runs the actual app binary on a simulator or emulator and drives it programmatically. Unlike Jest + RNTL, Detox tests the entire stack including native code.

Detox synchronizes with the app automatically: it waits for animations to complete, network requests to resolve, and timers to fire before asserting. This eliminates most of the flakiness that plagues E2E tests.

Practical considerations: Detox tests are slow (each test can take 10-30 seconds), so keep the E2E suite small and focused on critical user paths. Run unit and integration tests for coverage breadth; use Detox for critical path confidence.

---

## Interview Preparation Checklist

- Understand both architectures and be able to explain why the New Architecture was necessary.
- Have a mental model of the three threads (JS, UI, Shadow) and when each one causes problems.
- Know when to reach for Reanimated vs. the Animated API.
- Be able to design an offline sync system with a reasonable conflict resolution strategy.
- Practice the list optimization walkthrough as a verbal answer — it appears in nearly every React Native interview.
- Know your deployment pipeline: what CodePush/EAS Update can and cannot update OTA.
- Understand platform-specific differences well enough to explain why a feature "works on iOS but not Android."

The candidates who stand out in React Native interviews are the ones who have debugged real production problems. If you have crash reports you investigated, performance regressions you resolved, or native modules you wrote, those stories are your strongest interview material. Prepare two or three of them in STAR format before the interview.
