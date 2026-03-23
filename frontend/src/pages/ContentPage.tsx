import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Share2, Mail, Download, Video, ArrowRight, Zap } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { usePageMeta } from '../hooks/usePageMeta';

const CONTENT_CATEGORIES = [
  {
    id: 'blog',
    title: 'Blog Posts',
    description: 'STAR method, behavioral questions, salary negotiation, and FAANG prep guides.',
    count: 10,
    href: '/blog',
    icon: FileText,
    cta: 'Browse Articles',
  },
  {
    id: 'social',
    title: 'Social Media',
    description: 'LinkedIn and Twitter tips for interview preparation.',
    count: 15,
    href: '/blog',
    icon: Share2,
    cta: 'View Tips',
  },
  {
    id: 'email',
    title: 'Email Sequences',
    description: 'User onboarding and Pro upsell nurture flows.',
    count: 8,
    href: '/register',
    icon: Mail,
    cta: 'Get Started',
  },
  {
    id: 'downloads',
    title: 'Downloadable Resources',
    description: 'Cheatsheets, templates, and question banks.',
    count: 5,
    href: '/register?plan=pro',
    icon: Download,
    cta: 'Get Free Resources',
  },
  {
    id: 'video',
    title: 'Video Scripts',
    description: 'YouTube Shorts on STAR method, salary negotiation, and more.',
    count: 5,
    href: '/blog',
    icon: Video,
    cta: 'Watch Tips',
  },
];

const PAGE_TITLE = 'Interview Prep Content Library | CareerSwiftr Interview Simulator';
const PAGE_DESC =
  'Free interview preparation content: blog posts, social tips, email guides, downloadable cheatsheets, and video scripts. STAR method, behavioral questions, salary negotiation.';

export default function ContentPage() {
  usePageMeta({
    title: PAGE_TITLE,
    description: PAGE_DESC,
    ogTitle: PAGE_TITLE,
    ogDescription: PAGE_DESC,
  });

  // JSON-LD structured data for search engines
  useEffect(() => {
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'CollectionPage',
      name: 'Interview Prep Content Library',
      description: PAGE_DESC,
      url: typeof window !== 'undefined' ? `${window.location.origin}/content` : 'https://app.codeswiftr.com/content',
      provider: {
        '@type': 'Organization',
        name: 'CareerSwiftr',
        url: 'https://app.codeswiftr.com',
      },
      mainEntity: {
        '@type': 'ItemList',
        numberOfItems: 50,
        itemListElement: CONTENT_CATEGORIES.map((cat, i) => ({
          '@type': 'ListItem',
          position: i + 1,
          name: cat.title,
          description: cat.description,
        })),
      },
    });
    document.head.appendChild(script);
    return () => script.remove();
  }, []);

  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Hero */}
      <section className="relative pt-16 sm:pt-20 pb-12 sm:pb-16 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] rounded-full bg-electric-blue/15 dark:bg-electric-blue/10 blur-[80px]" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[#FF6B9D]/10 dark:bg-[#FF6B9D]/5 blur-[100px]" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 text-text-primary">
            Interview Prep Content Library
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-8">
            Free resources to help you ace your next interview: blog posts, social tips, email guides,
            cheatsheets, and video scripts. All focused on STAR method, behavioral questions, and
            salary negotiation.
          </p>
          <Link
            to="/register"
            className="btn-primary inline-flex items-center justify-center gap-2"
          >
            <Zap className="w-5 h-5" />
            Start Practicing Free
          </Link>
        </div>
      </section>

      {/* Content Categories */}
      <section className="pb-16 sm:pb-24">
        <div className="container mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-text-primary mb-8 text-center">
            Browse by Category
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {CONTENT_CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <Card key={cat.id} className="p-6 border-2 border-border-light hover:border-electric-blue/30 transition-colors">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="p-2 rounded-lg bg-electric-blue/10">
                      <Icon className="w-6 h-6 text-electric-blue" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-text-primary">{cat.title}</h3>
                      <span className="text-sm text-text-tertiary">{cat.count} pieces</span>
                    </div>
                  </div>
                  <p className="text-text-secondary text-sm mb-4">{cat.description}</p>
                  <Link
                    to={cat.href}
                    className="text-electric-blue flex items-center gap-2 text-sm font-medium hover:underline"
                  >
                    {cat.cta}
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Lead Magnet CTA */}
      <section className="py-16 bg-surface-secondary border-y border-border-light">
        <div className="container mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl font-bold text-text-primary mb-4">
            Get 50 Behavioral Interview Questions (Free)
          </h2>
          <p className="text-text-secondary mb-6 max-w-xl mx-auto">
            Download our cheatsheet with example answers. Perfect for preparing your STAR stories.
          </p>
          <Link
            to="/register?plan=pro"
            className="btn-primary inline-flex items-center justify-center gap-2"
          >
            <Download className="w-5 h-5" />
            Download Free Resource
          </Link>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl font-bold text-text-primary mb-4">
            Practice With AI Feedback
          </h2>
          <p className="text-text-secondary mb-6 max-w-xl mx-auto">
            Content helps you prepare. Practice with Interview Simulator to get real-time feedback
            before your interview.
          </p>
          <Link to="/register" className="btn-primary">
            Start Free Trial
          </Link>
        </div>
      </section>
    </div>
  );
}
