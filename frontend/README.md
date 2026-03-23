# Interview Simulator - Frontend

Modern React TypeScript frontend for the AI-powered Interview Simulator, built with Vite, TailwindCSS v4, and React Router.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: TailwindCSS v4 (with PostCSS)
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **State Management**: React Context (useAuth)

## Design System

The frontend implements the CodeSwiftr Interview Simulator design system with:

- **Brand Colors**: Charcoal (#111827), Electric Blue (#38BDF8), Clean White (#F8FAFC)
- **Typography**: Outfit (headings), Inter (body), JetBrains Mono (code/scores)
- **Components**: Custom utility classes for buttons, cards, badges, inputs
- **Animations**: Fade-in, slide-up, scale-in, recording pulse

See `/docs/DESIGN_SYSTEM.md` for complete design specifications.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   ├── layout/          # Layout components (Header, ProtectedRoute)
│   │   └── interview/       # Interview-specific components
│   ├── pages/
│   │   ├── HomePage.tsx     # Landing page
│   │   ├── LoginPage.tsx    # Authentication
│   │   ├── RegisterPage.tsx # User registration
│   │   ├── DashboardPage.tsx    # User dashboard (placeholder)
│   │   └── InterviewPage.tsx    # Interview room (placeholder)
│   ├── lib/
│   │   ├── api.ts          # Axios instance and API methods
│   │   └── utils.ts        # Utility functions (cn, formatters)
│   ├── hooks/
│   │   └── useAuth.tsx     # Authentication context and hook
│   ├── types/
│   │   └── index.ts        # TypeScript type definitions
│   └── styles/
│       └── globals.css     # Global styles and design tokens
├── public/                 # Static assets
└── index.html             # HTML entry point
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Available Scripts

- `npm run dev` - Start development server (http://localhost:5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## API Integration

The frontend connects to the backend API at `http://localhost:8000/api/v1` (configurable in `/src/lib/api.ts`).

### API Client Features

- **Automatic JWT token management** via localStorage
- **Request interceptor** for adding auth headers
- **Response interceptor** for handling 401 errors
- **Organized API methods** for auth, interviews, questions, responses, feedback

### Authentication Flow

1. User logs in/registers via `/login` or `/register`
2. JWT token is stored in localStorage
3. Token is automatically included in subsequent requests
4. Invalid token triggers redirect to login

## Routes

- `/` - Landing page (public)
- `/login` - Login page (public)
- `/register` - Registration page (public)
- `/dashboard` - User dashboard (protected)
- `/interview/:id` - Interview session (protected)

## State Management

### Authentication

Uses React Context (`useAuth` hook) for global auth state:

```tsx
const { user, isAuthenticated, login, register, logout } = useAuth();
```

### Protected Routes

Routes requiring authentication are wrapped with `<ProtectedRoute>`:

```tsx
<Route path="/dashboard" element={
  <ProtectedRoute>
    <DashboardPage />
  </ProtectedRoute>
} />
```

## Styling

### TailwindCSS v4

The project uses TailwindCSS v4 with the new `@theme` directive for design tokens:

```css
@theme {
  --color-electric-blue: #38BDF8;
  --font-family-heading: "Outfit", system-ui, sans-serif;
}
```

### Custom Utility Classes

Pre-built utility classes from the design system:

```tsx
// Typography
<h1 className="heading-hero">...</h1>
<p className="body-large">...</p>

// Buttons
<button className="btn-primary">...</button>

// Cards
<div className="card">...</div>
<div className="card-interactive">...</div>

// Badges
<span className="badge badge-in-progress">...</span>
```

## Type Safety

Full TypeScript coverage with type definitions for:

- User and authentication
- Questions and categories
- Interview sessions
- Responses and feedback
- API requests and errors

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development Guidelines

1. **Use TypeScript** - All new files should be `.ts` or `.tsx`
2. **Follow the design system** - Use predefined colors, typography, and components
3. **Type imports properly** - Use `import type` for type-only imports
4. **Accessibility** - Follow WCAG guidelines, use semantic HTML
5. **Performance** - Lazy load routes, optimize images, minimize bundle size

## Next Steps

- Add shadcn/ui components for forms and modals
- Implement Dashboard with interview history
- Build Interview Room interface with audio recording
- Add Feedback visualization components
- Set up E2E testing with Playwright

## Environment Variables

Create a `.env` file for configuration:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Access in code:
```ts
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

## Troubleshooting

### Build Errors

- Ensure all type imports use `import type` syntax
- Check that Tailwind v4 syntax is used (@import "tailwindcss")
- Verify PostCSS is configured with @tailwindcss/postcss

### Development Server Issues

- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## License

Proprietary - CodeSwiftr Interview Simulator
