---
title: "Node.js Backend Interview Guide: Event Loop, Streams, and Production Patterns"
description: "A comprehensive Node.js interview guide for backend engineers — covering the event loop in depth, streams, worker threads, cluster mode, common pitfalls, and the production patterns that interviewers at Node.js-heavy companies actually test."
date: "2026-03-20"
category: "Programming Languages"
---

# Node.js Backend Interview Guide: Event Loop, Streams, and Production Patterns

Node.js is simultaneously simple (JavaScript everywhere) and deeply nuanced (single-threaded, event-driven, non-blocking I/O). Interviews at companies that run Node.js in production test whether you genuinely understand the runtime or just know the API. The event loop is the single most tested topic — here's what you need to understand at depth.

## The Event Loop: The Actual Mental Model

Node.js is single-threaded in JavaScript execution but not in I/O. The underlying libuv library manages a thread pool (default 4 threads) for file system operations, DNS resolution, and crypto — but your JavaScript always runs on a single thread.

The event loop has phases, executed in order:

```
   ┌───────────────────────────┐
┌─>│           timers          │  ← setTimeout, setInterval callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     pending callbacks     │  ← I/O callbacks deferred from prev iteration
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │       idle, prepare       │  ← internal use
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │           poll            │  ← retrieve new I/O events; execute callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │           check           │  ← setImmediate callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
└──┤      close callbacks      │  ← socket.on('close', ...)
   └───────────────────────────┘
```

Between each phase (and between each callback in the timers phase), Node.js drains the **microtask queue**: `Promise` callbacks and `process.nextTick()` callbacks. `nextTick` always runs before `Promise` microtasks.

```javascript
// Order of execution — a classic interview question
console.log('1 - sync');

setTimeout(() => console.log('2 - setTimeout'), 0);
setImmediate(() => console.log('3 - setImmediate'));

Promise.resolve().then(() => console.log('4 - Promise'));
process.nextTick(() => console.log('5 - nextTick'));

console.log('6 - sync');

// Output:
// 1 - sync
// 6 - sync
// 5 - nextTick        ← microtask, runs before event loop phases
// 4 - Promise         ← microtask, after nextTick
// 2 - setTimeout      ← timers phase (may come before or after setImmediate)
// 3 - setImmediate    ← check phase
```

**Why `setTimeout(fn, 0)` vs `setImmediate` is non-deterministic:** When called from the main module (not inside an I/O callback), the order depends on OS timing. When called inside an I/O callback, `setImmediate` always fires before `setTimeout` — the poll phase precedes check but timers were already checked this iteration.

## The Critical Implication: Blocking the Event Loop

Since JavaScript executes on a single thread, **any synchronous CPU-intensive operation blocks all I/O**:

```javascript
// BAD: Blocks the event loop for the duration of the computation
app.get('/compute', (req, res) => {
    const result = fibonacci(45);  // Blocks for seconds
    res.json({ result });
    // All other requests are queued behind this one
});

// GOOD: Offload CPU work
app.get('/compute', async (req, res) => {
    const result = await computeInWorkerThread(fibonacci, 45);
    res.json({ result });
});
```

**What blocks the event loop:**
- Synchronous crypto operations (use async versions)
- JSON parsing of very large payloads
- Regex with catastrophic backtracking
- Synchronous file reads (`fs.readFileSync` in request handlers)
- Long-running loops or recursive computations

## Worker Threads

Worker threads (Node.js 10.5+, stable in 12+) provide true parallelism for CPU-intensive work:

```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

// main.js
function runInWorker(workerData) {
    return new Promise((resolve, reject) => {
        const worker = new Worker(__filename, { workerData });
        worker.on('message', resolve);
        worker.on('error', reject);
        worker.on('exit', (code) => {
            if (code !== 0) reject(new Error(`Worker exited with code ${code}`));
        });
    });
}

// Worker code (same file, different branch)
if (!isMainThread) {
    const { input } = workerData;
    const result = expensiveComputation(input);
    parentPort.postMessage(result);
}
```

