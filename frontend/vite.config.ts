import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import fs from 'node:fs'
import path from 'node:path'

const SITE_URL = 'https://app.codeswiftr.com'

// Static public pages (not behind auth)
const STATIC_PAGES = ['/', '/pricing', '/blog', '/affiliates', '/content', '/login', '/register']

function sitemapPlugin(): Plugin {
  return {
    name: 'sitemap-generator',
    closeBundle() {
      // process.cwd() is the project root (frontend/) in Vite's build context
      const root = process.cwd()
      const blogDir = path.join(root, 'content/blog')
      const slugs = fs.existsSync(blogDir)
        ? fs.readdirSync(blogDir).filter(f => f.endsWith('.md')).map(f => f.replace('.md', ''))
        : []

      const urls = [
        ...STATIC_PAGES.map(p => `${SITE_URL}${p}`),
        ...slugs.map(s => `${SITE_URL}/blog/${s}`),
      ]

      const xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ...urls.map(url => `  <url><loc>${url}</loc></url>`),
        '</urlset>',
      ].join('\n')

      const outDir = path.join(root, 'dist')
      if (fs.existsSync(outDir)) {
        fs.writeFileSync(path.join(outDir, 'sitemap.xml'), xml)
      }
    },
  }
}

// https://vite.dev/config/
// Port 5173 - Interview Simulator (primary CodeSwiftr frontend)
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Core React vendor bundle
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router-dom/') ||
              id.includes('node_modules/react-router/') ||
              id.includes('node_modules/@remix-run/')) {
            return 'react-vendor';
          }
          // Chart library (lazy loaded with DashboardPage)
          if (id.includes('node_modules/recharts/') ||
              id.includes('node_modules/d3-')) {
            return 'recharts';
          }
          // HTTP client
          if (id.includes('node_modules/axios/')) {
            return 'axios';
          }
          // React Query
          if (id.includes('node_modules/@tanstack/')) {
            return 'query';
          }
          // UI components and utilities
          if (id.includes('node_modules/lucide-react/') ||
              id.includes('node_modules/clsx/') ||
              id.includes('node_modules/tailwind-merge/')) {
            return 'ui-vendor';
          }
          // Error tracking
          if (id.includes('node_modules/@sentry/')) {
            return 'sentry';
          }
          // Analytics
          if (id.includes('node_modules/posthog-js/')) {
            return 'analytics';
          }
        },
      },
    },
    // Increase warning limit for larger chunks during development
    chunkSizeWarningLimit: 600,
  },
  plugins: [
    react(),
    sitemapPlugin(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'images/*.png'],
      manifest: {
        name: 'Interview Simulator - CareerSwiftr',
        short_name: 'Interview Prep',
        description: 'AI-powered interview practice for software engineers',
        theme_color: '#1a1a1a',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait-primary',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/images/logo-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: '/images/logo-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 12 * 1024 * 1024, // 12MB — blog chunks can exceed default 2MB
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/interview-simulator-api.*\/api\/v1\/.*/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 3600,
              },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 604800,
              },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'font-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 2592000,
              },
            },
          },
        ],
        navigateFallback: '/offline.html',
        navigateFallbackDenylist: [/^\/api/],
      },
    }),
  ],
  server: {
    port: 5173,
    host: 'localhost',
    // Allow local development domains via Caddy proxy
    allowedHosts: [
      'localhost',
      'app.codeswiftr.local',
      'codeswiftr.local',
      '.local', // Allow all .local domains
    ],
  },
})
