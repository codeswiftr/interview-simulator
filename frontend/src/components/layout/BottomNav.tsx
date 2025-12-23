import { Home, Mic, BarChart2, Settings } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { useAuth } from '../../hooks/useAuth';

const navItems = [
  { to: '/dashboard', icon: Home, label: 'Home' },
  { to: '/practice', icon: Mic, label: 'Practice' },
  { to: '/progress', icon: BarChart2, label: 'Progress' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

/**
 * BottomNav - Mobile navigation bar
 *
 * Displays a fixed bottom navigation for mobile devices (< md breakpoint).
 * Only shown when user is authenticated.
 * Hidden during active interview sessions to reduce cognitive distraction.
 * Uses NavLink for active state detection.
 */
export function BottomNav() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  // Hide during active interview (path like /interview/uuid but not /interview/uuid/feedback)
  const isActiveInterview = /^\/interview\/[^/]+$/.test(location.pathname);

  // Only show for authenticated users, and not during active interviews
  if (!isAuthenticated || isActiveInterview) {
    return null;
  }

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 glass border-t border-border-light md:hidden safe-area-bottom"
      aria-label="Mobile navigation"
    >
      <div className="mx-auto flex max-w-md items-center justify-around px-2 h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  // Min 44x44 touch target, centered content
                  'flex flex-col items-center justify-center min-w-[56px] min-h-[48px] px-2 py-1.5 rounded-lg',
                  'text-xs font-medium transition-all',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-electric-blue focus-visible:ring-offset-1',
                  isActive
                    ? 'text-electric-blue bg-electric-blue/10'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-secondary active:scale-95'
                )
              }
            >
              <Icon className="h-5 w-5 mb-0.5" aria-hidden="true" />
              <span className="leading-tight">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}

export default BottomNav;
