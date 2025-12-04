import { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { User, LogOut, Menu, X } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { ThemeToggle } from '../ThemeToggle';

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const prevPathname = useRef(location.pathname);

  // Close mobile menu on route change - use layout effect to avoid flash
  // This is intentional: we want to close the menu when navigating
  useLayoutEffect(() => {
    if (prevPathname.current !== location.pathname) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsMobileMenuOpen(false);
      prevPathname.current = location.pathname;
    }
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  const handleLogout = () => {
    setIsMobileMenuOpen(false);
    logout();
  };

  return (
    <header className="sticky top-0 z-50 glass border-b border-border-light">
      <div className="container mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <img
              src="/images/logo-192.png"
              alt="CareerSwiftr"
              className="w-8 h-8 rounded-lg"
            />
            <div className="flex flex-col">
              <span className="font-heading font-bold text-lg leading-none">
                Interview Simulator
              </span>
              <span className="text-xs text-text-tertiary hidden sm:block">by CareerSwiftr</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-text-secondary hover:text-text-primary transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/questions"
                  className="text-text-secondary hover:text-text-primary transition-colors"
                >
                  Questions
                </Link>
                <Link
                  to="/settings"
                  className="text-text-secondary hover:text-text-primary transition-colors"
                >
                  Settings
                </Link>

                {/* Theme Toggle */}
                <ThemeToggle />

                {/* User Menu */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-secondary">
                    <User className="w-4 h-4 text-text-secondary" />
                    <span className="text-sm font-medium">{user?.full_name}</span>
                  </div>

                  <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-text-secondary hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm font-medium">Logout</span>
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Theme Toggle for non-authenticated users */}
                <ThemeToggle />

                <Link
                  to="/login"
                  className="px-4 py-2 rounded-lg text-text-secondary hover:text-text-primary transition-colors"
                >
                  Login
                </Link>
                <Link to="/register" className="btn-primary">
                  Get Started
                </Link>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-3 md:hidden">
            <ThemeToggle />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <nav className="md:hidden mt-4 pb-4 border-t border-border-light pt-4">
            {isAuthenticated ? (
              <div className="flex flex-col gap-2">
                {/* User info */}
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-secondary mb-2">
                  <User className="w-4 h-4 text-text-secondary" />
                  <span className="text-sm font-medium">{user?.full_name}</span>
                </div>

                <Link
                  to="/dashboard"
                  className="px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/questions"
                  className="px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
                >
                  Questions
                </Link>
                <Link
                  to="/settings"
                  className="px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
                >
                  Settings
                </Link>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors mt-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm font-medium">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <Link
                  to="/login"
                  className="px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="btn-primary text-center"
                >
                  Get Started
                </Link>
              </div>
            )}
          </nav>
        )}
      </div>
    </header>
  );
}
