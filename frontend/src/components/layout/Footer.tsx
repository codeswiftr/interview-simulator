import { Link } from 'react-router-dom';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-surface-secondary border-t border-border-light py-8 hidden md:block">
      <div className="container mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Logo & Copyright */}
          <div className="flex items-center gap-4">
            <Link to="/" className="flex items-center gap-2">
              <img
                src="/images/logo-192.png"
                alt="CareerSwiftr"
                className="w-6 h-6 rounded"
                width="24"
                height="24"
              />
              <span className="font-heading font-semibold text-sm text-text-primary">
                Interview Simulator
              </span>
            </Link>
            <span className="text-text-tertiary text-sm">
              &copy; {currentYear} CodeSwiftr
            </span>
          </div>

          {/* Links */}
          <nav className="flex items-center gap-6 text-sm">
            <Link
              to="/affiliates"
              className="text-text-secondary hover:text-electric-blue transition-colors font-medium"
            >
              Affiliate Program
            </Link>
            <a
              href="mailto:support@codeswiftr.com"
              className="text-text-secondary hover:text-text-primary transition-colors"
            >
              Contact
            </a>
          </nav>
        </div>
      </div>
    </footer>
  );
}
