import { Link } from 'react-router-dom';
import { Mic, BarChart2, TrendingUp, MessageSquare, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-surface-primary overflow-hidden">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Abstract Background Elements - Theme Aware */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-electric-blue/20 dark:bg-electric-blue/10 blur-[100px] animate-pulse-glow" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: '1s' }} />
        </div>

        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/50 dark:bg-surface-secondary/80 border border-white/60 dark:border-border-light backdrop-blur-sm shadow-sm mb-8 animate-fade-in">
              <span className="flex h-2 w-2 rounded-full bg-electric-blue"></span>
              <span className="text-sm font-medium text-text-secondary">AI-Powered Interview Coach</span>
            </div>

            <h1 className="heading-hero mb-6 text-text-primary animate-slide-up">
              Master Your Interview Skills with <span className="text-transparent bg-clip-text bg-gradient-to-r from-electric-blue to-indigo-600">Real-Time AI Feedback</span>
            </h1>

            <p className="body-large text-text-secondary mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '0.1s' }}>
              Simulate real interview scenarios, record your answers, and get instant, actionable feedback to land your dream job.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn-primary flex items-center justify-center gap-2 group">
                  Go to Dashboard
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn-primary flex items-center justify-center gap-2 group">
                    Start Practicing Free
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                  <Link
                    to="/login"
                    className="btn-secondary"
                  >
                    Login
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Hero Visual */}
          <div className="mt-20 relative max-w-5xl mx-auto animate-scale-in" style={{ animationDelay: '0.3s' }}>
            <div className="absolute -inset-1 bg-gradient-to-r from-electric-blue to-indigo-600 rounded-2xl blur opacity-20 dark:opacity-10"></div>
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-white/20 dark:border-border-light bg-white/50 dark:bg-surface-secondary/30 backdrop-blur-xl">
              <img
                src="/images/hero-illustration.png"
                alt="Dashboard Preview"
                className="w-full h-auto rounded-2xl"
                loading="eager"
                decoding="async"
                fetchPriority="high"
              />
              {/* Floating Elements */}
              <div className="absolute top-10 right-10 p-4 bg-white/90 dark:bg-surface-secondary/90 backdrop-blur-md rounded-xl shadow-lg border border-white/50 dark:border-border-light animate-float hidden md:block">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-xs text-text-secondary font-medium uppercase">Audio Score</p>
                    <p className="text-xl font-bold text-charcoal dark:text-text-primary">92/100</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-surface-secondary relative">
        <div className="container mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="heading-section mb-4">Everything you need to excel</h2>
            <p className="body-default text-text-secondary">
              Our platform provides comprehensive tools to help you prepare for behavioral, technical, and system design interviews.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="card-glass p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-electric-blue/10 flex items-center justify-center mb-6">
                <Mic className="w-7 h-7 text-electric-blue" />
              </div>
              <h3 className="heading-card mb-3">Voice Recording</h3>
              <p className="body-small text-text-secondary leading-relaxed">
                Practice your answers out loud. Our advanced audio capture simulates real interview conditions.
              </p>
            </div>

            <div className="card-glass p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-score-excellent/10 flex items-center justify-center mb-6">
                <BarChart2 className="w-7 h-7 text-score-excellent" />
              </div>
              <h3 className="heading-card mb-3">AI Feedback</h3>
              <p className="body-small text-text-secondary leading-relaxed">
                Get instant, detailed analysis of your content, delivery, and structure with actionable tips.
              </p>
            </div>

            <div className="card-glass p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-amber-500/10 flex items-center justify-center mb-6">
                <TrendingUp className="w-7 h-7 text-amber-500" />
              </div>
              <h3 className="heading-card mb-3">Track Progress</h3>
              <p className="body-small text-text-secondary leading-relaxed">
                Monitor your improvement over time with detailed analytics and performance metrics.
              </p>
            </div>

            <div className="card-glass p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center mb-6">
                <MessageSquare className="w-7 h-7 text-indigo-500" />
              </div>
              <h3 className="heading-card mb-3">Question Bank</h3>
              <p className="body-small text-text-secondary leading-relaxed">
                Access hundreds of real interview questions across multiple categories and difficulty levels.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-charcoal -z-20"></div>
        <div className="absolute inset-0 bg-gradient-to-br from-charcoal to-gray-900 -z-10"></div>

        {/* Background Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-electric-blue/20 blur-[150px] rounded-full pointer-events-none"></div>

        <div className="container mx-auto px-6 text-center relative z-10">
          <h2 className="heading-section text-4xl mb-6 text-white">Ready to Ace Your Next Interview?</h2>
          <p className="body-large mb-10 text-gray-300 max-w-2xl mx-auto">
            Join thousands of engineers who have improved their interview skills with our AI-powered simulator.
          </p>

          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl font-bold bg-white text-charcoal hover:bg-gray-50 transition-all shadow-lg hover:shadow-xl hover:-translate-y-1"
            >
              Go to Dashboard
            </Link>
          ) : (
            <Link
              to="/register"
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl font-bold bg-electric-blue text-white hover:bg-sky-400 transition-all shadow-lg hover:shadow-electric-blue/50 hover:-translate-y-1"
            >
              Get Started Now
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
