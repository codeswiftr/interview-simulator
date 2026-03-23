---
title: "Java Engineering Interview Guide"
description: "Java-specific interview questions covering the JVM, garbage collection, concurrency, Spring, and what companies like Amazon, Oracle, and financial institutions ask about Java."
date: "2026-03-19"
category: "Backend Engineering"
---

# Java Engineering Interview Guide

Java remains the dominant language at enterprise companies, financial institutions, Android development, and many large-scale distributed systems. If you are interviewing for a Java-heavy role at Amazon, Goldman Sachs, JPMorgan, Oracle, LinkedIn, or a company running Spring-based microservices, this guide covers what those interviews actually test.

## The JVM: What Interviewers Test

Java interviews at senior levels routinely include JVM internals questions. Not to be pedantic, but because JVM understanding predicts your ability to diagnose production performance issues.

**Garbage collection**: Know the difference between GC algorithms and their trade-offs:

- **Serial GC**: Single-threaded, stop-the-world. Only for small heaps on single-processor systems.
- **Parallel GC (Throughput Collector)**: Multi-threaded GC, still stop-the-world. Good for batch processing where throughput matters more than latency.
- **G1 GC (Garbage First)**: Default since JDK 9. Divides heap into regions, can do concurrent marking, targets predictable pause times. Good general-purpose choice.
- **ZGC / Shenandoah**: Near-pause-free collectors. Handles heaps of many terabytes with sub-millisecond pauses. Use when latency SLAs are tight.

Interview question: "Your service has unpredictable latency spikes. How would you investigate?" Expected answer includes: check GC logs (`-Xlog:gc*`), look for long stop-the-world pauses, consider switching to G1 or ZGC, tune heap size to reduce GC frequency.

**JVM memory model**: Heap vs non-heap (metaspace, stack, code cache). Understanding that `OutOfMemoryError: Metaspace` is different from `OutOfMemoryError: Java heap space` — and how to tune each — is a common senior interview topic.

## Java Concurrency: The Core Interview Topic

Java concurrency is one of the most tested areas in Java interviews. Companies building high-throughput services care whether you understand the Java Memory Model and can write correct concurrent code.

**synchronized vs Lock**: `synchronized` is simpler and holds a monitor lock. `ReentrantLock` gives you tryLock (with timeout), lockInterruptibly, and explicit fairness. Use `Lock` when you need these features; otherwise `synchronized` is cleaner.

**volatile vs AtomicXxx**: `volatile` guarantees visibility (no CPU cache inconsistency) but not atomicity. `AtomicInteger.incrementAndGet()` is atomic via CAS (compare-and-swap). Interview question: "Why is `i++` not thread-safe even if `i` is volatile?" Answer: `i++` is read-modify-write — three operations that can be interleaved.

**java.util.concurrent**: Know the key classes:
- `ConcurrentHashMap`: Segment-based locking (pre-Java 8) / CAS + synchronized per bucket (Java 8+). Far better than `Collections.synchronizedMap()` under contention.
- `BlockingQueue`: Thread-safe producer-consumer queue. `ArrayBlockingQueue` (bounded), `LinkedBlockingQueue` (optionally bounded), `SynchronousQueue` (handoff, no buffering).
- `ExecutorService` and `CompletableFuture`: Thread pool management and async composition. Senior interviewers expect fluency with `CompletableFuture.thenCompose`, `thenCombine`, and exception handling chains.

**The volatile double-checked locking pattern**:

```java
// Classic pattern for lazy initialization — volatile is required
private volatile Singleton instance;

public Singleton getInstance() {
    if (instance == null) {
        synchronized (this) {
            if (instance == null) {
                instance = new Singleton();  // volatile ensures construction is visible
            }
        }
    }
    return instance;
}
```

Interviewers ask why `volatile` is required. Without it, the JVM can reorder instructions: another thread may see a non-null but incompletely constructed object.

## Spring Framework: What Enterprise Interviews Test

For Spring-heavy roles, expect questions on:

**Dependency Injection and IoC**: The difference between constructor injection (preferred — makes dependencies explicit, enables immutability) and field injection (discouraged — hides dependencies, complicates testing). Interviewers at enterprise companies often ask why you prefer constructor injection.

**Spring Boot auto-configuration**: How `@SpringBootApplication` composes `@Configuration`, `@EnableAutoConfiguration`, and `@ComponentScan`. What happens when you need to override an auto-configured bean. The `@ConditionalOnMissingBean` pattern.

**Transaction management**: `@Transactional` propagation levels — particularly `REQUIRED` (join existing or create new), `REQUIRES_NEW` (always new transaction), and `NOT_SUPPORTED` (suspend transaction). Interview question: "Why might a `@Transactional` annotation not work?" Common answers: method called within the same bean (Spring proxies only intercept external calls), method is not public, or the bean was not loaded through Spring context.

**Spring Data JPA and N+1**: The N+1 problem with lazy loading — fetching a list of entities and then triggering individual queries for each related entity. Solution: `@EntityGraph`, `JOIN FETCH` in JPQL, or `@BatchSize`.

## Java at Scale: What Large Systems Interviews Cover

**Java serialization alternatives**: Native Java serialization is slow and fragile. Production systems use Protobuf, Avro, Kryo, or Jackson. Interviewers ask why, and the answers are: size (binary > JSON), speed, and schema evolution.

**Profile before optimizing**: Java performance questions often start with "my service is slow." The correct answer is always: profile first (JFR/JProfiler/async-profiler), then optimize. Common hotspots: string concatenation in loops (use StringBuilder), autoboxing in tight loops, excessive object creation driving GC.

**Module system (JPMS)**: Introduced in Java 9. Interviewers at companies that have modernized their Java (post-JDK 9) may ask about module descriptors, encapsulation improvements, and migration challenges from classpath to modulepath.

## What to Study

- **Java Concurrency in Practice (Goetz)**: The definitive book on Java concurrency — interviewers at financial firms and Amazon know this book well
- **Effective Java (Bloch)**: Item-by-item best practices that senior interviewers reference directly
- **JVM Internals series (Shipilev)**: For senior/principal roles where JVM depth is tested
- **Spring documentation**: The reference documentation for Spring Framework and Spring Boot is comprehensive — the auto-configuration and data sections are most interview-relevant
