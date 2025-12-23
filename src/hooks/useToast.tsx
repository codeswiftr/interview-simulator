/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { ToastContainer, type ToastData, type ToastType } from '../components/ui/toast';

interface ToastContextValue {
  toasts: ToastData[];
  addToast: (type: ToastType, title: string, message?: string, duration?: number) => void;
  removeToast: (id: string) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

let toastId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (type: ToastType, title: string, message?: string, duration?: number) => {
      const id = `toast-${++toastId}`;
      setToasts((prev) => [...prev, { id, type, title, message, duration }]);
    },
    []
  );

  const success = useCallback(
    (title: string, message?: string) => addToast('success', title, message),
    [addToast]
  );

  const error = useCallback(
    (title: string, message?: string) => addToast('error', title, message, 8000),
    [addToast]
  );

  const warning = useCallback(
    (title: string, message?: string) => addToast('warning', title, message),
    [addToast]
  );

  const info = useCallback(
    (title: string, message?: string) => addToast('info', title, message),
    [addToast]
  );

  return (
    <ToastContext.Provider
      value={{ toasts, addToast, removeToast, success, error, warning, info }}
    >
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
