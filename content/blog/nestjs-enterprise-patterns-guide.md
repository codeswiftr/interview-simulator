---
title: "NestJS Enterprise Patterns Guide"
description: "Enterprise NestJS patterns for production applications—dependency injection, modules, guards, interceptors, pipes, microservices with message brokers, and the architectural patterns used in large-scale NestJS services."
date: "2026-03-21"
category: "Language Deep Dives"
---

# NestJS Enterprise Patterns Guide

NestJS brings Angular's architectural patterns to the Node.js backend—decorators, dependency injection, and opinionated module organization. For enterprise teams coming from Java Spring or Angular backgrounds, NestJS provides familiar structure. This guide covers the patterns that distinguish production NestJS applications.

## Module Architecture

NestJS organizes code into feature modules. A well-structured enterprise application uses domain modules:

```typescript
// users/users.module.ts
@Module({
  imports: [
    TypeOrmModule.forFeature([User, UserProfile]),
    AuthModule,
    CacheModule,
  ],
  controllers: [UsersController],
  providers: [
    UsersService,
    UsersRepository,
    { provide: 'USER_CACHE', useClass: UserCacheService },
  ],
  exports: [UsersService],  // Export for other modules to import
})
export class UsersModule {}

// app.module.ts
@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRootAsync({
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        url: config.get('DATABASE_URL'),
        entities: [__dirname + '/**/*.entity{.ts,.js}'],
        synchronize: false,
      }),
      inject: [ConfigService],
    }),
    UsersModule,
    OrdersModule,
    AuthModule,
  ],
})
export class AppModule {}
```

## Guards for Authorization

Guards implement `CanActivate` and run before route handlers:

```typescript
// auth/guards/roles.guard.ts
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ROLES_KEY } from '../decorators/roles.decorator';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!requiredRoles) return true;

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some(role => user.roles.includes(role));
  }
}

// Custom decorator
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

// Usage in controller
@Get('/admin/users')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin', 'superadmin')
async getAdminUsers() {
  return this.usersService.findAll();
}
```

## Interceptors for Cross-Cutting Concerns

Interceptors wrap request/response flow—ideal for logging, caching, and response transformation:

```typescript
// interceptors/logging.interceptor.ts
@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url } = request;
    const start = Date.now();

    return next.handle().pipe(
      tap({
        next: () => {
          const duration = Date.now() - start;
          this.logger.log(`${method} ${url} ${duration}ms`);
        },
        error: (err) => {
          const duration = Date.now() - start;
          this.logger.error(`${method} ${url} FAILED ${duration}ms`, err.stack);
        },
      }),
    );
  }
}

// interceptors/cache.interceptor.ts
@Injectable()
export class HttpCacheInterceptor extends CacheInterceptor {
  trackBy(context: ExecutionContext): string | undefined {
    const request = context.switchToHttp().getRequest();
    // Include user ID in cache key for personalized data
    const userId = request.user?.id;
    const path = request.url;
    return userId ? `user:${userId}:${path}` : path;
  }
}
```

## Pipes for Validation and Transformation

Pipes transform or validate input before it reaches handlers:

```typescript
// Built-in ValidationPipe with class-validator
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,          // Strip unknown properties
  forbidNonWhitelisted: true, // Throw on unknown properties
  transform: true,          // Auto-transform to DTO types
  transformOptions: {
    enableImplicitConversion: true,  // Convert query params to numbers
  },
}));

// DTO with class-validator decorators
export class CreateUserDto {
  @IsString()
  @MinLength(3)
  @MaxLength(50)
  username: string;

  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  @Matches(/(?=.*[A-Z])(?=.*[0-9])/, {
    message: 'Password must contain uppercase and number',
  })
  password: string;

  @IsOptional()
  @IsEnum(UserRole)
  role?: UserRole = UserRole.USER;
}

// Custom parse pipe
@Injectable()
export class ParseObjectIdPipe implements PipeTransform {
  transform(value: string): string {
    if (!isValidObjectId(value)) {
      throw new BadRequestException(`Invalid ID format: ${value}`);
    }
    return value;
  }
}
```

## Exception Filters

Global exception filters standardize error responses:

```typescript
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse();
      message = typeof exceptionResponse === 'string'
        ? exceptionResponse
        : (exceptionResponse as any).message;
    } else if (exception instanceof QueryFailedError) {
      status = HttpStatus.CONFLICT;
      message = 'Database constraint violation';
      this.logger.warn('DB error:', (exception as any).detail);
    } else {
      this.logger.error('Unhandled exception:', exception);
    }

    response.status(status).json({
      statusCode: status,
      message,
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}
```

## Microservices with Message Brokers

NestJS has first-class microservices support with multiple transports:

```typescript
// Order service — publishes events
@Injectable()
export class OrdersService {
  constructor(
    @Inject('NOTIFICATION_SERVICE') private readonly notificationClient: ClientProxy,
    @Inject('INVENTORY_SERVICE') private readonly inventoryClient: ClientProxy,
  ) {}

  async createOrder(dto: CreateOrderDto): Promise<Order> {
    const order = await this.ordersRepository.create(dto);

    // Emit event — fire-and-forget
    this.notificationClient.emit('order.created', {
      orderId: order.id,
      userId: order.userId,
      total: order.total,
    });

    // Request-response for inventory check
    const reserved = await firstValueFrom(
      this.inventoryClient.send('inventory.reserve', order.items)
    );

    if (!reserved.success) {
      await this.ordersRepository.cancel(order.id);
      throw new ConflictException('Insufficient inventory');
    }

    return order;
  }
}

// Notification service — consumes events
@Controller()
export class NotificationsController {
  @EventPattern('order.created')
  async handleOrderCreated(@Payload() data: OrderCreatedEvent) {
    await this.notificationsService.sendOrderConfirmation(data);
  }

  @MessagePattern('notification.send')
  async sendNotification(@Payload() payload: SendNotificationDto) {
    return this.notificationsService.send(payload);
  }
}
```

## Custom Decorators

Composing decorators reduces boilerplate:

```typescript
// Current user decorator
export const CurrentUser = createParamDecorator(
  (data: keyof User | undefined, ctx: ExecutionContext): User | any => {
    const request = ctx.switchToHttp().getRequest();
    const user = request.user;
    return data ? user?.[data] : user;
  },
);

// Composing multiple decorators
export function ApiAuthRoute(summary: string) {
  return applyDecorators(
    UseGuards(JwtAuthGuard),
    ApiBearerAuth(),
    ApiUnauthorizedResponse({ description: 'Unauthorized' }),
    ApiOperation({ summary }),
  );
}

// Usage
@Get('/profile')
@ApiAuthRoute('Get current user profile')
async getProfile(@CurrentUser() user: User) {
  return this.usersService.findById(user.id);
}
```

## Interview Tips

NestJS enterprise interview questions:

1. **DI container lifecycle** — singleton (default), request-scoped, transient providers and when to use each
2. **Guards vs Middleware vs Interceptors** — execution order, what each can access (Guards can inject services, middleware cannot easily)
3. **Module encapsulation** — why `exports` matters, why global modules should be rare
4. **Circular dependencies** — `forwardRef()` as a workaround, better to restructure to avoid
5. **Microservice patterns** — event patterns vs message patterns, at-least-once delivery considerations

The key NestJS insight: the opinionated structure is a feature, not a constraint. Teams spend less time arguing about architecture and more time building features. The tradeoff is that NestJS adds complexity for simple services that don't need enterprise patterns—for a simple CRUD API, plain Express or Fastify is often better.
