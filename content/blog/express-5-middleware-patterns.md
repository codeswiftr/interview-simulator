---
title: "Express 5 Middleware Patterns"
description: "Express 5 middleware patterns for production—async error handling, route-level middleware, custom middleware composition, security middleware stack, and the architectural patterns that make Express 5 services maintainable."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Express 5 Middleware Patterns

Express 5 (released 2024) is the first major Express version in a decade. The headline change: async middleware now works correctly—errors thrown from async functions are automatically forwarded to error handlers. For the vast majority of Express applications, this eliminates the most common source of production bugs.

## What Changed in Express 5

**Async error handling** is the most important change:

```javascript
// Express 4: async errors crash the process or hang the request
app.get('/users/:id', async (req, res, next) => {
  const user = await getUser(req.params.id);  // If this throws, bad things happen
  res.json(user);
});

// Express 5: thrown errors are automatically passed to next()
app.get('/users/:id', async (req, res, next) => {
  const user = await getUser(req.params.id);  // If this throws, goes to error handler
  res.json(user);
});
```

Other Express 5 changes: `req.query` is parsed with `qs` by default, `res.redirect()` no longer accepts status code as second argument (use `.status()` first), path matching is more strict.

## Application Structure

Production Express 5 applications use the router pattern for organization:

```javascript
// src/app.js
import express from 'express';
import { setupMiddleware } from './middleware/index.js';
import { usersRouter } from './routes/users.js';
import { authRouter } from './routes/auth.js';
import { errorHandler } from './middleware/error-handler.js';

export function createApp() {
  const app = express();
  setupMiddleware(app);

  app.use('/api/v1/auth', authRouter);
  app.use('/api/v1/users', usersRouter);

  // 404 handler
  app.use((req, res) => {
    res.status(404).json({ error: 'Not Found', path: req.path });
  });

  // Error handler — must be last and have (err, req, res, next) signature
  app.use(errorHandler);

  return app;
}
```

## Middleware Stack Setup

```javascript
// src/middleware/index.js
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { requestId } from './request-id.js';
import { requestLogger } from './request-logger.js';

export function setupMiddleware(app) {
  // Security headers
  app.use(helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
      },
    },
  }));

  // CORS
  app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') ?? [],
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true,
  }));

  // Rate limiting
  const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,  // 15 minutes
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests, please try again later' },
  });
  app.use('/api/', apiLimiter);

  // Request parsing
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true, limit: '1mb' }));

  // Custom middleware
  app.use(requestId);
  app.use(requestLogger);
}
```

## Custom Middleware Patterns

```javascript
// src/middleware/request-id.js
import { randomUUID } from 'node:crypto';

export function requestId(req, res, next) {
  req.id = req.headers['x-request-id'] ?? randomUUID();
  res.setHeader('X-Request-ID', req.id);
  next();
}

// src/middleware/request-logger.js
import logger from '../lib/logger.js';

export function requestLogger(req, res, next) {
  const start = Date.now();

  res.on('finish', () => {
    logger.info('request', {
      requestId: req.id,
      method: req.method,
      path: req.path,
      status: res.statusCode,
      durationMs: Date.now() - start,
      userAgent: req.headers['user-agent'],
    });
  });

  next();
}

// src/middleware/authenticate.js — route-level auth middleware
import jwt from 'jsonwebtoken';

export async function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid authorization header' });
  }

  const token = authHeader.slice(7);
  const payload = jwt.verify(token, process.env.JWT_SECRET);  // Throws in Express 5 → goes to error handler
  req.user = { id: payload.sub, roles: payload.roles };
  next();
}
```

## Error Handling

Express 5 error handlers receive errors from both sync and async routes:

```javascript
// src/middleware/error-handler.js
import logger from '../lib/logger.js';

export class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
  }
}

export function errorHandler(err, req, res, next) {
  // Known application errors
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: err.message,
      code: err.code,
    });
  }

  // JWT errors from jsonwebtoken
  if (err.name === 'JsonWebTokenError' || err.name === 'TokenExpiredError') {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  // Validation errors from libraries like zod
  if (err.name === 'ZodError') {
    return res.status(422).json({
      error: 'Validation failed',
      issues: err.errors,
    });
  }

  // Unknown errors — log full details, return generic message
  logger.error('Unhandled error', {
    requestId: req.id,
    error: err.message,
    stack: err.stack,
  });

  res.status(500).json({ error: 'Internal server error' });
}
```

## Router Patterns with Validation

```javascript
// src/routes/users.js
import { Router } from 'express';
import { z } from 'zod';
import { authenticate } from '../middleware/authenticate.js';
import { validate } from '../middleware/validate.js';
import { UsersController } from '../controllers/users.controller.js';

const createUserSchema = z.object({
  body: z.object({
    username: z.string().min(3).max(50),
    email: z.string().email(),
    password: z.string().min(8),
  }),
});

export const usersRouter = Router();
const controller = new UsersController();

usersRouter.get('/', authenticate, controller.list);
usersRouter.get('/:id', authenticate, controller.get);
usersRouter.post('/', validate(createUserSchema), controller.create);
usersRouter.put('/:id', authenticate, validate(updateUserSchema), controller.update);
usersRouter.delete('/:id', authenticate, controller.delete);

// src/middleware/validate.js
export function validate(schema) {
  return async (req, res, next) => {
    await schema.parseAsync({
      body: req.body,
      query: req.query,
      params: req.params,
    });
    next();
  };
}
```

## Testing Express 5 Applications

```javascript
import request from 'supertest';
import { createApp } from '../src/app.js';

describe('Users API', () => {
  const app = createApp();

  describe('POST /api/v1/users', () => {
    it('creates a user with valid data', async () => {
      const response = await request(app)
        .post('/api/v1/users')
        .send({ username: 'testuser', email: 'test@example.com', password: 'Test1234' });

      expect(response.status).toBe(201);
      expect(response.body.username).toBe('testuser');
    });

    it('returns 422 for invalid data', async () => {
      const response = await request(app)
        .post('/api/v1/users')
        .send({ email: 'not-an-email' });

      expect(response.status).toBe(422);
    });
  });
});
```

## Interview Tips

Express 5 interview questions:

1. **Async error handling** — the core Express 5 improvement; why Express 4 required `try/catch` + `next(err)` everywhere
2. **Middleware ordering** — why error handlers must come last with 4-argument signature
3. **Security middleware stack** — helmet, cors, rate limiting, why and when to apply each
4. **Router vs app** — organizing routes into routers for testability and separation
5. **When to use Express vs alternatives** — Fastify for performance, Hapi for enterprise conventions, tRPC for type safety

The core Express insight: Express is intentionally minimal. Every production feature (validation, logging, auth, rate limiting) comes from middleware composition. The skill is knowing which middleware to compose and in what order—Express itself just provides the mounting and dispatch mechanism.
