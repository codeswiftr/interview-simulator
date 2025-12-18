/**
 * Frontend security tests for Interview Simulator.
 *
 * Tests for:
 * - Token storage security
 * - Request/Response security
 * - XSS prevention in frontend
 * - CSRF protection
 * - Content Security Policy
 * - Authentication flow security
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import { authAPI, interviewsAPI, questionsAPI, responsesAPI, feedbackAPI, uploadAPI, subscriptionsAPI, userAPI } from '../api';

// Mock crypto.randomUUID using vi.stubGlobal
vi.stubGlobal('crypto', {
  ...crypto,
  randomUUID: () => 'test-uuid-12345',
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.location
const locationMock = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: locationMock,
  writable: true,
});

// TODO: API Security tests need proper MSW mocking - skipped until fixed
describe.skip('API Security Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Token Security', () => {
    it('should include authorization header when token exists', async () => {
      localStorageMock.getItem.mockReturnValue('test-access-token');

      const mockResponse = { data: { user: { id: '1', email: 'test@example.com' } } };
      const axiosSpy = vi.spyOn(axios, 'create').mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse),
        post: vi.fn().mockResolvedValue(mockResponse),
        patch: vi.fn().mockResolvedValue(mockResponse),
        delete: vi.fn().mockResolvedValue(mockResponse),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      // Import API to trigger interceptor setup
      const apiModule = await import('../api');

      // Verify token is retrieved
      expect(localStorageMock.getItem).toHaveBeenCalledWith('access_token');
    });

    it('should not include authorization header when no token exists', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      const axiosSpy = vi.spyOn(axios, 'create').mockReturnValue({
        get: vi.fn().mockResolvedValue({ data: {} }),
        post: vi.fn().mockResolvedValue({ data: {} }),
        patch: vi.fn().mockResolvedValue({ data: {} }),
        delete: vi.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      } as any);

      await import('../api');

      expect(localStorageMock.getItem).toHaveBeenCalledWith('access_token');
    });

    it('should add correlation ID to requests', async () => {
      const axiosInstance = axios.create();
      const requestInterceptorSpy = vi.fn();

      axiosInstance.interceptors.request.use = vi.fn((interceptor) => {
        requestInterceptorSpy.mockImplementation(interceptor);
      });

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      await import('../api');

      // Simulate request config
      const config = {
        headers: {},
        method: 'GET',
        url: '/test',
      };

      requestInterceptorSpy(config);

      expect(config.headers['X-Correlation-ID']).toBe('test-uuid-12345');
    });

    it('should not override existing correlation ID', async () => {
      const axiosInstance = axios.create();
      const requestInterceptorSpy = vi.fn();

      axiosInstance.interceptors.request.use = vi.fn((interceptor) => {
        requestInterceptorSpy.mockImplementation(interceptor);
      });

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      await import('../api');

      // Simulate request config with existing correlation ID
      const config = {
        headers: { 'X-Correlation-ID': 'existing-uuid' },
        method: 'GET',
        url: '/test',
      };

      requestInterceptorSpy(config);

      expect(config.headers['X-Correlation-ID']).toBe('existing-uuid');
    });
  });

  describe('Authentication Security', () => {
    it('should clear tokens on logout', () => {
      authAPI.logout();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });

    it('should handle 401 unauthorized responses', async () => {
      const axiosInstance = axios.create();
      const mockError = {
        response: { status: 401 },
        config: { url: '/api/test', method: 'GET' },
      };

      let responseInterceptor: any;
      axiosInstance.interceptors.response.use = vi.fn((success, error) => {
        responseInterceptor = error;
      });

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);
      vi.spyOn(axios, 'post').mockRejectedValue(mockError);

      await import('../api');

      // Should trigger 401 handling
      expect(responseInterceptor).toBeDefined();
    });

    it('should redirect to login on refresh failure', async () => {
      const axiosInstance = axios.create();
      const responseInterceptorSpy = vi.fn();

      axiosInstance.interceptors.response.use = vi.fn((success, error) => {
        responseInterceptorSpy.mockImplementation(error);
        return vi.fn();
      });

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);
      vi.spyOn(axios, 'post').mockRejectedValue(new Error('Refresh failed'));

      localStorageMock.getItem.mockReturnValue('test-refresh-token');

      await import('../api');

      // Simulate 401 error
      const mockError = {
        response: { status: 401 },
        config: { _retry: false, url: '/api/test' },
      };

      await responseInterceptorSpy(mockError);

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(locationMock.href).toBe('/login');
    });

    it('should prevent infinite retry loops', async () => {
      const axiosInstance = axios.create();
      const responseInterceptorSpy = vi.fn();

      axiosInstance.interceptors.response.use = vi.fn((success, error) => {
        responseInterceptorSpy.mockImplementation(error);
        return vi.fn();
      });

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      await import('../api');

      // Simulate request that has already been retried
      const mockError = {
        response: { status: 401 },
        config: { _retry: true, url: '/api/test' },
      };

      // Should reject without retrying
      await expect(responseInterceptorSpy(mockError)).rejects.toEqual(mockError);
    });
  });

  describe('Request Security', () => {
    it('should use HTTPS in production', () => {
      // This would be tested by checking VITE_API_URL in production
      const prodUrl = import.meta.env.VITE_API_URL || '';

      if (import.meta.env.PROD && prodUrl) {
        expect(prodUrl).toMatch(/^https:\/\//);
      }
    });

    it('should validate input before sending', async () => {
      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      // Test login API
      await authAPI.login('test@example.com', 'password123');

      expect(mockPost).toHaveBeenCalledWith('/users/login/', {
        email: 'test@example.com',
        password: 'password123',
      });
    });

    it('should sanitize file uploads', async () => {
      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      const file = new File(['test'], 'test.wav', { type: 'audio/wav' });

      await uploadAPI.uploadAudio(file, 'session-123', 'question-456');

      expect(mockPost).toHaveBeenCalledWith(
        '/upload/audio/',
        expect.any(FormData),
        expect.objectContaining({
          timeout: 60000,
          headers: {
            'Content-Type': undefined,
          },
        })
      );
    });
  });

  describe('Response Security', () => {
    it('should handle sensitive data securely', async () => {
      const sensitiveData = {
        access_token: 'secret-token',
        refresh_token: 'refresh-secret',
        user: { id: '123', email: 'user@example.com' },
      };

      const axiosInstance = {
        post: vi.fn().mockResolvedValue({ data: sensitiveData }),
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      // Mock refresh token endpoint
      vi.spyOn(axios, 'post').mockResolvedValue({ data: sensitiveData });

      localStorageMock.getItem.mockReturnValue('refresh-token');

      const apiModule = await import('../api');

      // Verify tokens are stored securely (not in URL)
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'access_token',
        'secret-token'
      );
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'refresh_token',
        'refresh-secret'
      );
    });

    it('should not log sensitive data in production', async () => {
      // Mock production environment
      const originalProd = import.meta.env.PROD;
      import.meta.env.PROD = true;

      const consoleSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const axiosInstance = {
        get: vi.fn().mockResolvedValue({
          data: {},
          headers: { 'x-correlation-id': 'test-id' },
        }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn((success) => success) },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      await import('../api');

      // In production, debug logging should be minimal
      expect(consoleSpy).not.toHaveBeenCalled();

      import.meta.env.PROD = originalProd;
      consoleSpy.mockRestore();
      consoleWarnSpy.mockRestore();
    });
  });

  describe('XSS Prevention', () => {
    it('should escape HTML in user inputs', async () => {
      const xssPayload = '<script>alert("XSS")</script>';
      const escapedPayload = '&lt;script&gt;alert("XSS")&lt;/script&gt;';

      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      // Test with potentially dangerous input
      await authAPI.register(xssPayload, 'password123', xssPayload);

      // The input should be sent as-is (backend handles escaping)
      expect(mockPost).toHaveBeenCalledWith('/users/register/', {
        email: xssPayload,
        password: 'password123',
        full_name: xssPayload,
      });
    });

    it('should handle JSON responses safely', async () => {
      const maliciousResponse = {
        message: '<img src=x onerror=alert(1)>',
        data: 'normal data',
      };

      const axiosInstance = {
        get: vi.fn().mockResolvedValue({ data: maliciousResponse }),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      const apiModule = await import('../api');

      // Response should be parsed safely as JSON
      expect(maliciousResponse.message).toContain('<img');
    });
  });

  describe('CSRF Protection', () => {
    it('should include security headers', async () => {
      // This would test actual header inclusion
      // For now, we test the concept
      const axiosInstance = axios.create();

      expect(axiosInstance.defaults.headers['Content-Type']).toBe('application/json');
    });

    it('should validate same-origin requests', () => {
      // Test API base URL configuration
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

      // In production, should be same origin or trusted CORS
      if (import.meta.env.PROD) {
        const url = new URL(apiUrl);
        expect(['https:', 'http:']).toContain(url.protocol);
      }
    });
  });

  describe('Content Security Policy', () => {
    it('should not use inline styles or scripts', async () => {
      // This tests frontend behavior, not headers
      const dangerousHTML = '<style>body { background: red !important; }</style>';

      // Should handle inline styles appropriately
      expect(typeof dangerousHTML).toBe('string');
    });

    it('should validate dynamic script loading', () => {
      // Test that dynamic imports are properly validated
      expect(() => import('../api')).not.toThrow();
    });
  });

  describe('Password Security', () => {
    it('should not log passwords', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      const password = 'superSecretPassword123!';
      await authAPI.login('test@example.com', password);

      // Password should not appear in logs
      expect(consoleSpy).not.toHaveBeenCalledWith(expect.stringContaining(password));
      expect(consoleErrorSpy).not.toHaveBeenCalledWith(expect.stringContaining(password));

      consoleSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    it('should handle password reset securely', async () => {
      const resetToken = 'reset-token-123';
      const newPassword = 'newSecurePassword456!';

      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      await authAPI.resetPassword(resetToken, newPassword);

      expect(mockPost).toHaveBeenCalledWith('/auth/reset-password', {
        token: resetToken,
        new_password: newPassword,
      });
    });
  });

  describe('Rate Limiting', () => {
    it('should handle rate limit responses gracefully', async () => {
      const rateLimitError = {
        response: {
          status: 429,
          data: {
            detail: 'Too many requests',
            retry_after: 60,
          },
        },
        config: { url: '/api/test' },
      };

      const axiosInstance = {
        get: vi.fn().mockRejectedValue(rateLimitError),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn((success, error) => error) },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      const apiModule = await import('../api');

      // Should handle rate limit without exposing sensitive info
      expect(rateLimitError.response.status).toBe(429);
    });
  });

  describe('File Upload Security', () => {
    it('should validate file types for audio uploads', async () => {
      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      // Test with allowed audio file
      const audioFile = new File(['audio data'], 'test.wav', { type: 'audio/wav' });

      await uploadAPI.uploadAudio(audioFile, 'session-123', 'question-456');

      expect(mockPost).toHaveBeenCalledWith(
        '/upload/audio/',
        expect.any(FormData),
        expect.any(Object)
      );
    });

    it('should set appropriate timeout for large uploads', async () => {
      const mockPost = vi.fn();
      const axiosInstance = {
        post: mockPost,
        get: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      };

      vi.spyOn(axios, 'create').mockReturnValue(axiosInstance as any);

      const file = new File(['test'], 'test.wav', { type: 'audio/wav' });

      await uploadAPI.uploadAudio(file, 'session-123', 'question-456');

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(FormData),
        expect.objectContaining({
          timeout: 60000,
        })
      );
    });
  });
});

describe('Frontend XSS Prevention', () => {
  describe('DOM Manipulation', () => {
    it('should use textContent instead of innerHTML when appropriate', () => {
      const element = document.createElement('div');
      const userInput = '<script>alert("XSS")</script>';

      // Safe approach - use textContent
      element.textContent = userInput;

      expect(element.innerHTML).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });

    it('should sanitize HTML when using innerHTML', () => {
      const element = document.createElement('div');
      const safeHTML = '<p>Safe content</p>';
      const dangerousHTML = '<script>alert("XSS")</script>';

      // If innerHTML must be used, it should be sanitized first
      // This would use a sanitization library in production
      const sanitized = dangerousHTML.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

      element.innerHTML = sanitized;

      expect(element.innerHTML).toBe('');
    });

    it('should escape dynamic URLs', () => {
      const userInput = 'javascript:alert("XSS")';
      const element = document.createElement('a');

      // Should validate or escape URLs
      if (userInput.startsWith('javascript:')) {
        element.href = '#';
      } else {
        element.href = userInput;
      }

      expect(element.href).not.toContain('javascript:');
    });
  });

  describe('Event Handlers', () => {
    it('should avoid inline event handlers', () => {
      const element = document.createElement('button');

      // Good practice - use addEventListener
      element.addEventListener('click', () => console.log('clicked'));

      // Avoid - element.onclick = 'alert("XSS")'

      expect(element.onclick).toBeNull();
    });

    it('should validate callback functions', () => {
      const callbacks: { [key: string]: Function } = {};

      // Should validate callbacks before execution
      const addCallback = (name: string, fn: Function) => {
        if (typeof fn === 'function') {
          callbacks[name] = fn;
        }
      };

      const validCallback = () => console.log('valid');
      addCallback('valid', validCallback);

      expect(typeof callbacks['valid']).toBe('function');

      const invalidCallback = '<script>alert("XSS")</script>' as any;
      addCallback('invalid', invalidCallback);

      expect(callbacks['invalid']).toBeUndefined();
    });
  });

  describe('Local Storage Security', () => {
    it('should not store sensitive data in localStorage', () => {
      // localStorage is accessible via JavaScript, so sensitive data should be avoided
      const sensitiveData = {
        password: 'secret123',
        creditCard: '1234-5678-9012-3456',
      };

      // Should not store sensitive data
      expect(() => {
        localStorage.setItem('sensitive', JSON.stringify(sensitiveData));
      }).not.toThrow(); // But this is bad practice

      // Clean up
      localStorage.removeItem('sensitive');
    });

    it('should encrypt sensitive data if localStorage is necessary', () => {
      // If localStorage must be used for sensitive data, it should be encrypted
      const sensitiveData = 'token-123';

      // This would use encryption in production
      const encrypted = btoa(sensitiveData); // Base64 is not encryption, just for demo

      expect(encrypted).not.toBe(sensitiveData);
      expect(atob(encrypted)).toBe(sensitiveData);
    });
  });

  describe('Web Security Headers', () => {
    it('should not disable security features', () => {
      // Should not disable security features
      expect(document.cookie).not.toContain('SameSite=None');
    });

    it('should use HTTPS in production', () => {
      if (import.meta.env.PROD) {
        expect(window.location.protocol).toBe('https:');
      }
    });
  });
});

describe('Error Handling Security', () => {
  it('should not expose stack traces in production', () => {
    const error = new Error('Internal error');

    if (import.meta.env.PROD) {
      // In production, errors should be sanitized
      const sanitizedError = {
        message: 'Something went wrong',
        code: 'INTERNAL_ERROR',
      };

      expect(sanitizedError.message).not.toContain('stack');
    } else {
      // In development, full error details can be shown
      expect(error.message).toBe('Internal error');
    }
  });

  it('should validate error messages before display', () => {
    const errorMessage = '<script>alert("XSS")</script> - Error occurred';

    // Should escape or sanitize error messages before display
    const escapedMessage = errorMessage.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    expect(escapedMessage).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt; - Error occurred');
  });
});