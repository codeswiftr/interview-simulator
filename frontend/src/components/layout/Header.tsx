import { useState, useLayoutEffect, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LogOut, Menu, X, Settings, ChevronDown, Plus, Shuffle, RefreshCw, Play } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { ThemeSlider } from '../ThemeSlider';
import { useScrollDirection } from '../../hooks/useScrollDirection';

// Contextual action configuration per route
interface ContextualAction {
  icon: React.ElementType;
  label: string;
  onClick?: () => void;
  to?: string;
}

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  const prevPathname = useRef(location.pathname);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const scrollDirection = useScrollDirection({ threshold: 15 });

  // Determine if header should be hidden on mobile (only when scrolling down and authenticated)
  const shouldHideOnMobile = isAuthenticated && scrollDirection === 'down';

  // Get contextual action based on current route
  const getContextualAction = (): ContextualAction | null => {
    const path = location.pathname;

    if (path === '/dashboard') {
      return {
        icon: Plus,
        label: 'New',
        // Dashboard handles this via its own modal - we emit a custom event
        onClick: () => window.dispatchEvent(new CustomEvent('open-new-interview')),
      };
    }

    if (path === '/practice' || path === '/questions') {
      return {
        icon: Shuffle,
        label: 'Random',
        onClick: () => window.dispatchEvent(new CustomEvent('random-practice')),
      };
    }

    if (path === '/progress') {
      return {
        icon: Play,
        label: 'Practice',
        to: '/practice',
      };
    }

    if (path === '/analytics') {
      return {
        icon: Play,
        label: 'Practice',
        to: '/practice',
      };
    }

    // Feedback page - /interview/:id/feedback
    if (path.match(/^\/interview\/[^/]+\/feedback$/)) {
      return {
        icon: RefreshCw,
        label: 'Again',
        to: '/dashboard',
      };
    }

    return null;
  };

  const contextualAction = isAuthenticated ? getContextualAction() : null;

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

      <header
        className={`sticky top-0 z-50 glass border-b border-border-light transition-transform duration-300 ease-out ${
          shouldHideOnMobile ? 'md:translate-y-0 -translate-y-full' : 'translate-y-0'
        }`}
      >
        <div className="container mx-auto px-4 sm:px-6 py-2.5 sm:py-3">
          <div className="flex items-center justify-between h-12 sm:h-14">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <img
                src="/images/logo-192.png"
                alt="CareerSwiftr"
                className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg"
                width="32"
                height="32"
                loading="eager"
                decoding="async"
              />
              <div className="flex flex-col">
                <span className="font-heading font-bold text-base sm:text-lg leading-none text-[var(--fg-primary)]">
                  Interview Simulator
                </span>
                <span className="text-[10px] sm:text-xs hidden sm:block leading-tight">
                  <span className="text-[#FF6B9D] font-semibold">Code</span>
                  <span className="text-text-tertiary">Swiftr</span>
                </span>
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
                  <Link
                    to="/progress"
                    className="text-text-secondary hover:text-text-primary transition-colors font-medium"
                  >
                    Progress
                  </Link>
                  <Link
                    to="/analytics"
                    className="text-text-secondary hover:text-text-primary transition-colors font-medium"
                  >
                    Analytics
                  </Link>

                  {/* User Menu Dropdown */}
                  <div className="relative" ref={userMenuRef}>
                    <button
                      onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-surface-secondary transition-colors"
                      aria-label="User menu"
                      aria-expanded={isUserMenuOpen}
                      aria-haspopup="true"
                    >
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-electric-blue to-indigo-500 flex items-center justify-center text-white font-bold text-xs">
                        {user?.full_name?.charAt(0) || 'U'}
                      </div>
                      <span className="text-sm font-medium text-text-primary">{user?.full_name}</span>
                      <ChevronDown className={`w-3.5 h-3.5 text-text-tertiary transition-transform ${isUserMenuOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
                    </button>

                    {isUserMenuOpen && (
                      <div className="absolute right-0 mt-2 w-72 bg-[hsl(var(--card))] dark:bg-[hsl(var(--card))] rounded-xl shadow-lg border border-[hsl(var(--border))] overflow-hidden animate-scale-in origin-top-right z-50">
                        {/* User Info */}
                        <div className="p-4 border-b border-[hsl(var(--border))]">
                          <p className="text-sm font-semibold text-text-primary">{user?.full_name}</p>
                          <p className="text-xs text-text-secondary truncate mt-0.5">{user?.email}</p>
                        </div>

                        {/* Settings Link */}
                        <div className="p-2">
                          <Link
                            to="/settings"
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-[hsl(var(--muted))] transition-colors focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-1"
                          >
                            <Settings size={18} aria-hidden="true" />
                            <span className="text-sm font-medium">Settings</span>
                          </Link>
                        </div>

                        {/* Theme Selector */}
                        <div className="px-4 py-3 border-t border-[hsl(var(--border))]">
                          <p className="text-xs font-semibold text-text-tertiary mb-2 uppercase tracking-wider">Theme</p>
                          <ThemeSlider />
                        </div>

                        {/* Logout */}
                        <div className="p-2 border-t border-[hsl(var(--border))]">
                          <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-status-error hover:bg-status-error/10 transition-colors focus:outline-none focus:ring-2 focus:ring-status-error focus:ring-offset-1"
                          >
                            <LogOut size={18} aria-hidden="true" />
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
                    to="/pricing"
                    className="px-3 py-1.5 rounded-lg text-text-secondary hover:text-text-primary transition-colors font-medium text-sm"
                  >
                    Pricing
                  </Link>
                  <Link
                    to="/login"
                    className="px-3 py-1.5 rounded-lg text-text-secondary hover:text-text-primary transition-colors font-medium text-sm"
                  >
                    Login
                  </Link>
                  <Link to="/register" className="btn-primary text-sm px-4 py-1.5">
                    Get Started
                  </Link>
                  <div className="ml-2">
                    <ThemeSlider />
                  </div>
                </>
              )}
            </nav>

            {/* Mobile Contextual Action - Only show when authenticated */}
            {isAuthenticated && contextualAction && (
              <div className="flex items-center md:hidden">
                {contextualAction.to ? (
                  <Link
                    to={contextualAction.to}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-electric-blue text-white text-sm font-medium shadow-sm active:scale-95 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-electric-blue focus-visible:ring-offset-2"
                  >
                    <contextualAction.icon className="w-4 h-4" aria-hidden="true" />
                    <span>{contextualAction.label}</span>
                  </Link>
                ) : (
                  <button
                    onClick={contextualAction.onClick}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-electric-blue text-white text-sm font-medium shadow-sm active:scale-95 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-electric-blue focus-visible:ring-offset-2"
                  >
                    <contextualAction.icon className="w-4 h-4" aria-hidden="true" />
                    <span>{contextualAction.label}</span>
                  </button>
                )}
              </div>
            )}

            {/* Mobile Menu Button - Only show when not authenticated (no BottomNav) */}
            {!isAuthenticated && (
              <div className="flex items-center gap-3 md:hidden">
                <button
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                  className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors"
                  aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
                  aria-expanded={isMobileMenuOpen}
                >
                  {isMobileMenuOpen ? (
                    <X className="w-6 h-6" aria-hidden="true" />
                  ) : (
                    <Menu className="w-6 h-6" aria-hidden="true" />
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu - Only show when not authenticated (authenticated users use BottomNav) */}
          {isMobileMenuOpen && !isAuthenticated && (
            <nav className="md:hidden mt-3 pb-3 border-t border-border-light pt-3 animate-slide-up">
              <div className="flex flex-col gap-3">
                <div className="px-2">
                  <ThemeSlider />
                </div>
                <Link
                  to="/pricing"
                  className="px-3 py-2.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors font-medium text-center text-sm"
                >
                  Pricing
                </Link>
                <Link
                  to="/login"
                  className="px-3 py-2.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-secondary transition-colors font-medium text-center border border-border-light text-sm"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="btn-primary text-center text-sm py-2.5"
                >
                  Get Started
                </Link>
              </div>
            </nav>
          )}
        </div>
      </header>
    </>
  );
}
