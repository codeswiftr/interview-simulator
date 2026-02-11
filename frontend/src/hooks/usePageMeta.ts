/**
 * usePageMeta - Update document title and meta description for SEO
 *
 * Use in page components to set page-specific meta tags.
 * Restores previous values on unmount.
 */
import { useEffect } from 'react';

interface PageMeta {
  title: string;
  description?: string;
  ogTitle?: string;
  ogDescription?: string;
}

export function usePageMeta({ title, description, ogTitle, ogDescription }: PageMeta): void {
  useEffect(() => {
    const prevTitle = document.title;
    const prevDesc = document.querySelector('meta[name="description"]')?.getAttribute('content');
    const prevOgTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content');
    const prevOgDesc = document.querySelector('meta[property="og:description"]')?.getAttribute('content');

    document.title = title;
    if (description) {
      const metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc) metaDesc.setAttribute('content', description);
    }
    if (ogTitle) {
      const metaOgTitle = document.querySelector('meta[property="og:title"]');
      if (metaOgTitle) metaOgTitle.setAttribute('content', ogTitle);
    }
    if (ogDescription) {
      const metaOgDesc = document.querySelector('meta[property="og:description"]');
      if (metaOgDesc) metaOgDesc.setAttribute('content', ogDescription);
    }

    return () => {
      document.title = prevTitle;
      if (description && prevDesc) {
        const metaDesc = document.querySelector('meta[name="description"]');
        if (metaDesc) metaDesc.setAttribute('content', prevDesc);
      }
      if (ogTitle && prevOgTitle) {
        const metaOgTitle = document.querySelector('meta[property="og:title"]');
        if (metaOgTitle) metaOgTitle.setAttribute('content', prevOgTitle);
      }
      if (ogDescription && prevOgDesc) {
        const metaOgDesc = document.querySelector('meta[property="og:description"]');
        if (metaOgDesc) metaOgDesc.setAttribute('content', prevOgDesc);
      }
    };
  }, [title, description, ogTitle, ogDescription]);
}
