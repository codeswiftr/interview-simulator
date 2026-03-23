---
title: "Java Backend Advanced Interview: JVM Internals, Spring Boot, and Microservices"
description: "Prepare for senior Java backend interviews with deep coverage of JVM internals, garbage collection algorithms, Spring Boot architecture, reactive programming with WebFlux, Java 21 virtual threads, and real interview Q&A."
date: "2026-03-20"
category: "Technical Skills"
---

# Java Backend Advanced Interview: JVM Internals, Spring Boot, and Microservices

Senior Java backend interviews probe well below the surface of framework usage. Interviewers at companies with mature Java codebases—banks, payments companies, enterprise SaaS—expect you to explain what happens inside the JVM, reason about threading models, and make architectural decisions about microservices with justification. This guide covers the areas that separate senior candidates from mid-level ones.

## JVM Internals: Garbage Collection

Garbage collection is the most common JVM topic in senior interviews. You should understand the mechanics of at least three algorithms.

**G1GC** (Garbage-First, default since Java 9) divides heap memory into equal-sized regions and prioritizes collecting the regions with the most garbage first. It aims to meet a configurable pause time target (`-XX:MaxGCPauseMillis`) and performs most work concurrently with the application. G1 is the right default for most applications.

**ZGC** (available since Java 15, production-ready since Java 17) is a low-latency collector designed to keep stop-the-world pauses under 1ms regardless of heap size. It uses colored pointers and load barriers to perform relocation concurrently. When to use it: latency-sensitive services where even G1's pause variance is unacceptable.

**Interview question:** "Our service has 64GB heap and we're seeing 200ms pause spikes during GC. What would you look at?" A strong answer covers: G1 region sizing, promotion failure rates (old gen filling up faster than concurrent GC completes), consideration of ZGC migration, and whether the heap is actually appropriately sized for the working set.

## JIT Compilation and Performance

The JVM interprets bytecode initially, then uses JIT compilation to translate hot code paths into native machine code. The tiered compilation model (C1 for quick compilation, C2 for heavily optimized code) means a Java service has a "warm-up" period before it reaches peak performance.

This matters in interviews when discussing Kubernetes pod scaling: new pods start cold and may handle requests poorly for 30-90 seconds. Mitigation strategies include application prewarming (sending synthetic traffic before adding to load balancer), using GraalVM Native Image for ahead-of-time compilation (eliminating warm-up at the cost of JIT's runtime adaptability), and Project CRaC (Coordinated Restore at Checkpoint) for restoring from a pre-warmed snapshot.

## Spring Boot Architecture

Interviewers expect you to explain dependency injection beyond "Spring manages beans." The container creates a directed acyclic graph of beans, resolves dependencies via constructor injection (preferred) or setter/field injection, and manages bean lifecycle. Constructor injection is superior because it makes dependencies explicit, supports immutability, and allows the class to be unit-tested without a Spring context.

**Auto-configuration** is Spring Boot's mechanism for opinionated defaults. When you add `spring-boot-starter-data-jpa` to the classpath, `HibernateJpaAutoConfiguration` detects the presence of Hibernate and creates a `DataSource`, `EntityManagerFactory`, and `TransactionManager` if none are already defined. The `@ConditionalOnMissingBean` pattern is central: auto-configuration only activates when you haven't provided your own.

**Actuator** exposes operational endpoints (`/actuator/health`, `/actuator/metrics`, `/actuator/prometheus`). In interviews, be ready to discuss which endpoints to expose externally (health, minimal info) versus internally on a management port (full metrics, env, beans). Exposing `/actuator/env` publicly leaks configuration details including secret names.

## Reactive Programming with WebFlux

Spring WebFlux uses Project Reactor and the `Publisher` contract from Reactive Streams. A `Mono<T>` represents 0-1 items; a `Flux<T>` represents 0-N. The key conceptual point for interviews: reactive programming is not about concurrency—it's about non-blocking I/O. You can run reactive code on a single thread if all operations are non-blocking.

When does WebFlux make sense? When your service is I/O-bound, performs many parallel remote calls, and thread pool exhaustion under load is a real concern. When does it not make sense? CPU-bound work does not benefit, and traditional blocking Spring MVC is significantly simpler to debug and reason about.

A common interview trap: "What happens if you call a blocking method inside a reactive chain?" The answer: it blocks the small pool of Netty event loop threads, potentially stalling the entire service under load. The mitigation is to wrap blocking calls with `Schedulers.boundedElastic()` to offload them to a dedicated thread pool.

## Java Concurrency: CompletableFuture and Virtual Threads

`CompletableFuture` enables asynchronous composition: `thenApply` transforms a result, `thenCompose` chains dependent futures, `allOf` waits for multiple futures. Error handling uses `exceptionally` or `handle`. The common gotcha: `thenApply` runs on the completing thread by default, which may be the common pool. For I/O-heavy work, always pass an explicit executor: `thenApplyAsync(fn, ioExecutor)`.

**Virtual threads** (stable in Java 21, Project Loom) are the most significant Java concurrency advancement in years. They are lightweight threads managed by the JVM, not the OS. A JVM can maintain millions of virtual threads with minimal memory overhead (roughly 1KB each vs. ~1MB for platform threads). The key benefit: you can write blocking code (no reactive boilerplate) and still achieve the throughput that previously required reactive frameworks. For JDBC, file I/O, and HTTP client calls, virtual threads deliver near-reactive throughput with imperative code style.

**Sample interview question:** "How would you migrate a Spring MVC service from a fixed thread pool to virtual threads?" Answer: enable virtual threads in Spring Boot 3.2+ with `spring.threads.virtual.enabled=true`. That's the minimal change. The harder part is ensuring no pinned carriers: `synchronized` blocks holding virtual threads on their carrier platform thread prevent unmounting and must be replaced with `ReentrantLock`.

## Microservices Architecture Q&A

**Q: How do you handle distributed transactions across microservices?**
Avoid two-phase commit in practice. Prefer the Saga pattern: either choreography (services emit events that trigger compensating actions) or orchestration (a central coordinator calls services and issues rollback commands on failure). The trade-off is eventual consistency: business logic must tolerate temporary inconsistency.

**Q: When would you choose Kafka over REST for inter-service communication?**
Kafka when: you need event replay/audit, consumer services need to process at their own pace, or you need fan-out to multiple consumers. REST when: you need synchronous response, the operation has a clear request/response contract, or event ordering and durability are not required.

---
