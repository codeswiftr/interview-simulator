import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, Search, ArrowRight, Crown, HelpCircle, MessageSquare } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { usePageMeta } from '../hooks/usePageMeta';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

const ALL_FAQS: FAQItem[] = [
  // Getting Started
  {
    category: 'Getting Started',
    question: 'What is Interview Simulator?',
    answer:
      'Interview Simulator is an AI-powered practice platform that helps you prepare for job interviews. You pick a question, record your response, and receive instant detailed feedback on your answer — covering content, communication, structure, and delivery. It works for behavioral, technical, and system design interviews.',
  },
  {
    category: 'Getting Started',
    question: 'How does AI interview practice work?',
    answer:
      'You select a question type and difficulty, then record your spoken answer (up to 5 minutes). Our AI transcribes your response and analyzes it across multiple dimensions: use of the STAR method, technical accuracy, clarity, pacing, and confidence. You get a score breakdown plus specific suggestions to improve.',
  },
  {
    category: 'Getting Started',
    question: 'Is it really free to start?',
    answer:
      'Yes — no credit card required. Free accounts get 3 AI-powered interviews per month, basic feedback, and access to easy coding questions. Upgrade to Pro whenever you want unlimited access.',
  },
  {
    category: 'Getting Started',
    question: 'What types of interviews can I practice?',
    answer:
      'Interview Simulator covers behavioral (STAR method), technical coding (easy through hard), and system design questions. Pro users get access to all difficulty levels and question types, including company-specific question sets for top employers like Google, Amazon, and Meta.',
  },

  // Product
  {
    category: 'Product',
    question: 'How is this different from LeetCode?',
    answer:
      'LeetCode focuses on written code submissions with no verbal component. Interview Simulator focuses on spoken responses — the skill that actually gets you hired. You practice the full interview experience: speaking through your thought process, explaining trade-offs, and communicating under pressure. We also cover behavioral and system design, not just algorithms.',
  },
  {
    category: 'Product',
    question: 'Can I practice system design interviews?',
    answer:
      'Yes. Pro accounts include system design questions covering distributed systems, databases, caching, API design, and more. Questions are drawn from real interview bank data at companies like Google, Meta, Uber, and Stripe. You get detailed feedback on your architecture choices and communication.',
  },
  {
    category: 'Product',
    question: 'Does it help with behavioral interviews?',
    answer:
      'Yes — behavioral prep is a core strength. The AI explicitly coaches you on STAR method usage (Situation, Task, Action, Result), detects filler words and hedging language, and rates the clarity of your narrative. You get specific rewrites for weak sections so you know exactly what to say next time.',
  },
  {
    category: 'Product',
    question: 'How accurate is the AI feedback?',
    answer:
      'Our feedback models are calibrated against thousands of real interview responses and ratings from senior engineers. Feedback accuracy improves continuously as more users practice. That said, AI feedback complements — rather than replaces — practice with real people. Use it to sharpen your baseline, then validate with mock interviews.',
  },
  {
    category: 'Product',
    question: 'Can I record video of my practice?',
    answer:
      'Video recording is available for Pro users and is currently in beta. It captures your camera alongside your audio response, then analyzes eye contact, posture, and facial expressions to give you a complete picture of how you present in remote interviews.',
  },

  // Pricing & Billing
  {
    category: 'Pricing & Billing',
    question: "What's included in the free tier?",
    answer:
      '3 AI-powered interviews per month, basic feedback on each response, easy coding questions, and basic progress tracking. The free tier is intentionally useful — it gives you enough to evaluate whether the platform works for you before committing.',
  },
  {
    category: 'Pricing & Billing',
    question: 'Can I cancel anytime?',
    answer:
      "Yes — cancel anytime from your account settings. Your Pro access continues until the end of your current billing period. There's no cancellation fee, no retention flows, and no questions asked. We'd rather you come back later than feel trapped.",
  },
  {
    category: 'Pricing & Billing',
    question: 'Do you offer student discounts?',
    answer:
      'Yes. Students with a valid .edu email address get 40% off the Pro plan. Email hello@codeswiftr.com from your school email and we\'ll send a discount code within 24 hours. We also offer free access for students participating in partner bootcamps — ask your program coordinator.',
  },
  {
    category: 'Pricing & Billing',
    question: 'What payment methods do you accept?',
    answer:
      'We accept all major credit and debit cards (Visa, Mastercard, American Express, Discover) processed securely by Stripe. We never store card details on our servers. Annual billing is charged once per year; monthly billing renews on the same date each month.',
  },

  // Team & Enterprise
  {
    category: 'Team & Enterprise',
    question: 'How does team billing work?',
    answer:
      'Team plans start at $99/month for 5 seats. The admin pays a single invoice, then invites teammates by email. Each seat gets full Pro access. Additional seats can be added at $19.80/seat/month. Usage analytics and admin controls let you track team progress from a central dashboard.',
  },
  {
    category: 'Team & Enterprise',
    question: 'Can I get a custom plan?',
    answer:
      "Yes — for teams over 25 seats, bootcamps, universities, and enterprise customers, we offer custom pricing with volume discounts, SSO integration, dedicated onboarding, and an SLA. Email hello@codeswiftr.com or use the Contact Sales button on the pricing page to start a conversation.",
  },
];

