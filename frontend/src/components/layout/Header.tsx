import { Link } from 'react-router-dom';
import { User, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 glass border-b border-border-light">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-electric-blue to-sky-500 flex items-center justify-center">
              <span className="text-white font-bold text-lg">CS</span>
            </div>
            <div className="flex flex-col">
              <span className="font-heading font-bold text-lg leading-none">
                Interview Simulator
              </span>
              <span className="text-xs text-text-tertiary">by CodeSwiftr</span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-text-secondary hover:text-text-primary transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  to="/settings"
                  className="text-text-secondary hover:text-text-primary transition-colors"
                >
                  Settings
                </Link>

                {/* User Menu */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-secondary">
                    <User className="w-4 h-4 text-text-secondary" />
                    <span className="text-sm font-medium">{user?.full_name}</span>
                  </div>

                  <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-text-secondary hover:text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="text-sm font-medium">Logout</span>
                  </button>
                </div>
              </>
            ) : (
              <>
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
        </div>
      </div>
    </header>
  );
}
