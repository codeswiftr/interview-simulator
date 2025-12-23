import { useState, useEffect, useCallback } from 'react';

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

declare global {
  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }
}

interface UsePWAInstallReturn {
  /** Whether the app can be installed (prompt is available) */
  canInstall: boolean;
  /** Whether the app is already installed as PWA */
  isInstalled: boolean;
  /** Whether the device is iOS (needs manual install instructions) */
  isIOS: boolean;
  /** Whether the device is Android */
  isAndroid: boolean;
  /** Trigger the install prompt (Android only) */
  promptInstall: () => Promise<boolean>;
}

/**
 * Hook to manage PWA installation across platforms.
 * - Android: Uses beforeinstallprompt API
 * - iOS: Detects platform for manual instructions
 */
export function usePWAInstall(): UsePWAInstallReturn {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  // Detect platform
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as unknown as { MSStream?: unknown }).MSStream;
  const isAndroid = /Android/.test(navigator.userAgent);

  // Check if already installed
  useEffect(() => {
    const checkInstalled = () => {
      // Check display-mode for installed PWA
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      // iOS Safari standalone mode
      const isIOSStandalone = (navigator as unknown as { standalone?: boolean }).standalone === true;
      setIsInstalled(isStandalone || isIOSStandalone);
    };

    checkInstalled();

    // Listen for display mode changes
    const mediaQuery = window.matchMedia('(display-mode: standalone)');
    const handler = () => checkInstalled();
    mediaQuery.addEventListener('change', handler);

    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Capture beforeinstallprompt event
  useEffect(() => {
    const handler = (e: BeforeInstallPromptEvent) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Check if already captured (in case event fired before hook mounted)
    if ((window as unknown as { deferredPrompt?: BeforeInstallPromptEvent }).deferredPrompt) {
      setDeferredPrompt((window as unknown as { deferredPrompt: BeforeInstallPromptEvent }).deferredPrompt);
    }

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  // Listen for successful install
  useEffect(() => {
    const handler = () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
    };

    window.addEventListener('appinstalled', handler);
    return () => window.removeEventListener('appinstalled', handler);
  }, []);

  const promptInstall = useCallback(async (): Promise<boolean> => {
    if (!deferredPrompt) return false;

    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        setDeferredPrompt(null);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, [deferredPrompt]);

  return {
    canInstall: !!deferredPrompt && !isInstalled,
    isInstalled,
    isIOS,
    isAndroid,
    promptInstall,
  };
}

export default usePWAInstall;
