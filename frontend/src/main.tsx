import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { analytics } from './lib/analytics';
import { captureUTMFromLocation } from './lib/utm';
import App from './App';
import './styles/globals.css';

// Capture UTM params early so they're available on first auth events
captureUTMFromLocation();

// Initialize PostHog analytics
analytics.init();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
