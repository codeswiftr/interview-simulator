# Test Infrastructure

This directory contains the test infrastructure for the frontend application.

## Setup

The test infrastructure includes:

- **Vitest**: Test runner and assertion library
- **React Testing Library**: Component testing utilities
- **MSW (Mock Service Worker)**: API mocking for integration tests
- **jsdom**: Browser environment simulation

## Files

- `setup.ts` - Global test setup (runs before all tests)
- `utils.tsx` - Custom render function with all providers
- `mocks/handlers.ts` - MSW request handlers for API mocking
- `mocks/server.ts` - MSW server configuration

## Using MSW in Tests

To use MSW for API mocking in your tests, import and configure the server in your test file:

```typescript
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { server } from '@/test/mocks/server';
import YourComponent from '../YourComponent';

// Start MSW server for this test file
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('YourComponent', () => {
  it('should fetch and display data', async () => {
    render(<YourComponent />);

    await waitFor(() => {
      expect(screen.getByText('Expected Text')).toBeInTheDocument();
    });
  });
});
```

## Custom Test Utilities

The `utils.tsx` file exports a custom `render` function that wraps components with:

- React Router's `BrowserRouter`
- `AuthProvider` for authentication context

Use it instead of the default React Testing Library render:

```typescript
import { render, screen } from '@/test/utils';
```

## Running Tests

```bash
# Run tests in watch mode
npm test

# Run tests once
npm test -- --run

# Run tests with UI
npm test:ui

# Run tests with coverage
npm test:coverage
```

## Writing Tests

### Component Tests

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### Tests with User Interaction

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('should handle click', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);

    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Clicked')).toBeInTheDocument();
  });
});
```

### Tests with API Calls

```typescript
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { server } from '@/test/mocks/server';
import { http, HttpResponse } from 'msw';
import MyComponent from '../MyComponent';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MyComponent', () => {
  it('should fetch and display data', async () => {
    // Override default handler for this test
    server.use(
      http.get('/api/v1/data', () => {
        return HttpResponse.json({ message: 'Test data' });
      })
    );

    render(<MyComponent />);

    await waitFor(() => {
      expect(screen.getByText('Test data')).toBeInTheDocument();
    });
  });
});
```

## Best Practices

1. **Keep tests simple and focused** - Test one thing at a time
2. **Use semantic queries** - Prefer `getByRole` and `getByLabelText`
3. **Test user behavior** - Focus on what users do and see, not implementation details
4. **Mock external dependencies** - Use MSW for API calls, mock other external services
5. **Clean up after tests** - The setup file handles cleanup, but be aware of side effects
6. **Use `waitFor` for async operations** - Don't use arbitrary timeouts
7. **Test accessibility** - Ensure components are accessible with proper ARIA labels
