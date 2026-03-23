---
title: "NestJS Backend Interview Guide: Architecture, Decorators, and Production Patterns"
description: "NestJS interview preparation — modules, providers, dependency injection, interceptors, guards, pipes, and how to architect scalable Node.js services with NestJS."
date: "2026-03-20"
category: "Backend"
---

# NestJS Backend Interview Guide: Architecture, Decorators, and Production Patterns

NestJS has become the dominant opinionated Node.js framework for backend services at scale. Its Angular-inspired architecture brings structure to the historically unstructured Node.js ecosystem, and its TypeScript-first approach makes it popular at engineering organizations that care about maintainability. If you are interviewing for a Node.js backend role in 2026, there is a good chance NestJS is in the stack.

## The NestJS Module System

NestJS applications are composed of **modules** — logical groupings of related functionality. Every application has a root `AppModule`. Feature modules encapsulate a domain: a `UsersModule` bundles the users controller, service, and any data-access providers together.

The `@Module()` decorator accepts four arrays: `imports` (other modules whose exports you need), `controllers` (route handlers), `providers` (services, repositories, guards, etc.), and `exports` (providers from this module that other modules can inject).

Why this matters in interviews: the module boundary defines the dependency graph. Circular dependencies between modules are a common real-world problem — NestJS provides `forwardRef()` as an escape hatch, but interviewers will probe whether you recognize that circular dependencies signal a design problem worth solving structurally.

## Providers and Dependency Injection

Providers are the core building block of NestJS logic. Any class decorated with `@Injectable()` can be registered as a provider. NestJS uses constructor-based DI: you declare dependencies in the constructor, and the IoC container resolves them.

Providers have scopes: **Singleton** (default — one instance per application), **Request** (one instance per incoming request, useful for per-request state like the current user), and **Transient** (new instance every time it is injected). Most services should be singletons. Request scope has a performance cost (the entire dependency chain must be instantiated per request) — only use it when necessary.

**Custom providers** are a frequent interview topic. You can register a provider using a factory function (`useFactory`), an existing class under a different token (`useExisting`), or a plain value (`useValue`). This is how you inject configuration objects, database connections, or mock implementations in tests.

## Decorators: The Vocabulary of NestJS

NestJS leans heavily on TypeScript decorators. You should be fluent with:

- `@Controller('path')` — marks a class as a route handler prefix
- `@Get()`, `@Post()`, `@Put()`, `@Delete()`, `@Patch()` — HTTP method decorators
- `@Param()`, `@Query()`, `@Body()` — extract route params, query strings, and request body
- `@Injectable()` — marks a class as a provider
- `@Module()` — declares a module
- `@UseGuards()`, `@UseInterceptors()`, `@UsePipes()` — attach cross-cutting concerns

Custom decorators (`createParamDecorator`) let you extract and transform request data into a clean parameter. A `@CurrentUser()` decorator that extracts the authenticated user from the request is a canonical example.

## Interceptors, Guards, and Pipes

These three constructs form NestJS's middleware-like layer, but each has a distinct responsibility:

**Guards** answer "is this request allowed to proceed?" They implement `CanActivate` and return a boolean or observable. Use them for authentication (JWT validation) and authorization (role checks). Guards run after middleware but before interceptors and pipes.

**Pipes** transform and validate incoming data. The built-in `ValidationPipe` (backed by `class-validator` and `class-transformer`) is the standard way to validate DTOs. Applied globally, it ensures all incoming data is validated against your DTO class before the controller method runs. Key interview question: "How do you handle validation in NestJS?" — `ValidationPipe` with `whitelist: true` (strip unknown properties) and `forbidNonWhitelisted: true`.

**Interceptors** wrap the request/response cycle. They can transform the response, add logging, handle caching, or measure execution time. They implement `NestInterceptor` and use RxJS observables. A common pattern: a `TransformInterceptor` that wraps all responses in a `{ data: ..., status: ... }` envelope.

The execution order: middleware → guards → interceptors (before) → pipes → controller → interceptors (after) → exception filters.

## Database Integration: Prisma and TypeORM

NestJS is database-agnostic. The two dominant choices are TypeORM (the original NestJS-blessed ORM) and Prisma (the modern challenger).

**TypeORM** uses the Active Record and Repository patterns. Define entities with `@Entity()` and `@Column()` decorators. NestJS's `TypeOrmModule.forFeature([Entity])` makes repositories injectable. Downsides: the API is complex, and TypeScript types sometimes diverge from runtime behavior.

**Prisma** uses a separate schema file (`schema.prisma`) and generates a type-safe client. The NestJS Prisma pattern is typically a `PrismaService` that extends `PrismaClient` and handles connection lifecycle. Prisma's type safety is superior to TypeORM — the generated client types match the schema exactly. This is the recommended choice for new projects.

## Microservices with NestJS

NestJS has built-in support for microservice patterns via its `@nestjs/microservices` package. It supports multiple transports: TCP, Redis, MQTT, NATS, RabbitMQ, Kafka. You switch transports by changing the transport configuration without rewriting business logic.

The microservice patterns NestJS implements: request-response (the caller waits for a reply) and event-based (fire and forget). Decorators `@MessagePattern()` and `@EventPattern()` handle incoming messages.

For interviews at companies with microservice architectures, expect questions about how you would structure an NestJS monorepo (the Nx or NestJS CLI workspaces approach) and how services communicate.

## Common NestJS Interview Questions

- "How does NestJS's DI container work under the hood?" — It uses a module registry and resolves the dependency graph at startup. Circular dependencies cause a runtime error unless you use `forwardRef()`.
- "What is the difference between middleware and interceptors?" — Middleware runs before the NestJS route matching and does not have access to the route handler. Interceptors are NestJS-aware, run after guards/pipes, and can modify both the request and the response.
- "How do you handle exceptions globally?" — `HttpExceptionFilter` implementing `ExceptionFilter`, registered globally via `app.useGlobalFilters()`. Unhandled exceptions return a 500; caught `HttpException` subclasses return the appropriate status code.
- "How would you test a NestJS service?" — Use `Test.createTestingModule()` to bootstrap a test module with mocked providers. Replace the real database service with a mock using `useValue` or `jest.fn()`.

## Production Checklist

Global `ValidationPipe` with `whitelist: true`. Global exception filter logging errors with correlation IDs. `helmet()` middleware for security headers. Rate limiting via `@nestjs/throttler`. Health checks via `@nestjs/terminus`. Structured logging with Pino or Winston. These topics come up in system design rounds at companies running NestJS in production.
