---
title: "Advanced Express.js and Node.js Interview Guide: Middleware, Performance, and Production Patterns"
description: "Senior Node.js interview prep — Express middleware architecture, event loop, clustering, streams, performance optimization, and production patterns for high-traffic APIs."
date: "2026-03-20"
category: "Programming Languages"
---

# Advanced Express.js and Node.js Interview Guide: Middleware, Performance, and Production Patterns

Senior Node.js interviews go deep on the event loop, performance patterns, and production architecture. If you've only used Express to build CRUD APIs, you may struggle with questions about concurrency, memory management, and scalability. This guide covers the topics that separate junior Node.js developers from engineers who can build reliable, high-traffic systems.

## The Event Loop: What Interviewers Really Ask

Every Node.js interview eventually tests the event loop. The surface question is "how does Node.js handle concurrency without threads?" But interviewers want to know if you understand the implications.

Node.js is single-threaded — one call stack. The event loop allows non-blocking I/O by offloading operations (network, filesystem) to the OS or worker threads (libuv), then processing callbacks when they complete.

The event loop phases (in order): timers (setTimeout, setInterval), pending callbacks (I/O callbacks deferred from previous iteration), idle/prepare (internal), poll (retrieve new I/O events), check (setImmediate), close callbacks.

`setImmediate` runs after the current iteration's poll phase. `process.nextTick` runs before the next event loop iteration — it drains the nextTick queue after every phase. This is why `process.nextTick` can starve the event loop if called recursively; use it sparingly.

Practical implication: CPU-bound work blocks the event loop. A tight loop calculating something expensive prevents all other requests from being processed. Solutions: Worker Threads (CPU-bound work in separate threads), child processes, or offloading to separate services.

## Middleware Architecture

Express middleware is a function `(req, res, next) => void`. Understanding middleware ordering is fundamental:

- Application-level middleware: `app.use()` — runs for all routes
- Router-level middleware: `router.use()` — runs for routes in that router
- Error-handling middleware: four arguments `(err, req, res, next)` — must be registered after routes

Order matters: middleware runs in registration order. A common mistake is registering body parsers after route handlers.

```javascript
// Correct order
app.use(helmet())
app.use(express.json())
app.use(cors())
app.use('/api', apiRouter)
app.use(errorHandler)  // error middleware last
```

Writing reusable middleware — middleware factories:

```javascript
function rateLimit(options) {
  const store = new Map()
  return function(req, res, next) {
    const key = req.ip
    const now = Date.now()
    // ... rate limiting logic
    next()
  }
}

app.use(rateLimit({ windowMs: 60000, max: 100 }))
```

## Streams

Streams are fundamental for memory-efficient processing of large data. A Node.js stream is an abstraction for continuous data — readable, writable, duplex, or transform.

Key advantage: streaming doesn't buffer the entire payload in memory. For large file uploads, streaming to S3 or disk prevents OOM errors.

```javascript
const { pipeline } = require('stream/promises')
const fs = require('fs')
const zlib = require('zlib')

// Stream large file: read → gzip compress → write
await pipeline(
  fs.createReadStream('large-file.txt'),
  zlib.createGzip(),
  fs.createWriteStream('output.gz')
)
```

Interview: "How would you handle a 10GB file upload without running out of memory?" Answer: stream the request body directly to storage — `req.pipe(uploadStream)` — never buffering the full body in memory.

## Clustering and Worker Threads

**Cluster module:** Spawns multiple Node.js processes sharing the same port. Each worker is a separate process (separate event loop, separate memory). Master process distributes connections across workers. With N CPU cores, you can process N concurrent CPU-bound requests.

```javascript
if (cluster.isPrimary) {
  for (let i = 0; i < os.cpus().length; i++) {
    cluster.fork()
  }
} else {
  app.listen(3000)
}
```

**Worker Threads:** Unlike clustering, worker threads share memory via SharedArrayBuffer and can communicate via message passing. Best for parallelizing CPU-bound work within one process — image processing, cryptography, parsing.

Don't use Worker Threads for I/O-bound work — the event loop handles that efficiently already.

## Memory Management

Common sources of memory leaks in Node.js:
- **Closures holding references:** Event listeners that capture large objects in closure scope
- **Event emitter leaks:** Adding listeners without removing them — check `emitter.listenerCount()` in production
- **Global caches without eviction:** Maps/Sets that grow unboundedly

Debugging: `--inspect` flag for Chrome DevTools heap snapshots, `node --inspect-brk` for startup debugging, `v8.getHeapSnapshot()` programmatically.

Production memory monitoring: track `process.memoryUsage().heapUsed` and alert when it approaches the heap limit.

## Performance Patterns

**Connection pooling:** Never create a new database connection per request — use a pool. With pg or mysql2, configure `max` pool size to match your database connection limit (typically 10-20 per app instance).

**Response compression:** `compression` middleware for gzip. Skip for already-compressed content (images, video).

**Keep-Alive connections:** HTTP/1.1 keep-alive reduces TCP handshake overhead. Express enables this by default; ensure your proxy (nginx, ALB) also supports it.

**Caching:** Redis for session storage and application caching. In-memory LRU cache (`lru-cache`) for hot data within a single process.

**Async/await error handling:** Unhandled promise rejections crash Node.js (default behavior since v15). Wrap async route handlers or use a wrapper:

```javascript
const asyncHandler = fn => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next)

app.get('/user/:id', asyncHandler(async (req, res) => {
  const user = await User.findById(req.params.id)
  res.json(user)
}))
```

## Production Checklist

- **Process manager:** PM2 or systemd, not `node server.js` directly — handles restarts on crash
- **Graceful shutdown:** Listen for SIGTERM, stop accepting new connections, finish in-flight requests, then exit
- **Health check endpoint:** `/healthz` for load balancer probing — check DB connectivity
- **Structured logging:** JSON logs with pino or winston — avoid `console.log` in production
- **Security headers:** helmet middleware, no `X-Powered-By`, CORS configured tightly

These production patterns show interviewers you've shipped Node.js to production and understand the operational requirements, not just the programming model.
