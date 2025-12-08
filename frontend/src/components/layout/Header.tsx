import { useState, useLayoutEffect, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LogOut, Menu, X, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { ThemeSlider } from '../ThemeSlider';

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  const prevPathname = useRef(location.pathname);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close mobile menu on route change
  useLayoutEffect(() => {
    if (prevPathname.current !== location.pathname) {
      setIsMobileMenuOpen(false);
      setIsUserMenuOpen(false);
      prevPathname.current = location.pathname;
    }
  }, [location.pathname]);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
    setIsUserMenuOpen(false);
    logout();
  };

  return (
    <>
      {/* Skip to main content link for keyboard users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only"
      >
        Skip to main content
      </a>

      <header className="sticky top-0 z-50 glass border-b border-border-light">
        <div className="container mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <img
              src="/images/logo-192.png"
              alt="CareerSwiftr"
              className="w-8 h-8 rounded-lg"
              width="32"
              height="32"
              loading="eager"
              decoding="async"
            />
            <div className="flex flex-col">
              <span className="font-heading font-bold text-lg leading-none text-[var(--fg-primary)]">
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
                  className="text-text-secondary hover:text-text-primary transition-colors font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/questions"
                  className="text-text-secondary hover:text-text-primary transition-colors font-medium"
                >
                  Questions
                </Link>
                
                {/* User Menu Dropdown */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-secondary transition-colors"
                    aria-label="User menu"
                    aria-expanded={isUserMenuOpen}
                    aria-haspopup="true"
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-electric-blue to-indigo-500 flex items-center justify-center text-white font-bold text-sm">
                      {user?.full_name?.charAt(0) || 'U'}
                    </div>
                    <span className="text-sm font-medium text-text-primary">{user?.full_name}</span>
                    <ChevronDown className={`w-4 h-4 text-text-tertiary transition-transform ${isUserMenuOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
                  </button>

                  {isUserMenuOpen && (
                    <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-surface-dark-alt rounded-xl shadow-xl border border-border-light dark:border-border-medium overflow-hidden animate-scale-in origin-top-right">
                      <div className="p-4 border-b border-border-light dark:border-border-medium">
                        <p className="text-sm font-medium text-text-primary dark:text-white">{user?.full_name}</p>
                        <p className="text-xs text-text-secondary truncate">{user?.email}</p>
                      </div>
                      
                      <div className="p-2">
                        <Link
                          to="/settings"
                          className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary dark:hover:bg-surface-tertiary transition-colors"
                        >
                          <Settings size={18} />
                          <span className="text-sm">Settings</span>
                        </Link>
                      </div>

                      <div className="px-4 py-2 border-t border-border-light dark:border-border-medium">
                        <p className="text-xs font-medium text-text-tertiary mb-2 uppercase">Theme</p>
                        <ThemeSlider />
                      </div>

                      <div className="p-2 border-t border-border-light dark:border-border-medium">
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        >
                          <LogOut size={18} />
                          <span className="text-sm font-medium">Logout</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-lg text-text-secondary hover:text-text-primary transition-colors font-medium"
                >
                  Login
                </Link>
                <Link to="/register" className="btn-primary">
                  Get Started
                </Link>
                <div className="ml-2">
                   <ThemeSlider />
                </div>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-3 md:hidden">
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
          <nav className="md:hidden mt-4 pb-4 border-t border-border-light pt-4 animate-slide-up">
            {isAuthenticated ? (
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3 px-3 py-3 rounded-lg bg-surface-secondary mb-2">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-electric-blue to-indigo-500 flex items-center justify-center text-white font-bold">
                    {user?.full_name?.charAt(0) || 'U'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{user?.full_name}</p>
                    <p className="text-xs text-text-secondary">{user?.email}</p>
                  </div>
                </div>

                <Link
                  to="/dashboard"
                  className="px-3 py-3 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/questions"
                  className="px-3 py-3 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors font-medium"
                >
                  Questions
                </Link>
                <Link
                  to="/settings"
                  className="px-3 py-3 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors font-medium"
                >
                  Settings
                </Link>

                <div className="px-3 py-3">
                  <p className="text-xs font-medium text-text-tertiary mb-2 uppercase">Theme</p>
                  <ThemeSlider />
                </div>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-3 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors mt-2"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="text-sm font-medium">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="px-3">
                  <ThemeSlider />
                </div>
                <Link
                  to="/login"
                  className="px-3 py-3 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors font-medium text-center border border-border-light"
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
    </>
  );
}
