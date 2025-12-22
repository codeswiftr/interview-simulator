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
      <div className="mx-auto flex max-w-md items-center justify-between px-3 pt-1.5 pb-1.5 h-14">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex flex-1 flex-col items-center gap-0.5 py-1 text-[10px] sm:text-xs font-medium transition-colors',
                  'text-text-tertiary hover:text-text-secondary',
                  isActive && 'text-electric-blue'
                )
              }
            >
              <Icon className="h-[18px] w-[18px] sm:h-5 sm:w-5" aria-hidden="true" />
              <span className="leading-tight">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}

export default BottomNav;
