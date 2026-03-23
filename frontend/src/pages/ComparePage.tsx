import { Link } from 'react-router-dom';
import { Check, X, Minus, Crown, ArrowRight, Zap, Clock, DollarSign, Star } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { usePageMeta } from '../hooks/usePageMeta';

interface ComparisonRow {
  feature: string;
  interviewSim: string | boolean | 'highlight';
  leetcode: string | boolean;
  pramp: string | boolean;
  interviewingIo: string | boolean;
  highlight?: boolean;
}

const COMPARISON_ROWS: ComparisonRow[] = [
  {
    feature: 'AI-powered feedback',
    interviewSim: 'Real-time, multi-dimensional',
    leetcode: false,
    pramp: false,
    interviewingIo: 'Human reviewers only',
    highlight: true,
  },
  {
    feature: 'Behavioral coaching (STAR)',
    interviewSim: true,
    leetcode: false,
    pramp: false,
    interviewingIo: false,
    highlight: true,
  },
  {
    feature: 'System design practice',
    interviewSim: true,
    leetcode: 'Limited (text only)',
    pramp: true,
    interviewingIo: true,
  },
  {
    feature: 'Technical coding practice',
    interviewSim: true,
    leetcode: true,
    pramp: true,
    interviewingIo: true,
  },
  {
    feature: 'Video analysis',
    interviewSim: 'Pro tier',
    leetcode: false,
    pramp: false,
    interviewingIo: false,
    highlight: true,
  },
  {
    feature: 'Available 24/7',
    interviewSim: true,
    leetcode: true,
    pramp: false,
    interviewingIo: false,
    highlight: true,
  },
  {
    feature: 'No scheduling required',
    interviewSim: true,
    leetcode: true,
    pramp: false,
    interviewingIo: false,
  },
  {
    feature: 'Spoken response practice',
    interviewSim: true,
    leetcode: false,
    pramp: true,
    interviewingIo: true,
    highlight: true,
  },
  {
    feature: 'Company-specific questions',
    interviewSim: 'Pro tier',
    leetcode: 'Premium only',
    pramp: false,
    interviewingIo: false,
  },
  {
    feature: 'Progress analytics',
    interviewSim: true,
    leetcode: true,
    pramp: false,
    interviewingIo: false,
  },
  {
    feature: 'Starting price',
    interviewSim: 'Free / $19/mo',
    leetcode: 'Free / $35/mo',
    pramp: 'Free',
    interviewingIo: '$100+/session',
    highlight: true,
  },
  {
    feature: 'Team/org plans',
    interviewSim: '$99/mo (5 seats)',
    leetcode: 'Enterprise only',
    pramp: false,
    interviewingIo: false,
  },
];

const WINNERS = [
  {
    icon: Zap,
    title: 'Instant feedback',
    description: 'No waiting for a human reviewer. Start a session, finish in 10 minutes, get your score immediately.',
  },
  {
    icon: Clock,
    title: 'Practice on your schedule',
    description: 'No booking a 1-hour slot days in advance. Open the app at midnight before your interview if you need to.',
  },
  {
    icon: Star,
    title: 'Full-stack interview prep',
    description: 'Behavioral, technical, and system design — all in one place, all with structured AI feedback.',
  },
  {
    icon: DollarSign,
    title: 'The best value',
    description: 'Interviewing.io charges $100+ per session. Interview Simulator gives you unlimited practice for $19/month.',
  },
];

type CellValue = string | boolean;

function ComparisonCell({ value, isIs }: { value: CellValue; isIs?: boolean }) {
  if (value === true) {
    return (
      <td className={`text-center py-4 px-3 ${isIs ? 'bg-electric-blue/5' : ''}`}>
        <Check className="w-5 h-5 text-status-success mx-auto" />
      </td>
    );
  }
  if (value === false) {
    return (
      <td className={`text-center py-4 px-3 ${isIs ? 'bg-electric-blue/5' : ''}`}>
        <X className="w-5 h-5 text-text-tertiary mx-auto" />
      </td>
    );
  }
  return (
    <td className={`text-center py-4 px-3 text-sm ${isIs ? 'bg-electric-blue/5 text-text-primary font-medium' : 'text-text-secondary'}`}>
      {value}
    </td>
  );
}

