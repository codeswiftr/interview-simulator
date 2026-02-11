import { Link } from 'react-router-dom';
import { Mic, BarChart2, TrendingUp, MessageSquare, ArrowRight, CheckCircle2, Crown, Check } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Card } from '../components/ui/Card';

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-surface-primary overflow-hidden">
      {/* Hero Section */}
      <section className="relative pt-16 sm:pt-24 lg:pt-48 pb-12 sm:pb-16 lg:pb-32 overflow-hidden">
        {/* Abstract Background Elements - Theme Aware */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-electric-blue/20 dark:bg-electric-blue/10 blur-[100px] animate-pulse-glow" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: '1s' }} />
        </div>

        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full bg-[hsl(var(--card))]/50 dark:bg-[hsl(var(--card))]/80 border border-[hsl(var(--border))]/60 backdrop-blur-sm shadow-sm mb-6 sm:mb-8 animate-fade-in">
              <span className="flex h-2 w-2 rounded-full bg-[#FF6B9D]"></span>
              <span className="text-xs sm:text-sm font-medium text-text-secondary">AI-Powered Interview Coach</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-6xl xl:text-7xl font-bold leading-tight mb-4 sm:mb-6 text-text-primary animate-slide-up">
              Master Your Interview Skills with <span className="text-transparent bg-clip-text bg-gradient-to-r from-electric-blue to-indigo-600">Real-Time AI Feedback</span>
            </h1>

            <p className="text-base sm:text-lg text-text-secondary mb-6 sm:mb-8 lg:mb-10 max-w-2xl mx-auto animate-slide-up" style={{ animationDelay: '0.1s' }}>
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
          <div className="mt-12 sm:mt-16 lg:mt-20 relative max-w-5xl mx-auto animate-scale-in" style={{ animationDelay: '0.3s' }}>
            <div className="absolute -inset-1 bg-gradient-to-r from-electric-blue to-indigo-600 rounded-2xl blur opacity-20 dark:opacity-10"></div>
            <div className="relative rounded-xl sm:rounded-2xl overflow-hidden shadow-2xl border border-[hsl(var(--border))]/20 bg-[hsl(var(--card))]/50 dark:bg-[hsl(var(--card))]/30 backdrop-blur-xl">
              <img
                src="/images/hero-illustration.png"
                alt="Dashboard Preview"
                className="w-full h-auto rounded-xl sm:rounded-2xl"
                loading="eager"
                decoding="async"
                fetchPriority="high"
              />
              {/* Floating Elements */}
              <div className="absolute top-4 right-4 sm:top-10 sm:right-10 p-3 sm:p-4 bg-[hsl(var(--card))]/90 backdrop-blur-md rounded-lg sm:rounded-xl shadow-lg border border-[hsl(var(--border))]/50 animate-float hidden sm:block">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[#FF6B9D]/10 dark:bg-[#FF6B9D]/20 flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5 sm:w-6 sm:h-6 text-[#FF6B9D]" />
                  </div>
                  <div>
                    <p className="text-xs text-text-secondary font-medium uppercase">Audio Score</p>
                    <p className="text-lg sm:text-xl font-bold text-text-primary">92/100</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 sm:py-16 lg:py-24 bg-[hsl(var(--muted))] relative">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-8 sm:mb-12 lg:mb-16">
            <h2 className="text-xl sm:text-2xl lg:text-3xl font-semibold mb-3 sm:mb-4 text-text-primary">Everything you need to excel</h2>
            <p className="text-sm sm:text-base text-text-secondary">
              Our platform provides comprehensive tools to help you prepare for behavioral, technical, and system design interviews.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
            <Card variant="elevated" className="p-4 sm:p-6 lg:p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-xl sm:rounded-2xl bg-electric-blue/10 flex items-center justify-center mb-4 sm:mb-6">
                <Mic className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-electric-blue" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-text-primary">Voice Recording</h3>
              <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
                Practice your answers out loud. Our advanced audio capture simulates real interview conditions.
              </p>
            </Card>

            <Card variant="elevated" className="p-4 sm:p-6 lg:p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-xl sm:rounded-2xl bg-[#FF6B9D]/10 flex items-center justify-center mb-4 sm:mb-6">
                <BarChart2 className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-[#FF6B9D]" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-text-primary">AI Feedback</h3>
              <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
                Get instant, detailed analysis of your content, delivery, and structure with actionable tips.
              </p>
            </Card>

            <Card variant="elevated" className="p-4 sm:p-6 lg:p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-xl sm:rounded-2xl bg-amber-500/10 flex items-center justify-center mb-4 sm:mb-6">
                <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-amber-500" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-text-primary">Track Progress</h3>
              <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
                Monitor your improvement over time with detailed analytics and performance metrics.
              </p>
            </Card>

            <Card variant="elevated" className="p-4 sm:p-6 lg:p-8 hover:translate-y-[-4px] transition-transform duration-300">
              <div className="w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-xl sm:rounded-2xl bg-indigo-500/10 flex items-center justify-center mb-4 sm:mb-6">
                <MessageSquare className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-indigo-500" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-text-primary">Question Bank</h3>
              <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
                Access hundreds of real interview questions across multiple categories and difficulty levels.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* Pricing Preview Section */}
      <section className="py-12 sm:py-16 lg:py-24 bg-surface-primary">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-8 sm:mb-12">
            <h2 className="text-xl sm:text-2xl lg:text-3xl font-semibold mb-3 sm:mb-4 text-text-primary">
              Simple, Transparent Pricing
            </h2>
            <p className="text-sm sm:text-base text-text-secondary">
              Start free with 3 interviews per month. Upgrade for unlimited access.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Free Plan */}
            <Card className="p-6 border-2 border-border-light">
              <h3 className="text-lg font-bold mb-2 text-text-primary">Free</h3>
              <div className="text-3xl font-bold mb-4 text-text-primary">
                $0<span className="text-lg font-normal text-text-secondary">/month</span>
              </div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2 text-text-secondary text-sm">
                  <Check className="w-4 h-4 text-status-success" />
                  3 interviews per month
                </li>
                <li className="flex items-center gap-2 text-text-secondary text-sm">
                  <Check className="w-4 h-4 text-status-success" />
                  Basic AI feedback
                </li>
                <li className="flex items-center gap-2 text-text-secondary text-sm">
                  <Check className="w-4 h-4 text-status-success" />
                  Progress tracking
                </li>
              </ul>
              <Link to="/register" className="btn-secondary w-full text-center">
                Get Started Free
              </Link>
            </Card>

            {/* Pro Plan */}
            <Card className="p-6 border-2 border-[#FF6B9D] bg-[#FF6B9D]/5 relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-[#FF6B9D] text-white text-xs font-semibold rounded-full">
                7-DAY FREE TRIAL
              </span>
              <div className="flex items-center gap-2 mb-2">
                <Crown className="w-5 h-5 text-[#FF6B9D]" />
                <h3 className="text-lg font-bold text-text-primary">Pro</h3>
              </div>
              <div className="text-3xl font-bold mb-4 text-text-primary">
                $29<span className="text-lg font-normal text-text-secondary">/month</span>
              </div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center gap-2 text-text-secondary text-sm">
                  <Check className="w-4 h-4 text-status-success" />
                  Unlimited interviews
                </li>
                <li className="flex items-center gap-2 text-text-secondary text-sm">
                  <Check className="w-4 h-4 text-status-success" />
                  Advanced AI feedback
                </li>
                <li className="flex items-center gap-2 text-text-secondary text-sm">
                  <Check className="w-4 h-4 text-status-success" />
                  Company-specific questions
                </li>
              </ul>
              <Link to="/pricing" className="btn-primary w-full text-center">
                View Full Pricing
              </Link>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-16 lg:py-24 relative overflow-hidden bg-charcoal dark:bg-surface-dark-alt">
        {/* Background Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] sm:w-[800px] h-[600px] sm:h-[800px] bg-electric-blue/20 blur-[100px] sm:blur-[150px] rounded-full pointer-events-none"></div>

        <div className="container mx-auto px-4 sm:px-6 text-center relative z-10">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-semibold mb-4 sm:mb-6 text-text-inverse">Ready to Ace Your Next Interview?</h2>
          <p className="text-base sm:text-lg mb-6 sm:mb-8 lg:mb-10 text-text-secondary max-w-2xl mx-auto">
            Join thousands of engineers who have improved their interview skills with our AI-powered simulator.
          </p>

          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="btn-primary inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 bg-[hsl(var(--card))] text-text-primary hover:opacity-90"
            >
              Go to Dashboard
            </Link>
          ) : (
            <Link
              to="/register"
              className="btn-primary inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4"
            >
              Get Started Now
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
