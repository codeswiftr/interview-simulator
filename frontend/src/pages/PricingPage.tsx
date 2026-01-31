import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, X, Crown, Zap, Users, ArrowRight, ChevronDown, Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { subscriptionsAPI } from '../lib/api';
import { analytics, Events } from '../lib/analytics';
import { Card } from '../components/ui/Card';

interface PricingConfig {
  pro_monthly_price_id: string | null;
  pro_annual_price_id: string | null;
}

// Pricing constants
const MONTHLY_PRICE = 19;
const ANNUAL_PRICE = 290; // $24/month, save 2 months
const ANNUAL_MONTHLY_EQUIVALENT = 24;

export default function PricingPage() {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');
  const [pricing, setPricing] = useState<PricingConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  // Fetch pricing configuration
  useEffect(() => {
    subscriptionsAPI.getPricing()
      .then((response) => {
        setPricing(response.data);
      })
      .catch((err) => {
        console.error('Failed to fetch pricing:', err);
      });
  }, []);

  // Track page view
  useEffect(() => {
    analytics.track(Events.PAGE_VIEWED, { page: 'pricing' });
  }, []);

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      // Redirect to register with plan intent
      navigate(`/register?plan=pro&billing=${billingPeriod}`);
      return;
    }

    if (user?.subscription_tier === 'pro') {
      // Already pro, go to settings
      navigate('/settings');
      return;
    }

    // Create checkout session
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
    } catch (err) {
      setError('Failed to start checkout. Please try again.');
      setLoading(false);
    }
  };

  const features = {
    free: [
      { name: '5 interviews per month', included: true },
      { name: 'Basic AI feedback', included: true },
      { name: 'Question bank access', included: true },
      { name: 'Progress tracking', included: true },
      { name: 'Unlimited interviews', included: false },
      { name: 'Advanced feedback analysis', included: false },
      { name: 'Company-specific questions', included: false },
      { name: 'Export & share interviews', included: false },
      { name: 'Priority support', included: false },
    ],
    pro: [
      { name: '5 interviews per month', included: true, highlight: 'Unlimited interviews' },
      { name: 'Basic AI feedback', included: true, highlight: 'Advanced feedback analysis' },
      { name: 'Question bank access', included: true },
      { name: 'Progress tracking', included: true },
      { name: 'Unlimited interviews', included: true },
      { name: 'Advanced feedback analysis', included: true },
      { name: 'Company-specific questions', included: true },
      { name: 'Export & share interviews', included: true },
      { name: 'Priority support', included: true },
    ],
  };

  const faqs = [
    {
      question: 'What happens after my 7-day free trial?',
      answer: 'After your trial ends, you\'ll be automatically charged for the plan you selected. You can cancel anytime before the trial ends and won\'t be charged. We\'ll send you a reminder email before your trial expires.',
    },
    {
      question: 'Can I cancel my subscription anytime?',
      answer: 'Yes! You can cancel your subscription at any time from your settings page. Your access will continue until the end of your current billing period, and you won\'t be charged again.',
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit and debit cards (Visa, Mastercard, American Express, Discover) through our secure payment processor, Stripe. We don\'t store your card details on our servers.',
    },
    {
      question: 'Is there a limit on interview length?',
      answer: 'Each interview response can be up to 5 minutes long, which matches real behavioral interview expectations. There\'s no limit on how many questions you can answer in a session.',
    },
    {
      question: 'How does the AI feedback work?',
      answer: 'Our AI analyzes your response across multiple dimensions: content quality, STAR method usage, communication clarity, and delivery. Pro users get deeper analysis including sentiment, pacing, and specific improvement suggestions.',
    },
    {
      question: 'Can I switch between monthly and annual billing?',
      answer: 'Yes! You can switch between billing periods anytime. If you switch from monthly to annual, you\'ll get a prorated credit. If you switch from annual to monthly, the change takes effect at your next renewal.',
    },
  ];

  const currentPrice = billingPeriod === 'annual' ? ANNUAL_MONTHLY_EQUIVALENT : MONTHLY_PRICE;
  const isCurrentPlan = isAuthenticated && user?.subscription_tier === 'pro';

  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Hero Section */}
      <section className="relative pt-16 sm:pt-20 pb-8 sm:pb-12 overflow-hidden">
        {/* Background */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-electric-blue/15 dark:bg-electric-blue/10 blur-[80px]" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[#FF6B9D]/10 dark:bg-[#FF6B9D]/5 blur-[100px]" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 text-text-primary">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-8">
            Start free, upgrade when you're ready. No hidden fees, cancel anytime.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center gap-3 p-1.5 bg-surface-secondary rounded-full mb-8">
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
              <span className="px-2 py-0.5 bg-status-success/20 text-status-success text-xs rounded-full">
                2 months free
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-16 sm:pb-24">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-4xl mx-auto">
            {/* Free Plan */}
            <Card className="p-6 sm:p-8 border-2 border-border-light relative">
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-text-tertiary" />
                  <h3 className="text-xl font-bold text-text-primary">Free</h3>
                </div>
                <p className="text-text-secondary text-sm">Perfect for getting started</p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-text-primary">$0</span>
                  <span className="text-text-secondary">/month</span>
                </div>
              </div>

              <Link
                to={isAuthenticated ? '/dashboard' : '/register'}
                className="btn-secondary w-full mb-8 flex items-center justify-center gap-2"
              >
                {isAuthenticated ? 'Go to Dashboard' : 'Get Started Free'}
                <ArrowRight className="w-4 h-4" />
              </Link>

              <ul className="space-y-3">
                {features.free.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    {feature.included ? (
                      <Check className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
                    ) : (
                      <X className="w-5 h-5 text-text-tertiary flex-shrink-0 mt-0.5" />
                    )}
                    <span className={feature.included ? 'text-text-secondary' : 'text-text-tertiary'}>
                      {feature.name}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Pro Plan */}
            <Card className="p-6 sm:p-8 border-2 border-[#FF6B9D] relative bg-[#FF6B9D]/5">
              {/* Popular Badge */}
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="px-4 py-1 bg-[#FF6B9D] text-white text-xs font-semibold rounded-full shadow-lg">
                  MOST POPULAR
                </span>
              </div>

              {/* Trial Badge */}
              <div className="absolute top-4 right-4">
                <span className="px-2.5 py-1 bg-status-success/20 text-status-success text-xs font-medium rounded-full">
                  7-day free trial
                </span>
              </div>
              {/* Founding Member Badge */}
              <div className="absolute top-4 left-4">
                <span className="px-2.5 py-1 bg-amber-500/15 text-amber-700 text-xs font-semibold rounded-full border border-amber-500/30">
                  Founding Member
                </span>
              </div>

              <div className="mb-6 mt-2">
                <div className="flex items-center gap-2 mb-2">
                  <Crown className="w-5 h-5 text-[#FF6B9D]" />
                  <h3 className="text-xl font-bold text-text-primary">Pro</h3>
                </div>
                <p className="text-text-secondary text-sm">For serious interview prep</p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-text-primary">${currentPrice}</span>
                  <span className="text-text-secondary">/month</span>
                </div>
                <p className="text-xs text-amber-700 mt-1 font-medium">
                  $19/mo for life — only 20 spots left
                </p>
                {billingPeriod === 'annual' && (
                  <p className="text-sm text-status-success mt-1">
                    ${ANNUAL_PRICE}/year ($24/month, save 2 months)
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
                ) : isAuthenticated ? (
                  <>
                    <Crown className="w-4 h-4" />
                    Start Free Trial
                  </>
                ) : (
                  <>
                    <Crown className="w-4 h-4" />
                    Start Free Trial
                  </>
                )}
              </button>

              <ul className="space-y-3">
                {features.pro.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
                    <span className="text-text-secondary">
                      {feature.highlight || feature.name}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          {/* Team Plan Teaser */}
          <Card className="max-w-4xl mx-auto mt-8 p-6 sm:p-8 border-2 border-dashed border-border-light">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                  <Users className="w-6 h-6 text-indigo-500" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-text-primary">Team Plans Coming Soon</h3>
                  <p className="text-text-secondary text-sm">
                    Bulk licensing, admin dashboard, and team analytics
                  </p>
                </div>
              </div>
              <Link
                to="/register?notify=team"
                className="btn-secondary whitespace-nowrap"
              >
                Get Notified
              </Link>
            </div>
          </Card>
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="py-16 sm:py-24 bg-[hsl(var(--muted))]">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12 text-text-primary">
            Compare Plans
          </h2>

          <div className="max-w-3xl mx-auto overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-light">
                  <th className="text-left py-4 px-4 text-text-secondary font-medium">Feature</th>
                  <th className="text-center py-4 px-4 text-text-secondary font-medium">Free</th>
                  <th className="text-center py-4 px-4 text-text-secondary font-medium">Pro</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">Interviews per month</td>
                  <td className="text-center py-4 px-4 text-text-secondary">5</td>
                  <td className="text-center py-4 px-4 text-text-primary font-medium">Unlimited</td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">AI Feedback</td>
                  <td className="text-center py-4 px-4 text-text-secondary">Basic</td>
                  <td className="text-center py-4 px-4 text-text-primary font-medium">Advanced</td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">Question Bank</td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">Progress Tracking</td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">Company-Specific Questions</td>
                  <td className="text-center py-4 px-4"><X className="w-5 h-5 text-text-tertiary mx-auto" /></td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">Export & Share</td>
                  <td className="text-center py-4 px-4"><X className="w-5 h-5 text-text-tertiary mx-auto" /></td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                </tr>
                <tr className="border-b border-border-light">
                  <td className="py-4 px-4 text-text-primary">Priority Support</td>
                  <td className="text-center py-4 px-4"><X className="w-5 h-5 text-text-tertiary mx-auto" /></td>
                  <td className="text-center py-4 px-4"><Check className="w-5 h-5 text-status-success mx-auto" /></td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-text-primary">Audio Response Limit</td>
                  <td className="text-center py-4 px-4 text-text-secondary">5 min</td>
                  <td className="text-center py-4 px-4 text-text-secondary">5 min</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-text-primary">
            Frequently Asked Questions
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-2xl mx-auto">
            Everything you need to know about our pricing and plans
          </p>

          <div className="max-w-2xl mx-auto space-y-4">
            {faqs.map((faq, idx) => (
              <Card key={idx} className="overflow-hidden">
                <button
                  onClick={() => setExpandedFaq(expandedFaq === idx ? null : idx)}
                  className="w-full p-5 flex items-center justify-between text-left hover:bg-surface-secondary/50 transition-colors"
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
            Join thousands of engineers who've improved their interview skills. Start with a 7-day free trial.
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
                  'You\'re on Pro!'
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
        </div>
      </section>
    </div>
  );
}