export default function ComparePage() {
  usePageMeta({
    title: 'Interview Simulator vs LeetCode, Pramp, Interviewing.io | CareerSwiftr',
    description: 'How does Interview Simulator compare to LeetCode, Pramp, and Interviewing.io? See a side-by-side feature comparison.',
    ogTitle: 'Interview Simulator vs the Competition',
    ogDescription: 'AI-powered feedback, 24/7 availability, full-stack prep for $19/month. See how we compare.',
  });

  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Hero */}
      <section className="relative pt-16 sm:pt-20 pb-10 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-electric-blue/15 dark:bg-electric-blue/10 blur-[80px]" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[400px] h-[400px] rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-[90px]" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[hsl(var(--card))]/50 border border-[hsl(var(--border))]/60 backdrop-blur-sm shadow-sm mb-6 animate-fade-in">
            <span className="text-xs font-medium text-text-secondary">Side-by-side comparison</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 text-text-primary animate-slide-up">
            Interview Simulator vs{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-electric-blue to-indigo-500">
              the Alternatives
            </span>
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
            LeetCode drills your code. Pramp and Interviewing.io need scheduling. Interview Simulator is the only platform that gives you AI-powered feedback on behavioral, technical, and system design responses — available 24/7.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <Link to="/register" className="btn-primary inline-flex items-center justify-center gap-2">
              Start Free — No Credit Card
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/pricing" className="btn-secondary inline-flex items-center justify-center gap-2">
              <Crown className="w-4 h-4" />
              View Pricing
            </Link>
          </div>
        </div>
      </section>

      {/* Why we win */}
      <section className="py-10 sm:py-16 bg-[hsl(var(--muted))]">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-xl sm:text-2xl font-bold text-center mb-8 text-text-primary">
            Why engineers choose Interview Simulator
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {WINNERS.map((item, idx) => {
              const Icon = item.icon;
              return (
                <Card key={idx} animate={idx + 1} className="p-5">
                  <div className="w-10 h-10 rounded-xl bg-electric-blue/10 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-electric-blue" />
                  </div>
                  <h3 className="font-semibold text-text-primary mb-2 text-sm">{item.title}</h3>
                  <p className="text-text-secondary text-xs leading-relaxed">{item.description}</p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Comparison table — desktop */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12 text-text-primary">
            Feature-by-feature breakdown
          </h2>

          <div className="hidden md:block max-w-5xl mx-auto overflow-x-auto rounded-xl border border-[hsl(var(--border))] shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[hsl(var(--border))] bg-[hsl(var(--muted))]">
                  <th className="text-left py-5 px-4 text-text-secondary font-medium w-1/4">Feature</th>
                  <th className="text-center py-5 px-3 w-[18%]">
                    <div className="flex flex-col items-center gap-1">
                      <span className="px-3 py-1 bg-electric-blue text-white text-xs font-bold rounded-full">Interview Simulator</span>
                      <span className="text-xs text-electric-blue font-semibold">codeswiftr.com</span>
                    </div>
                  </th>
                  <th className="text-center py-5 px-3 text-text-secondary font-medium w-[18%]">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-sm font-semibold">LeetCode</span>
                      <span className="text-xs text-text-tertiary">leetcode.com</span>
                    </div>
                  </th>
                  <th className="text-center py-5 px-3 text-text-secondary font-medium w-[18%]">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-sm font-semibold">Pramp</span>
                      <span className="text-xs text-text-tertiary">pramp.com</span>
                    </div>
                  </th>
                  <th className="text-center py-5 px-3 text-text-secondary font-medium w-[18%]">
                    <div className="flex flex-col items-center gap-1">
                      <span className="text-sm font-semibold">Interviewing.io</span>
                      <span className="text-xs text-text-tertiary">interviewing.io</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-[hsl(var(--card))]">
                {COMPARISON_ROWS.map((row, idx) => (
                  <tr
                    key={idx}
                    className={`border-b border-[hsl(var(--border))]/60 last:border-0 ${
                      row.highlight ? 'bg-electric-blue/2' : ''
                    }`}
                  >
                    <td className="py-4 px-4 text-text-primary font-medium text-sm">
                      {row.feature}
                      {row.highlight && (
                        <span className="ml-2 inline-flex items-center">
                          <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                        </span>
                      )}
                    </td>
                    <ComparisonCell value={row.interviewSim} isIs />
                    <ComparisonCell value={row.leetcode} />
                    <ComparisonCell value={row.pramp} />
                    <ComparisonCell value={row.interviewingIo} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: card-based comparison */}
          <div className="md:hidden max-w-md mx-auto space-y-6">
            {/* IS card */}
            <Card className="p-5 border-2 border-electric-blue">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-bold text-text-primary">Interview Simulator</h3>
                  <p className="text-xs text-text-tertiary">codeswiftr.com</p>
                </div>
                <span className="px-3 py-1 bg-electric-blue text-white text-xs font-bold rounded-full">Our pick</span>
              </div>
              <ul className="space-y-2">
                {[
                  'Real-time AI feedback on every response',
                  'Behavioral, technical, and system design',
                  'Available 24/7 — no scheduling',
                  'Video analysis (Pro)',
                  'Free to start — $19/month Pro',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                    <Check className="w-4 h-4 text-status-success flex-shrink-0 mt-0.5" />
                    {item}
                  </li>
                ))}
              </ul>
            </Card>

            {/* Competitors summary */}
            {[
              {
                name: 'LeetCode',
                pros: ['Huge problem bank', 'Great for coding prep'],
                cons: ['No behavioral prep', 'No spoken feedback', '$35/month premium'],
              },
              {
                name: 'Pramp',
                pros: ['Real human interviewers', 'Free to use'],
                cons: ['Requires scheduling', 'Limited to coding + system design', 'No AI feedback'],
              },
              {
                name: 'Interviewing.io',
                pros: ['Real engineers from top companies', 'High-signal feedback'],
                cons: ['$100+ per session', 'Must book in advance', 'No behavioral coverage'],
              },
            ].map((alt, idx) => (
              <Card key={idx} className="p-5">
                <h3 className="font-semibold text-text-primary mb-3">{alt.name}</h3>
                <div className="space-y-2 mb-3">
                  {alt.pros.map((p, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-text-secondary">
                      <Check className="w-4 h-4 text-status-success flex-shrink-0" />
                      {p}
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  {alt.cons.map((c, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-text-tertiary">
                      <Minus className="w-4 h-4 text-status-warning flex-shrink-0" />
                      {c}
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>

          <p className="text-xs text-text-tertiary text-center mt-6">
            Competitor data based on publicly available pricing and feature pages as of March 2026. Pricing may vary.
          </p>
        </div>
      </section>

      {/* Testimonials / social proof */}
      <section className="py-12 sm:py-16 bg-[hsl(var(--muted))]">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-xl sm:text-2xl font-bold text-center mb-8 text-text-primary">
            What engineers are saying
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              {
                quote: "I used LeetCode for 6 months and still bombed my behavioral rounds. Two weeks with Interview Simulator and I had a FAANG offer.",
                author: 'Senior SWE',
                detail: 'Google L5, offer accepted',
              },
              {
                quote: "Pramp is great but finding a partner at 11pm the night before an interview is impossible. IS is always there.",
                author: 'Staff Engineer',
                detail: 'Stripe, 2025',
              },
              {
                quote: "Worth every dollar. I went from stumbling through system design to confidently explaining trade-offs. The AI feedback is uncomfortably accurate.",
                author: 'ML Engineer',
                detail: 'Meta, 2025',
              },
            ].map((t, idx) => (
              <Card key={idx} animate={idx + 1} className="p-6">
                <div className="flex gap-1 mb-3">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 text-amber-400 fill-amber-400" />
                  ))}
                </div>
                <p className="text-text-secondary text-sm leading-relaxed mb-4">"{t.quote}"</p>
                <div>
                  <p className="text-text-primary font-medium text-sm">{t.author}</p>
                  <p className="text-text-tertiary text-xs">{t.detail}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-16 sm:py-24 bg-charcoal dark:bg-surface-dark-alt relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-electric-blue/20 blur-[150px] rounded-full pointer-events-none" />

        <div className="container mx-auto px-4 sm:px-6 text-center relative z-10">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4 text-text-inverse">
            The smarter way to prepare
          </h2>
          <p className="text-lg text-text-secondary max-w-xl mx-auto mb-4">
            Stop grinding LeetCode without feedback. Start practicing the full interview — behavioral, technical, and system design — with AI that tells you exactly what to improve.
          </p>
          <p className="text-sm text-text-tertiary mb-8">
            3 free interviews per month. No credit card required.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="btn-primary px-8 py-3 inline-flex items-center justify-center gap-2"
            >
              Start Free — No Credit Card
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/pricing"
              className="btn-secondary px-8 py-3 bg-white/10 hover:bg-white/20 text-white border-white/20 inline-flex items-center justify-center gap-2"
            >
              <Crown className="w-4 h-4" />
              See Pro Pricing
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
