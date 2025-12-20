import { Home, Mic, BarChart2, Settings } from 'lucide-react';
import { NavLink } from 'react-router-dom';
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
 * Uses NavLink for active state detection.
 */
export function BottomNav() {
  const { isAuthenticated } = useAuth();

  // Only show for authenticated users
  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border-light bg-white/95 backdrop-blur-sm md:hidden dark:border-dark-border-light dark:bg-dark-surface-primary/95 safe-area-bottom"
      aria-label="Mobile navigation"
    >
      <div className="mx-auto flex max-w-md items-center justify-between px-4 pt-2 pb-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex flex-1 flex-col items-center gap-1 py-1 text-xs font-medium transition-colors',
                  'text-text-tertiary hover:text-text-secondary',
                  isActive && 'text-electric-blue'
                )
              }
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}

export default BottomNav;
