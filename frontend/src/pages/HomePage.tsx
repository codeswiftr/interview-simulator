import { Link } from 'react-router-dom';
import { Mic, BarChart2, TrendingUp, MessageSquare } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-charcoal to-gray-800 text-white py-20">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center max-w-6xl mx-auto">
            <div className="text-center lg:text-left">
              <h1 className="heading-hero mb-6 text-white">
                Master Your Interview Skills with AI-Powered Practice
              </h1>
              <p className="body-large text-gray-300 mb-8">
                Simulate real interview scenarios, get instant feedback, and track your progress.
                Practice behavioral, technical, and system design questions with confidence.
              </p>
              <div className="flex gap-4 justify-center lg:justify-start">
                {isAuthenticated ? (
                  <Link to="/dashboard" className="btn-primary">
                    Go to Dashboard
                  </Link>
                ) : (
                  <>
                    <Link to="/register" className="btn-primary">
                      Start Practicing Free
                    </Link>
                    <Link
                      to="/login"
                      className="px-6 py-3 rounded-lg font-semibold text-white border border-white/30 hover:bg-white/10 transition-all"
                    >
                      Login
                    </Link>
                  </>
                )}
              </div>
            </div>
            <div className="hidden lg:block">
              <img
                src="/images/hero-illustration.png"
                alt="AI-powered interview practice"
                className="w-full max-w-lg mx-auto rounded-2xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-surface-primary">
        <div className="container mx-auto px-6">
          <h2 className="heading-section text-center mb-12">
            Why Interview Simulator?
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-electric-blue/10 flex items-center justify-center mb-4">
                <Mic className="w-6 h-6 text-electric-blue" />
              </div>
              <h3 className="heading-card mb-3">Voice Recording</h3>
              <p className="body-small text-text-secondary">
                Practice your answers out loud with voice recording to simulate real interview conditions.
              </p>
            </div>

            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-score-excellent/10 flex items-center justify-center mb-4">
                <BarChart2 className="w-6 h-6 text-score-excellent" />
              </div>
              <h3 className="heading-card mb-3">AI Feedback</h3>
              <p className="body-small text-text-secondary">
                Get detailed analysis of your content, delivery, and structure with actionable improvement tips.
              </p>
            </div>

            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center mb-4">
                <TrendingUp className="w-6 h-6 text-amber-500" />
              </div>
              <h3 className="heading-card mb-3">Track Progress</h3>
              <p className="body-small text-text-secondary">
                Monitor your improvement over time with detailed analytics and performance metrics.
              </p>
            </div>

            <div className="card p-6">
              <div className="w-12 h-12 rounded-lg bg-indigo-500/10 flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-indigo-500" />
              </div>
              <h3 className="heading-card mb-3">Question Bank</h3>
              <p className="body-small text-text-secondary">
                Access hundreds of real interview questions across behavioral, technical, and system design categories.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-electric-blue to-sky-500 text-white">
        <div className="container mx-auto px-6 text-center">
          <h2 className="heading-section mb-6 text-white">Ready to Ace Your Next Interview?</h2>
          <p className="body-large mb-8 text-white/90 max-w-2xl mx-auto">
            Join thousands of engineers who have improved their interview skills with our AI-powered simulator.
          </p>
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="inline-block px-8 py-4 rounded-lg font-semibold bg-white text-electric-blue hover:bg-gray-100 transition-colors"
            >
              Go to Dashboard
            </Link>
          ) : (
            <Link
              to="/register"
              className="inline-block px-8 py-4 rounded-lg font-semibold bg-white text-electric-blue hover:bg-gray-100 transition-colors"
            >
              Get Started Now
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
