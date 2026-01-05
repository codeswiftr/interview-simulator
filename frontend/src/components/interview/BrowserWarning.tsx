import { useState, useEffect } from 'react';
import { AlertTriangle, X, Chrome, Globe } from 'lucide-react';

interface BrowserCompatibility {
  isSupported: boolean;
  hasMediaRecorder: boolean;
  hasGetUserMedia: boolean;
  hasCrypto: boolean;
  browser: string;
  recommendation: string | null;
}

/**
 * Check browser compatibility for audio recording features.
 */
function checkBrowserCompatibility(): BrowserCompatibility {
  const ua = navigator.userAgent;

  // Detect browser
  let browser = 'Unknown';
  if (ua.includes('Chrome') && !ua.includes('Edg')) {
    browser = 'Chrome';
  } else if (ua.includes('Firefox')) {
    browser = 'Firefox';
  } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
    browser = 'Safari';
  } else if (ua.includes('Edg')) {
    browser = 'Edge';
  } else if (ua.includes('Opera') || ua.includes('OPR')) {
    browser = 'Opera';
  }

  // Check for MediaRecorder API
  const hasMediaRecorder = typeof MediaRecorder !== 'undefined';

  // Check for getUserMedia
  const hasGetUserMedia = !!(
    navigator.mediaDevices && navigator.mediaDevices.getUserMedia
  );

  // Check for crypto API (for UUID generation)
  const hasCrypto = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function';

  // Determine overall support
  const isSupported = hasMediaRecorder && hasGetUserMedia;

  // Generate recommendation
  let recommendation: string | null = null;
  if (!isSupported) {
    if (browser === 'Safari' && !hasMediaRecorder) {
      recommendation = 'Safari requires iOS 14.3+ or macOS Big Sur 11.1+ for audio recording.';
    } else {
      recommendation = 'Please use Chrome, Firefox, Safari 14.3+, or Edge for the best experience.';
    }
  }

  return {
    isSupported,
    hasMediaRecorder,
    hasGetUserMedia,
    hasCrypto,
    browser,
    recommendation,
  };
}

interface BrowserWarningProps {
  /** Called when user dismisses the warning */
  onDismiss?: () => void;
  /** Override to always show warning (for testing) */
  forceShow?: boolean;
}

/**
 * Browser compatibility warning banner.
 * Shows a dismissible warning if the browser doesn't support audio recording.
 */
export function BrowserWarning({ onDismiss, forceShow = false }: BrowserWarningProps) {
  const [compatibility, setCompatibility] = useState<BrowserCompatibility | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const result = checkBrowserCompatibility();
    setCompatibility(result);

    // Check if user has previously dismissed this warning
    const storedDismissal = localStorage.getItem('browser_warning_dismissed');
    if (storedDismissal) {
      setDismissed(true);
    }
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('browser_warning_dismissed', 'true');
    onDismiss?.();
  };

  // Don't render if:
  // - Still checking compatibility
  // - Browser is supported (unless forceShow)
  // - User has dismissed the warning
  if (!compatibility) return null;
  if (compatibility.isSupported && !forceShow) return null;
  if (dismissed && !forceShow) return null;

  return (
    <div
      role="alert"
      aria-live="polite"
      className="relative bg-status-warning/10 border border-status-warning/30 rounded-lg p-4 mb-4"
    >
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 p-1 text-text-secondary hover:text-text-primary rounded transition-colors"
        aria-label="Dismiss browser warning"
      >
        <X size={16} />
      </button>

      <div className="flex items-start gap-3 pr-6">
        <AlertTriangle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
        <div className="space-y-2">
          <p className="text-sm font-medium text-text-primary">
            Limited Browser Support Detected
          </p>
          <p className="text-sm text-text-secondary">
            Your browser ({compatibility.browser}) may not fully support audio recording features.
            {compatibility.recommendation && (
              <span className="block mt-1">{compatibility.recommendation}</span>
            )}
          </p>

          <div className="flex flex-wrap gap-2 mt-3">
            <a
              href="https://www.google.com/chrome/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs bg-surface-secondary hover:bg-surface-tertiary px-3 py-1.5 rounded transition-colors"
            >
              <Chrome size={14} />
              Get Chrome
            </a>
            <a
              href="https://www.mozilla.org/firefox/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs bg-surface-secondary hover:bg-surface-tertiary px-3 py-1.5 rounded transition-colors"
            >
              <Globe size={14} />
              Get Firefox
            </a>
          </div>

          <button
            onClick={handleDismiss}
            className="text-xs text-text-tertiary hover:text-text-secondary underline mt-2"
          >
            Continue anyway
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to check browser compatibility.
 * Use this to conditionally show warnings or adjust features.
 */
export function useBrowserCompatibility(): BrowserCompatibility | null {
  const [compatibility, setCompatibility] = useState<BrowserCompatibility | null>(null);

  useEffect(() => {
    setCompatibility(checkBrowserCompatibility());
  }, []);

  return compatibility;
}

export { checkBrowserCompatibility };
export type { BrowserCompatibility };
