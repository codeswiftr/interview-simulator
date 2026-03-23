---
title: "Spring Boot 4 Reactive Guide"
description: "Building reactive Spring Boot 4 applications—WebFlux, Project Reactor, R2DBC for reactive database access, and when reactive Spring makes sense vs blocking Spring MVC."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Spring Boot 4 Reactive Guide

Spring Boot 4 with WebFlux and Project Reactor provides a fully non-blocking reactive programming model for Java applications. Understanding reactive Spring is increasingly required for senior Java engineers, particularly in high-throughput microservice architectures.

## Reactive vs Blocking Spring

**Spring MVC (blocking)**: Each request occupies a thread while waiting for I/O. With Java 21 Virtual Threads, blocking I/O is no longer a scalability concern—virtual threads handle it cheaply.

**Spring WebFlux (reactive)**: Non-blocking, reactive streams. A small thread pool handles all requests. Requires reactive database drivers (R2DBC, reactive MongoDB) and reactive thinking throughout.

**When to use WebFlux in 2026**: Mostly when you need streaming (server-sent events, large data streaming), or when you're in a fully reactive ecosystem. For most CRUD applications, Spring MVC + Virtual Threads is simpler and equally performant.

## WebFlux Basics

```java
@RestController
@RequestMapping("/users")
public class UserController {

    private final UserRepository userRepository;

    // Mono<T> = 0 or 1 item
    @GetMapping("/{id}")
    public Mono<ResponseEntity<User>> getUser(@PathVariable Long id) {
        return userRepository.findById(id)
            .map(user -> ResponseEntity.ok(user))
            .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    // Flux<T> = 0 to N items (stream)
    @GetMapping
    public Flux<User> getAllUsers() {
        return userRepository.findAll();
    }

    @PostMapping
    public Mono<ResponseEntity<User>> createUser(@RequestBody @Valid UserCreateRequest request) {
        return userRepository.save(new User(request.name(), request.email()))
            .map(user -> ResponseEntity.status(HttpStatus.CREATED).body(user));
    }
}
```

## Project Reactor Operators

```java
// Transform values
Mono<String> name = Mono.just(1)
    .map(id -> "User " + id);

// Async transform (flatMap when the mapper returns Mono/Flux)
Mono<User> user = Mono.just(userId)
    .flatMap(id -> userRepository.findById(id));

// Combine multiple sources
Mono<UserProfile> profile = Mono.zip(
    userRepository.findById(userId),
    settingsRepository.findByUserId(userId)
).map(tuple -> new UserProfile(tuple.getT1(), tuple.getT2()));

// Error handling
Mono<User> safeUser = userRepository.findById(userId)
    .switchIfEmpty(Mono.error(new UserNotFoundException(userId)))
    .onErrorReturn(DatabaseException.class, User.anonymous());

// Filtering
Flux<User> activeUsers = userRepository.findAll()
    .filter(User::isActive)
    .take(100);  // Backpressure: only take 100
```

## R2DBC for Reactive Database Access

```java
// Spring Data R2DBC repository
public interface UserRepository extends ReactiveCrudRepository<User, Long> {
    Flux<User> findByEmail(String email);

    @Query("SELECT * FROM users WHERE created_at > :since ORDER BY created_at DESC")
    Flux<User> findRecentUsers(@Param("since") LocalDateTime since);
}

// Reactive transaction management
@Transactional
public Mono<Order> processOrder(CreateOrderRequest request) {
    return userRepository.findById(request.userId())
        .flatMap(user -> {
            Order order = new Order(user, request.items());
            return orderRepository.save(order)
                .flatMap(savedOrder ->
                    inventoryService.reserve(savedOrder.items())
                        .thenReturn(savedOrder)
                );
        });
}
```

## Server-Sent Events

WebFlux shines for streaming data to clients:

```java
@GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> streamEvents() {
    return Flux.interval(Duration.ofSeconds(1))
        .map(sequence -> ServerSentEvent.<String>builder()
            .id(String.valueOf(sequence))
            .event("stock-update")
            .data("AAPL:" + getStockPrice())
            .build());
}

// Real-time order tracking
@GetMapping(value = "/orders/{id}/status", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<OrderStatus> trackOrder(@PathVariable Long id) {
    return orderStatusService.statusStream(id)
        .takeUntil(status -> status == OrderStatus.DELIVERED);
}
```

## Reactive Security

```java
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        return http
            .authorizeExchange(exchanges -> exchanges
                .pathMatchers("/api/public/**").permitAll()
                .pathMatchers("/api/admin/**").hasRole("ADMIN")
                .anyExchange().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(Customizer.withDefaults())
            )
            .csrf(csrf -> csrf.disable())
            .build();
    }
}
```

## Testing Reactive Code

```java
@Test
void getUserReturnsUser() {
    // StepVerifier is the standard way to test reactive streams
    StepVerifier.create(userService.getUser(1L))
        .expectNextMatches(user -> user.id().equals(1L))
        .verifyComplete();
}

@Test
void getAllUsersReturnsAllUsers() {
    StepVerifier.create(userService.getAllUsers())
        .expectNextCount(3)
        .verifyComplete();
}

@Test
void getNonExistentUserThrowsError() {
    StepVerifier.create(userService.getUser(999L))
        .expectError(UserNotFoundException.class)
        .verify();
}
```

## Interview Tips

Reactive Spring interview questions:

1. **Mono vs Flux** — single vs multi-value reactive types
2. **map vs flatMap** — synchronous vs async transformation
3. **When to use WebFlux** — streaming, vs MVC + virtual threads for CRUD
4. **Backpressure** — Flux operators like `take()`, `limitRate()` for controlling flow
5. **StepVerifier** — how to test reactive code

The key interview insight: with Java 21 Virtual Threads, the reactive vs blocking debate for throughput has largely been settled—virtual threads handle blocking I/O cheaply. WebFlux is now primarily valuable for its streaming capabilities, not for raw throughput.
