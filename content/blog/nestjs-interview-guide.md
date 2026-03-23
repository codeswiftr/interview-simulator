---
title: "NestJS Interview Guide: Decorators, Dependency Injection, and Production Patterns"
description: "Prepare for NestJS interviews — modules, providers, guards, interceptors, pipes, microservices, and the architectural patterns that make NestJS production-ready."
date: "2026-03-20"
category: "Programming Languages"
---

# NestJS Interview Guide: Decorators, Dependency Injection, and Production Patterns

NestJS has become the dominant Node.js framework for structured backend development at enterprise companies and scale-ups. If you're applying to a TypeScript backend role and they use Node.js, there's a good chance they're on NestJS. Interviews test whether you understand the framework's architecture, not just whether you can use it.

## Why NestJS?

NestJS brings Angular's architectural patterns to Node.js: modules, dependency injection, decorators, and strong typing with TypeScript. It solves the "Express is too flexible" problem — teams end up with inconsistent project structures. NestJS imposes structure, making large codebases maintainable by multiple teams.

The tradeoff: more boilerplate, higher learning curve. An interviewer asking "why NestJS over Express?" wants to hear: structured application architecture at scale, built-in DI container, opinionated module system, testability by design, and rich ecosystem (TypeORM integration, GraphQL, microservices built-in).

## Modules: The Building Blocks

Every NestJS application is composed of modules. A module is a class decorated with `@Module()` that groups related providers, controllers, and imports.

```typescript
@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],  // make available to other modules
})
export class UsersModule {}
```

Key interview point: modules are singletons by default. The `exports` array controls what other modules can inject. This encapsulation is central to NestJS architecture — you should understand which services are public vs. private to a module.

Dynamic modules allow configuration at import time: `TypeOrmModule.forRoot(config)` vs. `TypeOrmModule.forFeature([Entity])`. Know this pattern for configurable modules.

## Dependency Injection

NestJS's DI container manages the lifecycle of providers. The `@Injectable()` decorator marks a class as a provider. Providers are registered in a module's `providers` array and injected via constructor injection.

```typescript
@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private readonly userRepo: Repository<User>,
    private readonly emailService: EmailService,
  ) {}
}
```

Interview question: "What are provider scopes in NestJS?" Answer: Default (singleton — shared across the entire application), Request (new instance per HTTP request, useful for request-scoped context), and Transient (new instance each time it's injected). Most services should be DEFAULT. Request scope is useful for request ID propagation or per-request caching.

Custom providers: useful for testing and configuration. `useValue` for providing a static value, `useFactory` for async initialization, `useClass` for swapping implementations.

## Controllers and Routing

```typescript
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get(':id')
  findOne(@Param('id') id: string): Promise<User> {
    return this.usersService.findOne(+id);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  create(@Body() dto: CreateUserDto): Promise<User> {
    return this.usersService.create(dto);
  }
}
```

## Request Pipeline: Guards, Interceptors, Pipes, Filters

This is the most tested NestJS topic. The request pipeline processes in order:

1. **Guards** — authentication/authorization. `canActivate()` returns boolean or throws.
2. **Interceptors (before)** — logging, request transformation
3. **Pipes** — validation and transformation of incoming data
4. **Handler** — your controller method
5. **Interceptors (after)** — response transformation
6. **Exception Filters** — catch and format errors

**Guards:** Implement `CanActivate`. The JWT guard is the classic example: extract token from header, verify, attach user to request.

**Pipes:** Implement `PipeTransform`. `ValidationPipe` with class-validator DTOs is standard. Mark with `@UsePipes(new ValidationPipe({ whitelist: true }))` to strip unknown properties and validate automatically.

**Interceptors:** Implement `NestInterceptor`. Use for: logging (log request/response), caching, response transformation (wrap all responses in `{ data: ... }` envelope), timeout.

**Exception Filters:** Implement `ExceptionFilter`. Transform exceptions into HTTP responses. The built-in `HttpException` and its subclasses (`NotFoundException`, `UnauthorizedException`) cover most cases. Custom filters for domain-specific error formatting.

## DTOs and Validation

DTOs (Data Transfer Objects) define the shape of incoming requests. Combined with class-validator and class-transformer:

```typescript
export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;

  @IsOptional()
  @IsString()
  name?: string;
}
```

Enable `ValidationPipe` globally in `main.ts` with `useGlobalPipes`. Set `whitelist: true` to strip unknown properties, `transform: true` to auto-transform payloads to DTO instances.

## Testing

NestJS is designed for testability. `@nestjs/testing` provides `Test.createTestingModule()` which creates an isolated DI container for tests.

```typescript
const module = await Test.createTestingModule({
  providers: [
    UsersService,
    { provide: getRepositoryToken(User), useValue: mockRepo },
  ],
}).compile();

service = module.get<UsersService>(UsersService);
```

This is cleaner than mocking imports directly — the DI container handles dependency injection, and you provide mock implementations via `useValue` or `useClass`.

## Microservices

NestJS has built-in microservice support via `@nestjs/microservices`. Supports transports: TCP, Redis, NATS, Kafka, RabbitMQ, gRPC. The same decorator-based programming model applies: `@MessagePattern()` for request-response, `@EventPattern()` for fire-and-forget.

Interview: "How would you split a NestJS monolith into microservices?" Answer: NestJS's module system aligns well with service boundaries — each major module (UsersModule, OrdersModule) becomes a service. ClientProxy for inter-service communication, DTOs become shared contracts, consider gRPC for type-safe binary transport.

## Production Patterns

Config management: `@nestjs/config` with Joi validation schemas. Health checks: `@nestjs/terminus` with database and external service indicators. Rate limiting: `@nestjs/throttler`. OpenAPI documentation: `@nestjs/swagger` with decorators on DTOs and controllers.

Knowing these production-ready patterns distinguishes candidates who've shipped NestJS to production from those who've only read the docs.
