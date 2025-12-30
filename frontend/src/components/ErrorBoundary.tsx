import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { Link } from 'react-router-dom';
import { captureError } from '../lib/sentry';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Report to Sentry with component stack context
    captureError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
    });

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
          <div className="card p-8 max-w-md w-full text-center">
            <AlertCircle className="w-16 h-16 text-status-error mx-auto mb-4" />
            <h2 className="heading-section mb-4">Something went wrong</h2>
            <p className="body-default text-text-secondary mb-6">
              We encountered an unexpected error. Please try refreshing the page or return to the
              dashboard.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <details className="text-left mb-6">
                <summary className="body-small text-text-tertiary cursor-pointer mb-2">
                  Error details (development only)
                </summary>
                <pre className="text-xs bg-surface-secondary p-4 rounded overflow-auto max-h-48">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}

            <div className="flex flex-col sm:flex-row gap-4">
              <button onClick={this.handleReset} className="btn-primary flex-1 inline-flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              <Link to="/dashboard" className="btn-secondary flex-1 inline-flex items-center justify-center gap-2">
                <Home className="w-4 h-4" />
                Go Home
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