Workers have separate heaps and V8 instances — no shared memory except `SharedArrayBuffer`. Communication via message passing. Worker pool libraries (like `workerpool` or `piscina`) manage a reusable pool of workers to avoid creation overhead.

## Streams

Streams are Node.js's solution to processing large amounts of data without loading everything into memory.

**Four stream types:**
- `Readable` — data source (file read, HTTP request body)
- `Writable` — data sink (file write, HTTP response)
- `Transform` — duplex, transforms data as it flows through (gzip, cipher)
- `Duplex` — bidirectional (TCP socket)

**The pipeline pattern** (proper error handling):

```javascript
const { pipeline } = require('stream/promises');
const fs = require('fs');
const zlib = require('zlib');

async function compressFile(input, output) {
    await pipeline(
        fs.createReadStream(input),
        zlib.createGzip(),
        fs.createWriteStream(output)
    );
    // pipeline handles error propagation and cleanup automatically
}
```

**Backpressure** is streams' core safety mechanism. When a writable stream's internal buffer fills, `write()` returns `false`. The readable should pause until the writable drains. The `pipeline` function handles backpressure automatically — this is why you should use `pipeline` instead of manual `.pipe()`.

**Common interview question:** "How would you process a 10GB CSV file?" — Stream it. Don't load it into memory. Use a readable stream + `readline` + a transform stream to process line by line.

```javascript
const readline = require('readline');
const fs = require('fs');

async function processLargeCSV(filePath) {
    const fileStream = fs.createReadStream(filePath);
    const rl = readline.createInterface({ input: fileStream });
    
    for await (const line of rl) {
        await processLine(line);  // Await prevents overwhelming downstream
    }
}
```

## Cluster Mode and Horizontal Scaling

A single Node.js process uses one CPU core. `cluster` module forks multiple processes sharing the same port:

```javascript
const cluster = require('cluster');
const os = require('os');

if (cluster.isPrimary) {
    const numCPUs = os.cpus().length;
    for (let i = 0; i < numCPUs; i++) {
        cluster.fork();
    }
    cluster.on('exit', (worker) => {
        console.log(`Worker ${worker.process.pid} died, restarting...`);
        cluster.fork();  // Auto-restart on crash
    });
} else {
    // Worker process: start your HTTP server here
    const app = require('./app');
    app.listen(3000);
}
```

**In production:** PM2 manages cluster mode more robustly with `pm2 start app.js -i max`. Kubernetes is the preferred approach at scale — run Node.js as single-process containers, scale horizontally with pods.

## Production Patterns

**Graceful shutdown:**
```javascript
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(async () => {
        await db.close();  // Drain connections
        process.exit(0);
    });
    // Force exit after 30s if graceful fails
    setTimeout(() => process.exit(1), 30000);
});
```

**Unhandled rejection handling:**
```javascript
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection:', reason);
    // In production: alert, then shutdown
    process.exit(1);
});
```

**Avoid callback hell with async/await:** Always promisify callback-based APIs. Use `util.promisify` or the `promises` sub-module (`fs.promises`, `dns.promises`).

## Common Interview Questions

**"What is the difference between `process.nextTick` and `setImmediate`?"** `nextTick` fires before any I/O events in the current iteration; `setImmediate` fires in the check phase after I/O. `nextTick` can starve I/O if called recursively — prefer `setImmediate` for recursion.

**"How do you handle CPU-intensive tasks in Node.js?"** Worker threads for computation; offload to a separate service (Python ML service, Go computation service) for heavy lifting; message queue (BullMQ + Redis) for background jobs.

**"What causes memory leaks in Node.js?"** Closures holding references, global variable accumulation, event listeners not removed (`emitter.removeListener`), circular references in non-WeakMap structures, stream buffers not consumed.

**"How would you debug high event loop lag?"** Use `perf_hooks` to measure event loop delay: `performance.eventLoopUtilization()`. Profile with `--prof` flag and process with `node --prof-process`. Use clinic.js for visual flame charts.

Understanding these patterns at depth — not just knowing the API — is what interviewers test when they're looking for engineers who can architect and maintain Node.js systems in production.
