---
title: "Java Virtual Threads: Production Guide"
description: "How Java's Virtual Threads (Project Loom) transform Java concurrency—the difference from platform threads, migrating blocking code, Spring Boot integration, and performance characteristics for high-throughput services."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Java Virtual Threads: Production Guide

Java 21 made Virtual Threads a permanent feature (Project Loom). Virtual Threads are lightweight threads managed by the JVM rather than the OS, enabling millions of concurrent operations without the overhead of traditional platform threads. This is the most significant Java concurrency development in decades.

## The Problem with Platform Threads

Traditional Java (and most languages): one OS thread per blocking operation. OS threads are expensive (~1MB per thread). A server handling 10,000 concurrent connections needs 10,000 threads. This limits scalability and requires complex async/reactive code.

The reactive workaround (WebFlux, Vert.x): non-blocking I/O with callbacks/reactive streams. This solves the thread problem but introduces accidental complexity — stack traces become incomprehensible, debugging is hard, and standard Java libraries can't be used.

## Virtual Threads: The Solution

Virtual Threads are cheap (~few KB each). You can create millions:

```java
// Create 1 million virtual threads — runs fine
List<Thread> threads = new ArrayList<>();
for (int i = 0; i < 1_000_000; i++) {
    Thread thread = Thread.ofVirtual().start(() -> {
        Thread.sleep(Duration.ofSeconds(1));
    });
    threads.add(thread);
}
// Blocks until all complete
for (Thread t : threads) t.join();
```

Creating 1 million platform threads would exhaust memory. Virtual threads handle this trivially.

## How Virtual Threads Work

Virtual threads are multiplexed onto a small pool of carrier (platform) threads by the JVM:

1. Virtual thread makes a blocking call (I/O, sleep, lock)
2. JVM unmounts the virtual thread from its carrier thread
3. Carrier thread picks up another ready virtual thread
4. When I/O completes, the virtual thread is remounted

This is cooperative scheduling at the JVM level, transparent to the application code. Your blocking JDBC calls, HTTP clients, and file reads automatically yield when waiting.

## Using Virtual Threads

```java
// Spring Boot 3.2+: one config line enables virtual threads
@Configuration
class ThreadConfig {
    @Bean
    TomcatProtocolHandlerCustomizer<?> protocolHandlerCustomizer() {
        return handler -> handler.setExecutor(
            Executors.newVirtualThreadPerTaskExecutor()
        );
    }
}
```

Or globally in application.properties:
```
spring.threads.virtual.enabled=true
```

Every HTTP request now runs on a virtual thread — no reactive code needed.

## Blocking Code Works as Expected

```java
// This works correctly with virtual threads
// No reactive/async needed
@Service
public class UserService {
    public User createUser(CreateUserRequest request) {
        // Blocking DB call — virtual thread yields while waiting
        User user = userRepository.save(new User(request.email()));

        // Blocking HTTP call — virtual thread yields while waiting
        emailClient.sendWelcomeEmail(user.email());

        // Blocking cache call — virtual thread yields while waiting
        cacheService.put("user:" + user.id(), user);

        return user;
    }
}
```

With platform threads, each of these blocking calls holds the thread. With virtual threads, the JVM switches to other work while waiting for I/O.

## Performance Comparison

Benchmark: API server, each request does 3 DB queries (100ms each combined):

| Thread Model | Throughput (req/s) |
|-------------|-------------------|
| Platform threads (200 thread pool) | 2,000 |
| Reactive (WebFlux) | 20,000 |
| Virtual threads | 18,000 |

Virtual threads match reactive performance without reactive complexity.

## Structured Concurrency with Virtual Threads

Java 21+ includes structured concurrency, similar to Swift/Kotlin:

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Future<User> userFuture = scope.fork(() -> userService.getUser(id));
    Future<Order[]> ordersFuture = scope.fork(() -> orderService.getOrders(id));

    scope.join().throwIfFailed();  // Wait for both

    User user = userFuture.resultNow();
    Order[] orders = ordersFuture.resultNow();

    return new UserProfile(user, orders);
}
```

Both tasks run concurrently. If either fails, the other is cancelled automatically.

## Pinning: The Main Caveat

Virtual threads can be "pinned" to a carrier thread (can't yield) in two cases:
1. Inside `synchronized` blocks
2. When calling native code

Pinned virtual threads behave like platform threads—defeats the purpose. Migrate `synchronized` to `ReentrantLock`:

```java
// Before (pins the virtual thread)
synchronized (lock) {
    sharedResource.update();
}

// After (allows virtual thread to yield)
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    sharedResource.update();
} finally {
    lock.unlock();
}
```

## Interview Tips

Virtual threads questions are common for senior Java engineers:

1. **Why virtual threads vs reactive** — same performance, but imperative code is simpler
2. **How the JVM unmounts virtual threads** — cooperative scheduling on carrier threads
3. **Pinning and when to use ReentrantLock** — the main gotcha
4. **Spring Boot integration** — single configuration line
5. **Structured concurrency** — StructuredTaskScope for parallel tasks

The core interview insight: Virtual Threads don't improve performance of CPU-bound work. They specifically improve throughput for I/O-bound, blocking applications—which describes most enterprise Java services.
