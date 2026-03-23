import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft } from 'lucide-react';

const blogModules = import.meta.glob('/content/blog/*.md', {
  query: '?raw',
  import: 'default',
  eager: true
}) as Record<string, string>;

function extractTitle(content: string): string {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1] : 'Untitled';
}

function extractExcerpt(content: string): string {
  const lines = content.split('\n').filter(line => !line.startsWith('#') && line.trim());
  const text = lines.slice(0, 3).join(' ').replace(/\*\*/g, '').replace(/\*/g, '');
  return text.length > 160 ? text.slice(0, 160) + '...' : text;
}

export function BlogPost() {
  const { slug } = useParams<{ slug: string }>();

  const path = Object.keys(blogModules).find(p => p.includes(`/${slug}.md`));
  const content = path ? (blogModules[path] as string) : null;

  if (!content) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12 text-center">
        <title>Post Not Found | Interview Insights - CareerSwiftr</title>
        <h1 className="text-2xl font-bold text-text-primary mb-4">Post Not Found</h1>
        <Link to="/blog" className="text-electric-blue hover:underline">
          ← Back to Blog
        </Link>
      </div>
    );
  }

  const title = extractTitle(content);
  const excerpt = extractExcerpt(content);
  const pageTitle = `${title} | Interview Insights - CareerSwiftr`;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <title>{pageTitle}</title>
      <meta name="description" content={excerpt} />
      <meta property="og:title" content={pageTitle} />
      <meta property="og:description" content={excerpt} />
      <meta property="og:type" content="article" />

      <Link
        to="/blog"
        className="inline-flex items-center gap-2 text-electric-blue hover:underline mb-8"
      >
        <ArrowLeft size={16} /> Back to Blog
      </Link>
      <article className="prose prose-invert prose-lg max-w-none prose-headings:text-text-primary prose-p:text-text-secondary prose-a:text-electric-blue prose-strong:text-text-primary prose-blockquote:border-electric-blue prose-blockquote:text-text-secondary">
        <ReactMarkdown>{content}</ReactMarkdown>
      </article>
    </div>
  );
}

export default BlogPost;
