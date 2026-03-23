---
title: "Java Spring Boot Interview Guide: Dependency Injection, JPA, and Microservices Patterns"
description: "A comprehensive guide to Java Spring Boot interview preparation — covering core DI concepts, JPA performance pitfalls, transaction management, and the microservices patterns that senior Java engineers are expected to know."
date: "2026-03-20"
category: "Programming Languages"
---

# Java Spring Boot Interview Guide: Dependency Injection, JPA, and Microservices Patterns

Java remains the dominant language in enterprise engineering and financial services. Spring Boot is the framework of choice for microservices at companies ranging from UBS and Deutsche Bank to Netflix and Airbnb. Senior Java interviews go well beyond syntax — they test your understanding of the framework's internals, JPA's behavior under load, and the patterns that distinguish a system that works in development from one that holds up in production.

This guide focuses on the areas where senior candidates most often fall short.

## Dependency Injection: Beyond the Basics

Spring's IoC container is the foundation of the framework. Interviewers expect you to understand more than "annotate with `@Autowired`."

**Constructor injection vs. field injection:**

Field injection (`@Autowired` on a field) is convenient but considered bad practice:
- It makes the class impossible to instantiate without a Spring context (breaks unit testing)
- It hides dependencies (you can't tell what a class needs by looking at its constructor)
- It prevents the `final` keyword on fields

Constructor injection is the current best practice:
```java
@Service
public class OrderService {
    private final InventoryService inventoryService;
    private final PaymentService paymentService;

    public OrderService(InventoryService inventoryService, PaymentService paymentService) {
        this.inventoryService = inventoryService;
        this.paymentService = paymentService;
    }
}
```

Spring auto-wires constructor parameters when there's a single constructor. The `@Autowired` annotation is optional in this case.

**Bean scopes:**

Interviewers frequently ask about scope mismatches. The default scope is singleton — one instance per application context. Injecting a prototype-scoped bean into a singleton is a common bug: the prototype bean is created once and injected at startup, negating the prototype behavior.

Solutions: inject via `ApplicationContext.getBean()`, use `@Lookup` method injection, or use `ObjectProvider<T>`.

**`@Component` vs. `@Service` vs. `@Repository`:**

All three are specializations of `@Component` with identical behavior, but:
- `@Repository` enables automatic persistence exception translation (Spring wraps provider-specific exceptions into `DataAccessException`)
- `@Service` and `@Component` are semantically identical but signal intent
- Use the semantically appropriate annotation — interviewers notice when you default to `@Component` everywhere

## JPA and Hibernate: The Performance Traps

JPA is where Java interviews find the most differentiation. Candidates who know the theory but haven't debugged JPA in production almost always expose themselves in these areas.

**The N+1 query problem:**

The most common JPA performance issue. When you load a list of entities with a `@OneToMany` relationship and access the collection lazily, Hibernate issues one query per parent entity to load the children.

```java
List<Order> orders = orderRepository.findAll(); // 1 query
for (Order order : orders) {
    System.out.println(order.getItems().size()); // N queries — one per order
}
```

Solutions:
1. **JOIN FETCH in JPQL:** `SELECT o FROM Order o JOIN FETCH o.items` — fetches in a single query
2. **`@EntityGraph`:** Declaratively specify associations to fetch eagerly for a specific query
3. **Batch size:** `@BatchSize(size = 20)` on the collection — fetches in batches of 20 instead of one at a time

The interview follow-up: what's the downside of JOIN FETCH? It can produce a Cartesian product if you fetch multiple collections simultaneously, inflating the result set. Use `@EntityGraph` or separate queries for multiple collections.

**Transaction propagation:**

`@Transactional` has a `propagation` attribute that most candidates understand only at the surface level:

- `REQUIRED` (default): join the existing transaction, or create one if none exists
- `REQUIRES_NEW`: always create a new transaction, suspending the existing one
- `NESTED`: create a savepoint within the existing transaction

Common interview scenario: you call a `@Transactional(propagation = REQUIRES_NEW)` method from within another `@Transactional` method. Does the inner transaction see uncommitted changes from the outer? No — the outer transaction is suspended, and the inner runs independently.

**The self-invocation problem:**

Spring's transactional behavior is proxy-based. If a `@Transactional` method calls another `@Transactional` method in the same class, Spring's proxy is bypassed and the annotation has no effect. This is a common source of subtle bugs.

Solution: inject the bean into itself (dirty but works), use `ApplicationContext.getBean()`, or refactor to a separate class.

## Spring Boot Auto-Configuration

Senior candidates should understand how `@SpringBootApplication` works:

- `@EnableAutoConfiguration` enables Spring Boot's auto-configuration mechanism
- Auto-configuration classes are loaded via `spring.factories` (pre-3.x) or `AutoConfiguration.imports` (3.x+)
- Each auto-configuration class uses `@ConditionalOnClass`, `@ConditionalOnMissingBean`, etc. to decide whether to apply

**Interview question:** "How does Spring Boot know to configure a `DataSource` without any explicit bean definition?"

Answer: `DataSourceAutoConfiguration` is on the classpath. It uses `@ConditionalOnClass(DataSource.class)` (satisfied if a JDBC driver is present) and `@ConditionalOnMissingBean(DataSource.class)` (only activates if you haven't defined your own). It reads `spring.datasource.*` properties.

## Microservices Patterns in Spring

For senior roles, Spring interviews often include microservices architecture questions:

**Circuit Breaker (Resilience4j):**

Spring Cloud integrates with Resilience4j for circuit breaker patterns. Know the three states: Closed (normal operation), Open (failing fast, no requests to downstream), Half-Open (limited requests to test recovery). Interviewers ask about the transition thresholds and why half-open is necessary.

**Distributed tracing:**

Micrometer Tracing (formerly Spring Cloud Sleuth) propagates trace IDs across service boundaries. For interviews: know that trace IDs are injected into outgoing HTTP headers (`traceparent` in W3C trace context format) and extracted by downstream services.

**Externalized configuration:**

Spring Cloud Config Server, Kubernetes ConfigMaps, or AWS Parameter Store patterns. The key interview point: Spring's `@RefreshScope` allows beans to reload configuration at runtime without restart, but has performance implications (bean re-creation on every refresh).

## Common Interview Failure Points

1. **Not knowing lazy vs. eager loading defaults:** `@OneToMany` defaults to LAZY, `@ManyToOne` defaults to EAGER. Many candidates get this backwards.
2. **Ignoring transaction isolation levels:** Know READ_COMMITTED vs. REPEATABLE_READ and when dirty reads, phantom reads, or non-repeatable reads become a problem.
3. **Spring Security filter chain:** For companies that do security work, not knowing how `OncePerRequestFilter` and `SecurityFilterChain` interact will hurt you.
4. **JVM memory and GC:** Senior Java roles expect you to discuss heap sizing, G1GC vs. ZGC for low-latency applications, and how to read a GC log.

Spring Boot expertise is deep — candidates who treat it as "just annotations" hit ceilings quickly. The engineers who stand out are those who can explain what Spring does on their behalf and why.
