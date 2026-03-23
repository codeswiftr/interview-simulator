import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, X, Crown, Zap, Users, ArrowRight, ChevronDown, Loader2, GitCompare, HelpCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { subscriptionsAPI } from '../lib/api';
import { analytics, Events } from '../lib/analytics';
import { Card } from '../components/ui/Card';
import { usePageMeta } from '../hooks/usePageMeta';

interface PricingConfig {
  pro_monthly_price_id: string | null;
  pro_annual_price_id: string | null;
}

// Pricing constants (Pro $19/month, Team $99/month 5 seats)
const MONTHLY_PRICE = 19;
const ANNUAL_PRICE = 149; // $149/year — save ~34%
const ANNUAL_MONTHLY_EQUIVALENT = Math.round((149 / 12) * 10) / 10; // ~$12.4/month

export default function PricingPage() {
  usePageMeta({
    title: 'Pricing | Interview Simulator - CareerSwiftr',
    description: 'Practice unlimited AI interviews for $19/month. Behavioral, technical, system design. Start free — no credit card required.',
    ogTitle: 'Interview Simulator Pricing — $19/month',
    ogDescription: 'Unlimited AI-powered interview practice. Real-time feedback on all question types. Start with 3 free interviews.',
  });

  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');
  const [pricing, setPricing] = useState<PricingConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  useEffect(() => {
    subscriptionsAPI.getPricing()
      .then((response) => {
        setPricing(response.data);
      })
      .catch((err) => {
        console.error('Failed to fetch pricing:', err);
      });
  }, []);

  useEffect(() => {
    analytics.track(Events.PAGE_VIEWED, { page: 'pricing' });
  }, []);

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      navigate(`/register?plan=pro&billing=${billingPeriod}`);
      return;
    }

    if (user?.subscription_tier === 'pro') {
      navigate('/settings');
      return;
    }

    const priceId = billingPeriod === 'annual'
      ? pricing?.pro_annual_price_id
      : pricing?.pro_monthly_price_id;

    if (!priceId) {
      setError('Pricing not configured. Please contact support.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      analytics.track(Events.UPGRADE_CTA_CLICKED, {
        surface: 'pricing_page',
        plan: 'pro',
        billing_period: billingPeriod,
      });

      const response = await subscriptionsAPI.createCheckout(priceId);
      window.location.href = response.data.url;
    } catch {
      setError('Failed to start checkout. Please try again.');
      setLoading(false);
    }
  };

  const freeFeatures = [
    { name: '3 AI interviews per month', included: true },
    { name: 'Basic AI feedback', included: true },
    { name: 'Easy coding questions only', included: true },
    { name: 'Progress tracking', included: true },
    { name: 'Unlimited interviews', included: false },
    { name: 'All question types', included: false },
    { name: 'Detailed analytics', included: false },
    { name: 'Video feedback', included: false },
    { name: 'Priority AI models', included: false },
  ];

  const proFeatures = [
    { name: 'Unlimited AI interviews', included: true },
    { name: 'All question types (behavioral, technical, system design)', included: true },
    { name: 'Detailed analytics & scoring', included: true },
    { name: 'Video feedback analysis', included: true },
    { name: 'Priority AI models', included: true },
    { name: 'Company-specific questions', included: true },
    { name: 'Export & share interviews', included: true },
    { name: 'Priority support', included: true },
    { name: 'STAR method coaching', included: true },
  ];

  const teamFeatures = [
    'Everything in Pro',
    '5 team seats included',
    'Team dashboard & analytics',
    'Usage analytics per member',
    'Admin controls & seat management',
    'Team invitations & onboarding',
    'Priority support',
  ];

  const faqs = [
    {
      question: "What's included in the free tier?",
      answer: "The free tier gives you 3 AI-powered interviews per month, basic feedback on your responses, and access to easy coding questions. It\'s perfect for getting a feel for the platform before committing.",
    },
    {
      question: 'Can I cancel anytime?',
      answer: "Yes — cancel anytime from your settings page. Your access continues until the end of your current billing period, and you won\'t be charged again. No questions asked.",
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit and debit cards (Visa, Mastercard, American Express, Discover) via Stripe. We never store your card details on our servers.',
    },
    {
      question: 'Do you offer student discounts?',
      answer: 'Yes! Students with a valid .edu email address can get 40% off Pro. Email us at hello@codeswiftr.com with your school email and we\'ll send you a discount code within 24 hours.',
    },
  ];

  const currentPrice = billingPeriod === 'annual' ? ANNUAL_MONTHLY_EQUIVALENT : MONTHLY_PRICE;
  const annualSavings = Math.round(((MONTHLY_PRICE * 12 - ANNUAL_PRICE) / (MONTHLY_PRICE * 12)) * 100);
  const isCurrentPlan = isAuthenticated && user?.subscription_tier === 'pro';

  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Hero */}
      <section className="relative pt-16 sm:pt-20 pb-8 sm:pb-12 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-electric-blue/15 dark:bg-electric-blue/10 blur-[80px]" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[#FF6B9D]/10 dark:bg-[#FF6B9D]/5 blur-[100px]" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 text-center">
          <div
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[hsl(var(--card))]/50 border border-[hsl(var(--border))]/60 backdrop-blur-sm shadow-sm mb-6 animate-fade-in"
          >
            <span className="flex h-2 w-2 rounded-full bg-status-success"></span>
            <span className="text-xs font-medium text-text-secondary">Founding member pricing — locked until May 2026</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 text-text-primary animate-slide-up">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Start free, upgrade when you're ready. No hidden fees, cancel anytime.
          </p>

          {/* Social proof */}
          <p className="text-sm text-text-tertiary mb-6 animate-slide-up" style={{ animationDelay: '0.15s' }}>
            Trusted by 2,000+ engineers preparing for FAANG, startups, and everything in between
          </p>

          {/* Billing toggle */}
          <div
            className="inline-flex items-center gap-3 p-1.5 bg-surface-secondary rounded-full mb-10 animate-slide-up"
            style={{ animationDelay: '0.2s' }}
          >
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                billingPeriod === 'monthly'
                  ? 'bg-[hsl(var(--card))] text-text-primary shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('annual')}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                billingPeriod === 'annual'
                  ? 'bg-[hsl(var(--card))] text-text-primary shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Annual
              <span className="px-2 py-0.5 bg-status-success/20 text-status-success text-xs rounded-full font-semibold">
                Save {annualSavings}%
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-16 sm:pb-24">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 lg:gap-8 max-w-5xl mx-auto">

            {/* Free */}
            <Card animate={1} className="p-6 sm:p-8 border-2 border-border-light relative">
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-text-tertiary" />
                  <h3 className="text-xl font-bold text-text-primary">Free</h3>
                </div>
                <p className="text-text-secondary text-sm">Perfect for getting started</p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-text-primary font-mono">$0</span>
                  <span className="text-text-secondary">/month</span>
                </div>
                <p className="text-xs text-text-tertiary mt-1">No credit card required</p>
              </div>

              <Link
                to={isAuthenticated ? '/dashboard' : '/register'}
                className="btn-secondary w-full mb-8 flex items-center justify-center gap-2"
              >
                {isAuthenticated ? 'Go to Dashboard' : 'Start Free'}
                <ArrowRight className="w-4 h-4" />
              </Link>

              <ul className="space-y-3">
                {freeFeatures.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    {feature.included ? (
                      <Check className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
                    ) : (
                      <X className="w-5 h-5 text-text-tertiary flex-shrink-0 mt-0.5" />
                    )}
                    <span className={feature.included ? 'text-text-secondary' : 'text-text-tertiary text-sm'}>
                      {feature.name}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Pro — highlighted */}
            <Card animate={2} className="p-6 sm:p-8 border-2 border-[#FF6B9D] relative bg-[#FF6B9D]/5">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className="px-4 py-1 bg-[#FF6B9D] text-white text-xs font-semibold rounded-full shadow-lg">
                  MOST POPULAR
                </span>
              </div>

              <div className="mb-6 mt-2">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <Crown className="w-5 h-5 text-[#FF6B9D]" />
                    <h3 className="text-xl font-bold text-text-primary">Pro</h3>
                  </div>
                  <span className="px-2.5 py-1 bg-status-success/20 text-status-success text-xs font-medium rounded-full">
                    7-day free trial
                  </span>
                </div>
                <p className="text-text-secondary text-sm">For serious interview prep</p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-text-primary font-mono">${currentPrice}</span>
                  <span className="text-text-secondary">/month</span>
                </div>
                {billingPeriod === 'annual' ? (
                  <p className="text-sm text-status-success mt-1">
                    ${ANNUAL_PRICE}/year — save {annualSavings}%
                  </p>
                ) : (
                  <p className="text-xs text-text-tertiary mt-1">
                    Or ${ANNUAL_PRICE}/year (save {annualSavings}%)
                  </p>
                )}
              </div>

              {error && (
                <div className="mb-4 p-3 bg-status-error/10 border border-status-error/20 rounded-lg">
                  <p className="text-status-error text-sm">{error}</p>
                </div>
              )}

              <button
                onClick={handleUpgrade}
                disabled={loading || isCurrentPlan}
                className="btn-primary w-full mb-8 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : isCurrentPlan ? (
                  'Current Plan'
                ) : (
                  <>
                    <Crown className="w-4 h-4" />
                    Upgrade to Pro
                  </>
                )}
              </button>

              <ul className="space-y-3">
                {proFeatures.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
                    <span className="text-text-secondary">{feature.name}</span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Team */}
            <Card animate={3} className="p-6 sm:p-8 border-2 border-border-light relative opacity-80">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="px-4 py-1 bg-surface-secondary text-text-secondary text-xs font-semibold rounded-full shadow border border-border-light">
                  COMING SOON
                </span>
              </div>

              <div className="mb-6 mt-2">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-xl font-bold text-text-primary">Team</h3>
                </div>
                <p className="text-text-secondary text-sm">For engineering teams and bootcamps</p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-text-primary font-mono">$99</span>
                  <span className="text-text-secondary">/mo</span>
                </div>
                <p className="text-xs text-text-tertiary mt-1">
                  5 seats included — $19.80/seat
                </p>
              </div>

              <a
                href="mailto:team@codeswiftr.com?subject=Team%20Plan%20Interest"
                className="btn-secondary w-full mb-8 flex items-center justify-center gap-2 opacity-90"
              >
                Contact Sales
              </a>

              <ul className="space-y-3">
                {teamFeatures.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-text-tertiary flex-shrink-0 mt-0.5" />
                    <span className="text-text-secondary">{feature}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          {/* Enterprise CTA */}
          <Card className="max-w-4xl mx-auto mt-8 p-6 sm:p-8 border-2 border-dashed border-border-light">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                  <Users className="w-6 h-6 text-indigo-500" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-text-primary">Enterprise</h3>
                  <p className="text-text-secondary text-sm">
                    Custom pricing for large teams. Bulk licensing, admin dashboard, SSO, and dedicated support.
                  </p>
                </div>
              </div>
              <a
                href="mailto:hello@codeswiftr.com?subject=Enterprise%20Plan%20Inquiry"
                className="btn-secondary whitespace-nowrap"
              >
                Contact Sales
              </a>
            </div>
          </Card>
        </div>
      </section>

      {/* Comparison links */}
      <section className="pb-8">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 text-sm">
            <Link to="/compare" className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
              <GitCompare className="w-4 h-4" />
              How we compare to LeetCode & Pramp
            </Link>
            <Link to="/faq" className="flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors">
              <HelpCircle className="w-4 h-4" />
              Full FAQ
            </Link>
          </div>
        </div>
      </section>

      {/* Feature comparison table */}
      <section className="py-16 sm:py-24 bg-[hsl(var(--muted))]">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12 text-text-primary">
            Compare Plans
          </h2>

          <div className="hidden sm:block max-w-3xl mx-auto overflow-x-auto">
            <table className="w-full text-sm sm:text-base">
              <thead>
                <tr className="border-b border-border-light">
                  <th className="text-left py-4 px-4 text-text-secondary font-medium">Feature</th>
                  <th className="text-center py-4 px-4 text-text-secondary font-medium">Free</th>
                  <th className="text-center py-4 px-4 text-[#FF6B9D] font-semibold">Pro</th>
                  <th className="text-center py-4 px-4 text-text-secondary font-medium">Team</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['Interviews per month', '3', 'Unlimited', 'Unlimited'],
                  ['AI Feedback', 'Basic', 'Advanced', 'Advanced'],
                  ['Question types', 'Easy coding only', 'All types', 'All types'],
                  ['Video feedback', null, true, true],
                  ['Detailed analytics', null, true, true],
                  ['Company-specific questions', null, true, true],
                  ['Team dashboard', null, null, true],
                  ['Admin controls', null, null, true],
                  ['Priority support', null, true, true],
                ].map(([feature, free, pro, team], idx) => (
                  <tr key={idx} className="border-b border-border-light">
                    <td className="py-4 px-4 text-text-primary">{feature}</td>
                    {[free, pro, team].map((val, colIdx) => (
                      <td key={colIdx} className={`text-center py-4 px-4 ${colIdx === 1 ? 'bg-[#FF6B9D]/5' : ''}`}>
                        {val === null ? (
                          <X className="w-5 h-5 text-text-tertiary mx-auto" />
                        ) : val === true ? (
                          <Check className="w-5 h-5 text-status-success mx-auto" />
                        ) : (
                          <span className={colIdx === 1 ? 'text-text-primary font-medium' : 'text-text-secondary'}>{val}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile layout */}
          <div className="sm:hidden max-w-md mx-auto space-y-2">
            {[
              ['Interviews/month', '3', 'Unlimited'],
              ['AI Feedback', 'Basic', 'Advanced'],
              ['Question types', 'Easy only', 'All types'],
            ].map(([feature, free, pro], idx) => (
              <div key={idx} className="flex items-center justify-between py-3 px-2 border-b border-border-light">
                <span className="text-sm text-text-primary pr-2">{feature}</span>
                <div className="flex gap-6 text-sm">
                  <span className="text-text-secondary">{free}</span>
                  <span className="text-[#FF6B9D] font-medium">{pro}</span>
                </div>
              </div>
            ))}
            {[
              ['Video feedback', false, true],
              ['Analytics', false, true],
              ['Company questions', false, true],
            ].map(([feature, free, pro], idx) => (
              <div key={idx} className="flex items-center justify-between py-3 px-2 border-b border-border-light">
                <span className="text-sm text-text-primary pr-2">{feature as string}</span>
                <div className="flex gap-6">
                  {free ? <Check className="w-4 h-4 text-status-success" /> : <X className="w-4 h-4 text-text-tertiary" />}
                  {pro ? <Check className="w-4 h-4 text-status-success" /> : <X className="w-4 h-4 text-text-tertiary" />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mini FAQ */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-text-primary">
            Common Questions
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-2xl mx-auto">
            Quick answers. For the full list, see the{' '}
            <Link to="/faq" className="text-electric-blue hover:underline">FAQ page</Link>.
          </p>

          <div className="max-w-2xl mx-auto space-y-4">
            {faqs.map((faq, idx) => (
              <Card key={idx} className="overflow-hidden">
                <button
                  onClick={() => setExpandedFaq(expandedFaq === idx ? null : idx)}
                  className="w-full p-5 flex items-center justify-between text-left hover:bg-surface-secondary/50 transition-colors min-h-[52px]"
                  aria-expanded={expandedFaq === idx}
                >
                  <span className="font-medium text-text-primary pr-4">{faq.question}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-text-tertiary flex-shrink-0 transition-transform ${
                      expandedFaq === idx ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {expandedFaq === idx && (
                  <div className="px-5 pb-5 text-text-secondary animate-slide-up">
                    {faq.answer}
                  </div>
                )}
              </Card>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link to="/faq" className="btn-secondary inline-flex items-center gap-2">
              <HelpCircle className="w-4 h-4" />
              View all 15 questions
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 sm:py-24 bg-charcoal dark:bg-surface-dark-alt relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-electric-blue/20 blur-[150px] rounded-full pointer-events-none" />

        <div className="container mx-auto px-4 sm:px-6 text-center relative z-10">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4 text-text-inverse">
            Start Your Interview Prep Today
          </h2>
          <p className="text-lg text-text-secondary max-w-xl mx-auto mb-8">
            Join 2,000+ engineers who've improved their interview performance. Start with 3 free interviews — no credit card required.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <button
                onClick={handleUpgrade}
                disabled={loading || isCurrentPlan}
                className="btn-primary px-8 py-3 inline-flex items-center justify-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : isCurrentPlan ? (
                  "You're on Pro!"
                ) : (
                  <>
                    <Crown className="w-5 h-5" />
                    Upgrade to Pro
                  </>
                )}
              </button>
            ) : (
              <>
                <Link
                  to={`/register?plan=pro&billing=${billingPeriod}`}
                  className="btn-primary px-8 py-3 inline-flex items-center justify-center gap-2"
                >
                  <Crown className="w-5 h-5" />
                  Start Free Trial
                </Link>
                <Link
                  to="/register"
                  className="btn-secondary px-8 py-3 bg-white/10 hover:bg-white/20 text-white border-white/20"
                >
                  Try Free Plan
                </Link>
              </>
            )}
          </div>

          <p className="text-sm text-text-tertiary mt-4">
            Pro: 7-day free trial. Cancel anytime. No questions asked.
          </p>
        </div>
      </section>
    </div>
  );
}
