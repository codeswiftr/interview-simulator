import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { registerSW } from 'virtual:pwa-register';
import { AuthProvider } from './hooks/useAuth';
import { analytics } from './lib/analytics';
import { captureUTMFromLocation } from './lib/utm';
import { queryClient } from './lib/queryClient';
import { initSentry } from './lib/sentry';
import App from './App';
import './styles/globals.css';

// Initialize Sentry error tracking (must be first)
initSentry();

// Capture UTM params early so they're available on first auth events
captureUTMFromLocation();

// Initialize PostHog analytics
analytics.init();

// Load Rewardful affiliate tracking (only if API key is configured)
const rewardfulKey = import.meta.env.VITE_REWARDFUL_API_KEY;
if (rewardfulKey) {
  // Initialize Rewardful queue
  interface RewardfulWindow extends Window {
    _rwq: string;
    rewardful: ((...args: unknown[]) => void) & { q?: unknown[] };
  }
  const rw = window as unknown as RewardfulWindow;
  rw._rwq = 'rewardful';
  rw.rewardful = rw.rewardful || function(...args: unknown[]) {
    (rw.rewardful.q = rw.rewardful.q || []).push(args);
  };

  // Load Rewardful script
  const script = document.createElement('script');
  script.src = 'https://r.wdfl.co/rw.js';
  script.dataset.rewardful = rewardfulKey;
  script.async = true;
  document.head.appendChild(script);
}

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  registerSW({
    onNeedRefresh() {
      // Could show a prompt to user that new content is available
      console.log('[PWA] New content available, refresh for update');
    },
    onOfflineReady() {
      console.log('[PWA] App ready to work offline');
    },
    onRegistered(registration) {
      console.log('[PWA] Service worker registered:', registration);
    },
    onRegisterError(error) {
      console.error('[PWA] Service worker registration failed:', error);
    },
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
);
