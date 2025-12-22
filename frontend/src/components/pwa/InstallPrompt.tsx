import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { X, Download } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

/**
 * PWA Install Prompt component.
 * Shows a banner prompting users to install the app on supported browsers.
 * Automatically hides on iOS (uses Add to Home Screen instead).
 * Context-aware: Only shows on non-interview pages to avoid interrupting user flow.
 */
export function InstallPrompt() {
  const location = useLocation();
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Don't show during active interview sessions
  const isInterviewPage = location.pathname.includes('/interview/') && !location.pathname.includes('/feedback');

  useEffect(() => {
    // Don't show during interviews
    if (isInterviewPage) {
      setShowPrompt(false);
      return;
    }

    // Check if already dismissed this session
    const wasDismissed = sessionStorage.getItem('pwa-install-dismissed');
    if (wasDismissed) {
      setDismissed(true);
      return;
    }

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return;
    }

    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      // Delay showing prompt - longer delay to avoid interrupting user flow
      // Only show after user has been on a non-interview page for 10 seconds
      setTimeout(() => {
        if (!isInterviewPage) {
          setShowPrompt(true);
        }
      }, 10000);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, [isInterviewPage]);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('[PWA] User accepted install prompt');
    }

    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    setDismissed(true);
    sessionStorage.setItem('pwa-install-dismissed', 'true');
  };

  // Don't show during interviews or if dismissed
  if (isInterviewPage || !showPrompt || dismissed || !deferredPrompt) {
    return null;
  }

  return (
    <div
      role="dialog"
      aria-labelledby="install-prompt-title"
      className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-80 z-50 animate-slide-up"
    >
      <div className="bg-surface-dark dark:bg-dark-surface-secondary rounded-xl shadow-2xl border border-white/10 overflow-hidden">
        <div className="p-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 bg-electric-blue/20 rounded-lg flex items-center justify-center">
              <Download className="w-5 h-5 text-electric-blue" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 id="install-prompt-title" className="text-sm font-semibold text-white">
                Install Interview Prep
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                Add to your home screen for quick access and offline use.
              </p>
            </div>
            <button
              onClick={handleDismiss}
              className="flex-shrink-0 p-1 text-gray-500 hover:text-gray-300 transition-colors"
              aria-label="Dismiss install prompt"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleDismiss}
              className="flex-1 px-3 py-2 text-xs font-medium text-gray-400 hover:text-white transition-colors"
            >
              Not now
            </button>
            <button
              onClick={handleInstall}
              className="flex-1 px-3 py-2 text-xs font-medium bg-electric-blue text-white rounded-lg hover:bg-electric-blue/90 transition-colors active:scale-[0.98]"
            >
              Install
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
