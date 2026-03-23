import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
}

// Use Vite's glob import
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
  // Skip title and get first paragraph
  const lines = content.split('\n').filter(line => !line.startsWith('#') && line.trim());
  const text = lines.slice(0, 3).join(' ').replace(/\*\*/g, '').replace(/\*/g, '');
  return text.length > 200 ? text.slice(0, 200) + '...' : text;
}

export function BlogList() {
  const posts: BlogPost[] = Object.entries(blogModules).map(([path, content]) => {
    const slug = path.split('/').pop()?.replace('.md', '') || '';
    return {
      slug,
      title: extractTitle(content as string),
      excerpt: extractExcerpt(content as string),
    };
  }).sort((a, b) => a.title.localeCompare(b.title));

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <title>Interview Insights Blog | CareerSwiftr</title>
      <meta name="description" content="Expert tips, strategies, and insights for software engineers preparing for behavioral, technical, and system design interviews." />
      <meta property="og:title" content="Interview Insights Blog | CareerSwiftr" />
      <meta property="og:description" content="Expert tips, strategies, and insights for software engineers preparing for behavioral, technical, and system design interviews." />

      <h1 className="text-3xl font-bold text-text-primary mb-8">Interview Insights Blog</h1>
      <div className="space-y-6">
        {posts.map((post) => (
          <Link
            key={post.slug}
            to={`/blog/${post.slug}`}
            className="block p-6 bg-surface-secondary rounded-xl hover:bg-surface-tertiary transition-colors border border-border-default"
          >
            <h2 className="text-xl font-semibold text-text-primary mb-2 group-hover:text-electric-blue">
              {post.title}
            </h2>
            <p className="text-text-secondary mb-4">{post.excerpt}</p>
            <span className="text-electric-blue flex items-center gap-2 text-sm font-medium">
              Read more <ArrowRight size={16} />
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default BlogList;
