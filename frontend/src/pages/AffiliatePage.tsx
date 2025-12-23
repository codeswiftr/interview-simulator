import { Link } from 'react-router-dom';
import { DollarSign, Users, TrendingUp, CheckCircle, ArrowRight, Mail } from 'lucide-react';
import { analytics } from '../lib/analytics';

const AFFILIATE_EMAIL = 'affiliates@codeswiftr.com';
const MAILTO_LINK = `mailto:${AFFILIATE_EMAIL}?subject=Affiliate%20Program%20Interest&body=Hi%2C%0A%0AI'm%20interested%20in%20joining%20the%20Interview%20Simulator%20affiliate%20program.%0A%0AMy%20platform%2Faudience%3A%20%0A%0AThanks!`;

// Track affiliate interest in PostHog
const trackAffiliateInterest = (source: string) => {
  analytics.track('affiliate_interest_clicked', { source });
};

const benefits = [
  {
    icon: DollarSign,
    title: '25% Recurring Commission',
    description: 'Earn 25% of every payment for 12 months. Monthly subscriptions mean monthly payouts.',
  },
  {
    icon: TrendingUp,
    title: '60-Day Cookie Duration',
    description: 'Your referrals have 60 days to convert. Plenty of time for them to try the free tier first.',
  },
  {
    icon: Users,
    title: 'Dedicated Dashboard',
    description: 'Track your referrals, conversions, and earnings in real-time with our affiliate portal.',
  },
];

const features = [
  'No minimum payout threshold',
  'Monthly PayPal or Wise payouts',
  'Real-time conversion tracking',
  'Custom referral links',
  'Marketing materials provided',
  'Priority support for affiliates',
];

export default function AffiliatePage() {
  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <span className="inline-block px-4 py-1.5 bg-electric-blue/10 text-electric-blue rounded-full text-sm font-medium">
              Affiliate Program
            </span>
            <span className="inline-block px-3 py-1 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-full text-xs font-semibold">
              Coming Soon
            </span>
          </div>
          <h1 className="heading-display mb-6">
            Earn Money Helping Engineers<br />
            <span className="text-electric-blue">Land Their Dream Jobs</span>
          </h1>
          <p className="text-xl text-text-secondary mb-8 max-w-2xl mx-auto">
            Our affiliate program is launching soon. Register your interest now to be among the first affiliates
            and earn 25% recurring commission for every customer you refer.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href={MAILTO_LINK}
              onClick={() => trackAffiliateInterest('hero_cta')}
              className="btn-primary inline-flex items-center gap-2"
            >
              Register Interest
              <Mail size={18} />
            </a>
            <Link to="/register" className="btn-secondary inline-flex items-center gap-2">
              Try the Product First
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-16 px-4 bg-surface-secondary">
        <div className="max-w-5xl mx-auto">
          <h2 className="heading-page text-center mb-12">Why Join Our Program?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {benefits.map((benefit) => (
              <div key={benefit.title} className="card p-6 text-center">
                <div className="w-14 h-14 bg-electric-blue/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <benefit.icon size={28} className="text-electric-blue" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">{benefit.title}</h3>
                <p className="text-text-secondary">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="heading-page text-center mb-12">How It Works</h2>
          <div className="space-y-8">
            <div className="flex items-start gap-6">
              <div className="w-10 h-10 bg-electric-blue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                1
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-1">Sign Up for Free</h3>
                <p className="text-text-secondary">
                  Create your affiliate account in seconds. No approval process or waiting period.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-6">
              <div className="w-10 h-10 bg-electric-blue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                2
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-1">Share Your Link</h3>
                <p className="text-text-secondary">
                  Get your unique referral link and share it with your audience via blog posts, social media, newsletters, or videos.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-6">
              <div className="w-10 h-10 bg-electric-blue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                3
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-1">Earn Commissions</h3>
                <p className="text-text-secondary">
                  When someone signs up using your link and upgrades to Pro, you earn 25% of their subscription - every month for a full year.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features List Section */}
      <section className="py-16 px-4 bg-surface-secondary">
        <div className="max-w-4xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="heading-section mb-6">Everything You Need to Succeed</h2>
              <ul className="space-y-3">
                {features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3">
                    <CheckCircle size={20} className="text-green-500 flex-shrink-0" />
                    <span className="text-text-primary">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-8 text-center">
              <p className="text-text-secondary mb-2">Example earnings</p>
              <p className="text-4xl font-bold text-electric-blue mb-2">$870/year</p>
              <p className="text-sm text-text-tertiary">
                From just 10 Pro monthly referrals @ $29/month
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="heading-page mb-4">Be the First to Know</h2>
          <p className="text-text-secondary mb-8">
            Our affiliate program is launching soon. Register your interest now and we'll notify you
            as soon as signups open. Early affiliates get priority onboarding and support.
          </p>
          <a
            href={MAILTO_LINK}
            onClick={() => trackAffiliateInterest('bottom_cta')}
            className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-4"
          >
            Register Your Interest
            <Mail size={20} />
          </a>
          <p className="text-sm text-text-tertiary mt-4">
            Questions? Email us at {AFFILIATE_EMAIL}
          </p>
        </div>
      </section>
    </div>
  );
}
