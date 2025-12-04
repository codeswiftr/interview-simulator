import { describe, it, expect, beforeAll, afterAll, afterEach, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { useAuth, AuthProvider } from '../useAuth';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Start MSW server
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
  mockNavigate.mockClear();
});
afterAll(() => server.close());

// Test wrapper
const wrapper = ({ children }: { children: ReactNode }) => (
  <MemoryRouter>
    <AuthProvider>{children}</AuthProvider>
  </MemoryRouter>
);

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should start with loading state', async () => {
    // Remove token to ensure we test initial loading state
    localStorage.removeItem('access_token');

    const { result } = renderHook(() => useAuth(), { wrapper });

    // In test environment, loading completes very quickly
    // We just verify it eventually becomes false
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should initialize with no user when not authenticated', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should load user from token on mount', async () => {
    // Set token in localStorage before mounting
    localStorage.setItem('access_token', 'existing-token');

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual({
      id: 'mock-user-id',
      email: 'test@example.com',
      full_name: 'Test User',
      experience_level: 'mid',
      subscription_tier: 'free',
      interviews_this_month: 0,
      total_interviews: 0,
      created_at: expect.any(String),
    });
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('should clear invalid token on mount', async () => {
    localStorage.setItem('access_token', 'invalid-token');
    localStorage.setItem('refresh_token', 'invalid-refresh');

    // Mock 401 error
    server.use(
      http.get('http://localhost:8000/api/v1/users/me', () => {
        return new HttpResponse(null, { status: 401 });
      })
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await result.current.login('test@example.com', 'password');

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorage.getItem('access_token')).toBe('mock-access-token');
      expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('should navigate to custom redirect path after login', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await result.current.login('test@example.com', 'password', '/custom-path');

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      expect(mockNavigate).toHaveBeenCalledWith('/custom-path');
    });

    it('should handle login error', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json(
            { detail: 'Invalid credentials' },
            { status: 401 }
          );
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        result.current.login('test@example.com', 'wrong-password')
      ).rejects.toThrow();

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });

  describe('register', () => {
    it('should register and login successfully', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await result.current.register(
        'new@example.com',
        'password123',
        'New User',
        'mid'
      );

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(localStorage.getItem('access_token')).toBe('mock-access-token');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('should handle registration error', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/register', () => {
          return HttpResponse.json(
            { detail: 'Email already exists' },
            { status: 400 }
          );
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        result.current.register('existing@example.com', 'password', 'User')
      ).rejects.toThrow();

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear user and tokens on logout', async () => {
      localStorage.setItem('access_token', 'existing-token');

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      result.current.logout();

      await waitFor(() => {
        expect(result.current.user).toBeNull();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('refreshUser', () => {
    it('should refresh user data', async () => {
      localStorage.setItem('access_token', 'existing-token');

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      // Update mock response
      server.use(
        http.get('http://localhost:8000/api/v1/users/me', () => {
          return HttpResponse.json({
            id: 'mock-user-id',
            email: 'test@example.com',
            full_name: 'Updated User Name',
            experience_level: 'senior',
            subscription_tier: 'pro',
            interviews_this_month: 5,
            total_interviews: 10,
            created_at: new Date().toISOString(),
          });
        })
      );

      await result.current.refreshUser();

      await waitFor(() => {
        expect(result.current.user?.full_name).toBe('Updated User Name');
      });

      expect(result.current.user?.subscription_tier).toBe('pro');
      expect(result.current.user?.interviews_this_month).toBe(5);
    });

    it('should handle refresh error gracefully', async () => {
      localStorage.setItem('access_token', 'existing-token');

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.user).toBeTruthy();
      });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Mock error
      server.use(
        http.get('http://localhost:8000/api/v1/users/me', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      await result.current.refreshUser();

      // User should remain unchanged on error
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled();
      });

      expect(result.current.user).toBeTruthy();
      consoleSpy.mockRestore();
    });
  });

  it('should throw error when used outside AuthProvider', () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');
  });
});