const CATEGORIES = ['All', 'Getting Started', 'Product', 'Pricing & Billing', 'Team & Enterprise'];

export default function FAQPage() {
  usePageMeta({
    title: 'FAQ | Interview Simulator - CareerSwiftr',
    description: 'Answers to the most common questions about Interview Simulator — how it works, pricing, video feedback, and team plans.',
    ogTitle: 'Interview Simulator FAQ',
    ogDescription: 'Everything you need to know about AI-powered interview practice.',
  });

  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const filtered = ALL_FAQS.filter((faq) => {
    const matchesCategory = activeCategory === 'All' || faq.category === activeCategory;
    const matchesSearch =
      !searchQuery ||
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const toggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Hero */}
      <section className="relative pt-16 sm:pt-20 pb-12 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[600px] h-[300px] rounded-full bg-electric-blue/10 dark:bg-electric-blue/5 blur-[100px]" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[hsl(var(--card))]/50 border border-[hsl(var(--border))]/60 backdrop-blur-sm shadow-sm mb-6 animate-fade-in">
            <HelpCircle className="w-3.5 h-3.5 text-text-tertiary" />
            <span className="text-xs font-medium text-text-secondary">Frequently Asked Questions</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 text-text-primary animate-slide-up">
            Got Questions?
          </h1>
          <p className="text-lg text-text-secondary max-w-xl mx-auto mb-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Everything you need to know about Interview Simulator — how it works, what's included, and how to get started.
          </p>

          {/* Search */}
          <div
            className="relative max-w-lg mx-auto animate-slide-up"
            style={{ animationDelay: '0.2s' }}
          >
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none" />
            <input
              type="text"
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setActiveCategory('All');
                setOpenIndex(null);
              }}
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-electric-blue/30 focus:border-electric-blue transition-all text-sm"
            />
          </div>
        </div>
      </section>

      {/* Category tabs */}
      <section className="pb-4 sticky top-0 z-10 bg-surface-primary/95 backdrop-blur-sm border-b border-[hsl(var(--border))]/40">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => {
                  setActiveCategory(cat);
                  setSearchQuery('');
                  setOpenIndex(null);
                }}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  activeCategory === cat
                    ? 'bg-electric-blue text-white shadow-sm'
                    : 'bg-surface-secondary text-text-secondary hover:text-text-primary hover:bg-surface-secondary/80'
                }`}
              >
                {cat}
                {cat !== 'All' && (
                  <span className="ml-1.5 text-xs opacity-70">
                    {ALL_FAQS.filter((f) => f.category === cat).length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ list */}
      <section className="py-10 sm:py-16">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="max-w-3xl mx-auto">
            {filtered.length === 0 ? (
              <div className="text-center py-16">
                <MessageSquare className="w-10 h-10 text-text-tertiary mx-auto mb-4" />
                <p className="text-text-secondary text-lg mb-2">No results found</p>
                <p className="text-text-tertiary text-sm">
                  Try a different search term or browse all categories.
                </p>
                <button
                  onClick={() => { setSearchQuery(''); setActiveCategory('All'); }}
                  className="btn-secondary mt-4 text-sm"
                >
                  Clear search
                </button>
              </div>
            ) : (
              <>
                {/* Group by category when browsing all */}
                {activeCategory === 'All' && !searchQuery ? (
                  CATEGORIES.filter((c) => c !== 'All').map((cat) => {
                    const catFaqs = filtered.filter((f) => f.category === cat);
                    if (!catFaqs.length) return null;
                    const catStartIndex = filtered.findIndex((f) => f.category === cat);
                    return (
                      <div key={cat} className="mb-10">
                        <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                          <span className="w-1 h-5 rounded-full bg-electric-blue inline-block" />
                          {cat}
                        </h2>
                        <div className="space-y-3">
                          {catFaqs.map((faq, localIdx) => {
                            const globalIdx = catStartIndex + localIdx;
                            return (
                              <FAQAccordion
                                key={globalIdx}
                                faq={faq}
                                isOpen={openIndex === globalIdx}
                                onToggle={() => toggle(globalIdx)}
                              />
                            );
                          })}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="space-y-3">
                    {filtered.map((faq, idx) => (
                      <FAQAccordion
                        key={idx}
                        faq={faq}
                        isOpen={openIndex === idx}
                        onToggle={() => toggle(idx)}
                        showCategory
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </section>

      {/* Still have questions CTA */}
      <section className="py-12 sm:py-16 border-t border-[hsl(var(--border))]/40">
        <div className="container mx-auto px-4 sm:px-6">
          <Card className="max-w-2xl mx-auto p-8 text-center">
            <div className="w-12 h-12 rounded-full bg-electric-blue/10 flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-6 h-6 text-electric-blue" />
            </div>
            <h3 className="text-xl font-bold text-text-primary mb-2">Still have questions?</h3>
            <p className="text-text-secondary mb-6 text-sm">
              Our support team typically responds within 2 hours on weekdays.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href="mailto:hello@codeswiftr.com"
                className="btn-primary inline-flex items-center justify-center gap-2"
              >
                Email Support
                <ArrowRight className="w-4 h-4" />
              </a>
              <Link
                to="/pricing"
                className="btn-secondary inline-flex items-center justify-center gap-2"
              >
                <Crown className="w-4 h-4" />
                View Pricing
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}

interface FAQAccordionProps {
  faq: FAQItem;
  isOpen: boolean;
  onToggle: () => void;
  showCategory?: boolean;
}

function FAQAccordion({ faq, isOpen, onToggle, showCategory }: FAQAccordionProps) {
  return (
    <Card className="overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-5 flex items-start justify-between text-left hover:bg-surface-secondary/50 transition-colors gap-4"
        aria-expanded={isOpen}
      >
        <div className="flex-1 min-w-0">
          {showCategory && (
            <span className="text-xs text-text-tertiary font-medium mb-1 block">{faq.category}</span>
          )}
          <span className="font-medium text-text-primary">{faq.question}</span>
        </div>
        <ChevronDown
          className={`w-5 h-5 text-text-tertiary flex-shrink-0 mt-0.5 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>
      {isOpen && (
        <div className="px-5 pb-5 text-text-secondary text-sm leading-relaxed animate-slide-up border-t border-[hsl(var(--border))]/40 pt-4">
          {faq.answer}
        </div>
      )}
    </Card>
  );
}
