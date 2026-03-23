---
title: "Advanced JavaScript Interview Guide: Closures, Prototypes, Event Loop, and Async Patterns"
description: "Deep dive JavaScript for senior interviews — closures, prototype chain, event loop, promises vs callbacks, generators, and the quirks that separate experts from beginners."
date: "2026-03-20"
category: "Programming Languages"
---

# Advanced JavaScript Interview Guide: Closures, Prototypes, Event Loop, and Async Patterns

Advanced JavaScript interviews separate engineers who've shipped production JavaScript from those who know the surface syntax. Interviewers probe the language's quirky corners: the event loop, closures, `this` binding, prototype inheritance, and the async model. Here's what to master.

## The Event Loop

JavaScript is single-threaded — one call stack. The event loop allows non-blocking I/O by processing callbacks when the call stack is empty.

**Execution order:** Synchronous code runs first (call stack). Then microtasks (Promise `.then`, `queueMicrotask`, `MutationObserver`). Then macrotasks (setTimeout, setInterval, I/O callbacks, requestAnimationFrame).

```javascript
console.log('1')
setTimeout(() => console.log('4'), 0)  // macrotask
Promise.resolve().then(() => console.log('3'))  // microtask
console.log('2')
// Output: 1, 2, 3, 4
```

Key insight: Promises resolve before setTimeout even with `setTimeout(fn, 0)`. Microtasks drain completely before the next macrotask begins.

**Blocking the event loop:** A long synchronous operation (computing Fibonacci of 50, parsing a huge JSON) blocks all other callbacks. In browsers: UI freezes. In Node.js: all concurrent requests stall. Use Web Workers (browser) or Worker Threads (Node.js) for CPU-bound work.

## Closures

A closure is a function that retains access to its outer scope after the outer function has returned. This is JavaScript's key mechanism for data encapsulation.

```javascript
function makeCounter() {
  let count = 0;
  return {
    increment: () => ++count,
    decrement: () => --count,
    value: () => count
  };
}

const counter = makeCounter();
counter.increment(); // 1
counter.increment(); // 2
counter.decrement(); // 1
counter.value();     // 1
// count is private — not accessible from outside
```

**Classic closure bug (loop + setTimeout):**
```javascript
// BUG: all log "3"
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}

// Fix 1: let (block scope)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);  // 0, 1, 2
}

// Fix 2: IIFE closure
for (var i = 0; i < 3; i++) {
  ((j) => setTimeout(() => console.log(j), 0))(i);
}
```

## Prototype Chain

JavaScript uses prototypal inheritance, not classical inheritance. Every object has a hidden `[[Prototype]]` link (accessible as `__proto__` or via `Object.getPrototypeOf`).

```javascript
const animal = { eat() { return 'eating'; } };
const dog = Object.create(animal);
dog.bark = function() { return 'woof'; };

dog.bark();       // 'woof' — own property
dog.eat();        // 'eating' — from prototype
dog.hasOwnProperty('bark');  // true
dog.hasOwnProperty('eat');   // false — inherited
```

ES6 `class` syntax is syntactic sugar over prototypes. `class Dog extends Animal {}` sets `Dog.prototype.__proto__ = Animal.prototype`.

**instanceof:** Checks the prototype chain. `dog instanceof Animal` is true if `Animal.prototype` appears anywhere in `dog`'s prototype chain.

## `this` Binding

`this` is one of JavaScript's most confusing features because its value depends on how a function is called, not where it's defined (except for arrow functions).

Rules (in priority order):
1. `new` call: `this` is the newly created object
2. Explicit binding: `call`, `apply`, `bind` set `this` explicitly
3. Implicit binding: `obj.method()` — `this` is `obj`
4. Default binding: bare function call — `this` is `undefined` (strict mode) or `window`/`global`

**Arrow functions:** Lexically bound `this` — they inherit `this` from the enclosing scope at definition time. Arrow functions cannot have their `this` rebound.

```javascript
const obj = {
  name: 'Alice',
  greet: function() {
    // this = obj
    setTimeout(function() {
      console.log(this.name);  // undefined — this is window/undefined
    }, 0);
    
    setTimeout(() => {
      console.log(this.name);  // 'Alice' — arrow function inherits this
    }, 0);
  }
};
```

## Promises and Async/Await

**Promise chain vs async/await:** Both handle async operations; async/await is syntactic sugar over Promises.

```javascript
// Callback hell
getData(id, (err, data) => {
  if (err) handle(err);
  else processData(data, (err, result) => {
    // ...
  });
});

// Promise chain
getData(id)
  .then(data => processData(data))
  .then(result => saveResult(result))
  .catch(err => handle(err));

// Async/await
async function workflow(id) {
  try {
    const data = await getData(id);
    const result = await processData(data);
    await saveResult(result);
  } catch (err) {
    handle(err);
  }
}
```

**Parallel vs. sequential:** `await` inside a loop is sequential. For parallel:
```javascript
// Sequential (slow)
for (const id of ids) {
  await process(id);
}

// Parallel (fast)
await Promise.all(ids.map(id => process(id)));

// Parallel with concurrency limit
// Use p-limit library or implement a semaphore
```

**Promise.all vs. Promise.allSettled vs. Promise.race:**
- `all`: resolves when all resolve; rejects on first rejection
- `allSettled`: resolves when all complete (success or failure), returns all results
- `race`: resolves/rejects with the first to complete

## WeakMap and WeakRef

`WeakMap` holds weak references to keys — if the key object is garbage collected, the entry is removed. Use for: private data associated with DOM nodes (avoiding memory leaks when DOM elements are removed), caching computed values for objects.

```javascript
const privateData = new WeakMap();

class User {
  constructor(name) {
    privateData.set(this, { name, createdAt: Date.now() });
  }
  getName() {
    return privateData.get(this).name;
  }
}
```

These advanced topics signal genuine production JavaScript experience. They appear in senior JavaScript interviews at companies where JavaScript is core infrastructure (Node.js backends, browser performance-critical applications).
