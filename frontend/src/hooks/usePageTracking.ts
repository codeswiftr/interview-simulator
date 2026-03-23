import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { analytics } from '../lib/analytics';

/**
 * Hook to track page views on route changes.
 * Add this hook to the App component to enable automatic page tracking.
 */
export function usePageTracking(): void {
  const location = useLocation();

  useEffect(() => {
    // Track page view with path and title
    analytics.pageView(location.pathname);
  }, [location.pathname]);
}
