import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast, ToastProvider } from '../useToast';
import type { ReactNode } from 'react';

// Test wrapper
const wrapper = ({ children }: { children: ReactNode }) => (
  <ToastProvider>{children}</ToastProvider>
);

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should start with empty toasts', () => {
    const { result } = renderHook(() => useToast(), { wrapper });
    expect(result.current.toasts).toEqual([]);
  });

  describe('addToast', () => {
    it('should add a toast with custom properties', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('info', 'Test Title', 'Test Message', 5000);
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0]).toMatchObject({
        type: 'info',
        title: 'Test Title',
        message: 'Test Message',
        duration: 5000,
      });
      expect(result.current.toasts[0].id).toBeDefined();
    });

    it('should add multiple toasts', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('success', 'First Toast');
        result.current.addToast('error', 'Second Toast');
        result.current.addToast('warning', 'Third Toast');
      });

      expect(result.current.toasts).toHaveLength(3);
      expect(result.current.toasts[0].title).toBe('First Toast');
      expect(result.current.toasts[1].title).toBe('Second Toast');
      expect(result.current.toasts[2].title).toBe('Third Toast');
    });

    it('should generate unique IDs for each toast', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('info', 'Toast 1');
        result.current.addToast('info', 'Toast 2');
      });

      expect(result.current.toasts).toHaveLength(2);
      expect(result.current.toasts[0].id).not.toBe(result.current.toasts[1].id);
    });
  });

  describe('removeToast', () => {
    it('should remove a specific toast by ID', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('info', 'Toast 1');
        result.current.addToast('info', 'Toast 2');
        result.current.addToast('info', 'Toast 3');
      });

      expect(result.current.toasts).toHaveLength(3);

      const toastId = result.current.toasts[1].id;

      act(() => {
        result.current.removeToast(toastId);
      });

      expect(result.current.toasts).toHaveLength(2);
      expect(result.current.toasts.find(t => t.id === toastId)).toBeUndefined();
    });

    it('should not affect other toasts when removing one', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('info', 'Toast 1');
        result.current.addToast('info', 'Toast 2');
        result.current.addToast('info', 'Toast 3');
      });

      const toastToRemove = result.current.toasts[1].id;
      const remainingToastIds = [result.current.toasts[0].id, result.current.toasts[2].id];

      act(() => {
        result.current.removeToast(toastToRemove);
      });

      expect(result.current.toasts).toHaveLength(2);
      expect(result.current.toasts[0].id).toBe(remainingToastIds[0]);
      expect(result.current.toasts[1].id).toBe(remainingToastIds[1]);
    });
  });

  describe('convenience methods', () => {
    it('should create success toast', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Success Title', 'Success Message');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('success');
      expect(result.current.toasts[0].title).toBe('Success Title');
      expect(result.current.toasts[0].message).toBe('Success Message');
    });

    it('should create error toast with extended duration', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.error('Error Title', 'Error Message');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('error');
      expect(result.current.toasts[0].title).toBe('Error Title');
      expect(result.current.toasts[0].duration).toBe(12000); // Error toasts have longer duration
    });

    it('should create warning toast', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.warning('Warning Title', 'Warning Message');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('warning');
      expect(result.current.toasts[0].title).toBe('Warning Title');
    });

    it('should create info toast', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.info('Info Title', 'Info Message');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('info');
      expect(result.current.toasts[0].title).toBe('Info Title');
    });

    it('should create toasts without message', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Title Only');
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Title Only');
      expect(result.current.toasts[0].message).toBeUndefined();
    });
  });

  describe('multiple toasts management', () => {
    it('should handle multiple toast types simultaneously', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Success');
        result.current.error('Error');
        result.current.warning('Warning');
        result.current.info('Info');
      });

      expect(result.current.toasts).toHaveLength(4);
      expect(result.current.toasts.map(t => t.type)).toEqual([
        'success',
        'error',
        'warning',
        'info',
      ]);
    });

    it('should maintain toast order', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('info', 'First');
        result.current.addToast('info', 'Second');
        result.current.addToast('info', 'Third');
      });

      expect(result.current.toasts[0].title).toBe('First');
      expect(result.current.toasts[1].title).toBe('Second');
      expect(result.current.toasts[2].title).toBe('Third');
    });

    it('should remove toasts independently', () => {
      const { result } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.addToast('info', 'First');
        result.current.addToast('info', 'Second');
        result.current.addToast('info', 'Third');
      });

      const firstId = result.current.toasts[0].id;
      const secondId = result.current.toasts[1].id;
      const thirdId = result.current.toasts[2].id;

      // Remove middle toast
      act(() => {
        result.current.removeToast(secondId);
      });

      expect(result.current.toasts).toHaveLength(2);
      expect(result.current.toasts[0].id).toBe(firstId);
      expect(result.current.toasts[1].id).toBe(thirdId);
    });
  });

  it('should throw error when used outside ToastProvider', () => {
    expect(() => {
      renderHook(() => useToast());
    }).toThrow('useToast must be used within a ToastProvider');
  });

  describe('toast persistence', () => {
    it('should persist toasts across renders', () => {
      const { result, rerender } = renderHook(() => useToast(), { wrapper });

      act(() => {
        result.current.success('Persistent Toast');
      });

      expect(result.current.toasts).toHaveLength(1);

      rerender();

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Persistent Toast');
    });
  });
});
