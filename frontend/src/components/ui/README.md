# UI Component Library

A comprehensive set of reusable UI components for the interview simulator frontend, built with React, TypeScript, and Tailwind CSS.

## Components

### Button

A versatile button component with multiple variants, sizes, and states.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'primary' \| 'secondary' \| 'ghost' \| 'danger'` | `'primary'` | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Button size |
| `loading` | `boolean` | `false` | Shows spinner and disables button |
| `leftIcon` | `ReactNode` | - | Icon to display on the left |
| `rightIcon` | `ReactNode` | - | Icon to display on the right |
| `fullWidth` | `boolean` | `false` | Makes button full width |
| `disabled` | `boolean` | `false` | Disables the button |
| `className` | `string` | - | Additional CSS classes |

#### Examples

```tsx
import { Button } from '@/components/ui';
import { CheckCircle, ArrowRight } from 'lucide-react';

// Primary button
<Button onClick={handleSubmit}>
  Submit
</Button>

// Secondary button with icon
<Button variant="secondary" leftIcon={<CheckCircle />}>
  Save Draft
</Button>

// Loading state
<Button loading>
  Processing...
</Button>

// Danger variant
<Button variant="danger" onClick={handleDelete}>
  Delete Interview
</Button>

// Ghost button with right icon
<Button variant="ghost" rightIcon={<ArrowRight />}>
  Next
</Button>

// Full width button
<Button fullWidth size="lg">
  Start Interview
</Button>
```

### Spinner

A loading indicator component with configurable size and optional label.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Spinner size |
| `label` | `string` | - | Optional text label |
| `className` | `string` | - | Additional CSS classes |

#### Examples

```tsx
import { Spinner } from '@/components/ui';

// Default spinner
<Spinner />

// Small spinner
<Spinner size="sm" />

// Spinner with label
<Spinner label="Loading interviews..." />

// Custom styled spinner
<Spinner size="lg" className="text-electric-blue" />
```

### Modal

A fully accessible modal dialog with focus trap, backdrop blur, and keyboard support.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `isOpen` | `boolean` | - | Controls modal visibility |
| `onClose` | `() => void` | - | Callback when modal should close |
| `title` | `string` | - | Modal title |
| `children` | `ReactNode` | - | Modal content |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Modal width |
| `closeOnBackdrop` | `boolean` | `true` | Close when clicking backdrop |
| `closeOnEscape` | `boolean` | `true` | Close when pressing Escape |
| `showCloseButton` | `boolean` | `true` | Show close button |
| `className` | `string` | - | Additional CSS classes |

#### Features

- **Focus Trap**: Keeps keyboard focus inside modal when open
- **Backdrop Blur**: Beautiful blurred background effect
- **Keyboard Support**: Close with Escape key (configurable)
- **Accessibility**: Proper ARIA attributes and screen reader support
- **Animated**: Smooth entrance and exit animations
- **Portal**: Renders in document.body to avoid z-index issues

#### Examples

```tsx
import { Modal, Button } from '@/components/ui';
import { useState } from 'react';

function InterviewModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>
        Create Interview
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="New Interview"
        size="lg"
      >
        <div className="space-y-4">
          <p>Configure your interview settings...</p>

          <div className="flex gap-3 justify-end">
            <Button variant="ghost" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate}>
              Create
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}

// Modal without close button
<Modal
  isOpen={isOpen}
  onClose={onClose}
  showCloseButton={false}
  closeOnBackdrop={false}
>
  <p>This modal requires explicit user action</p>
  <Button onClick={onClose}>Acknowledge</Button>
</Modal>
```

### Card

A flexible container component with Shadcn-style slots for consistent layouts.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'glass' \| 'interactive' \| 'elevated' \| 'outline'` | `'default'` | Visual style variant |
| `className` | `string` | - | Additional CSS classes |

#### Slot Components

- **Card**: Base container with rounded corners and transitions
- **CardHeader**: Header section with vertical spacing (p-6)
- **CardTitle**: h3 heading with proper typography
- **CardDescription**: Muted text description
- **CardContent**: Main content area (p-6 pt-0)
- **CardFooter**: Footer with flex alignment (p-6 pt-0)

#### Variants

| Variant | Description |
|---------|-------------|
| `default` | White/dark background with border and shadow |
| `glass` | Glassmorphism effect with backdrop blur |
| `interactive` | Hover effects for clickable cards |
| `elevated` | Stronger shadow for emphasis |
| `outline` | Transparent with border only |

#### Examples

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui';
import { Button } from '@/components/ui';

// Simple card
<Card className="p-6">
  <h3>Simple Card</h3>
  <p>Basic content without slots</p>
</Card>

// Full slot composition
<Card>
  <CardHeader>
    <CardTitle>Interview Practice</CardTitle>
    <CardDescription>Complete your daily practice</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Your content here...</p>
  </CardContent>
  <CardFooter>
    <Button>Start Practice</Button>
  </CardFooter>
</Card>

// Interactive card
<Card variant="interactive" className="cursor-pointer">
  <CardContent>
    <p>Click me for more details</p>
  </CardContent>
</Card>

// Glass effect (for overlays)
<Card variant="glass" className="p-6">
  <p>Translucent glassmorphism card</p>
</Card>
```

### Toast

Toast notification system for displaying temporary messages (already exists, included for completeness).

#### Examples

```tsx
import { Toast, ToastContainer } from '@/components/ui';

// See Toast.tsx for full implementation
```

## Design Tokens

All components use design tokens from `globals.css`:

### Colors
- `--color-electric-blue`: Primary brand color
- `--color-charcoal`: Dark text color
- `--color-clean-white`: Light background
- `--color-status-success`: Success green
- `--color-status-error`: Error red
- `--color-status-warning`: Warning orange
- `--color-status-info`: Info blue

### Typography
- `--font-family-heading`: Outfit (headings)
- `--font-family-body`: Inter (body text)
- `--font-family-mono`: JetBrains Mono (code)

### Shadows
- `--shadow-blue-glow`: Blue glow effect
- `--shadow-success-glow`: Success glow effect
- `--shadow-glass`: Glass morphism effect

## Accessibility

All components follow WCAG 2.1 AA guidelines:

- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Visible focus indicators
- **ARIA Attributes**: Proper semantic markup
- **Screen Readers**: Descriptive labels and roles
- **Color Contrast**: Meets minimum contrast ratios
- **Reduced Motion**: Respects `prefers-reduced-motion`

## Testing

Components are tested with Vitest and React Testing Library:

```bash
# Run all UI component tests
npm test -- src/components/ui

# Run with coverage
npm run test:coverage -- src/components/ui

# Run in watch mode
npm test -- src/components/ui
```

## Dark Mode

All components automatically adapt to dark mode via CSS custom properties:

```tsx
// No special handling needed - works automatically
<Button>Works in light and dark mode</Button>
```

## Best Practices

1. **Always use semantic HTML**: Components render proper semantic elements
2. **Provide accessible labels**: Use `aria-label` when button text isn't descriptive
3. **Handle loading states**: Use `loading` prop instead of disabling manually
4. **Compose components**: Build complex UIs by combining simple components
5. **Use design tokens**: Leverage existing CSS classes for consistency

## Examples

### Complete Form Example

```tsx
import { Button, Modal, Spinner } from '@/components/ui';
import { useState } from 'react';
import { Save, X } from 'lucide-react';

function InterviewForm() {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await saveInterview();
      setIsOpen(false);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)} leftIcon={<Save />}>
        New Interview
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Create Interview"
        size="lg"
      >
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <div className="space-y-4">
            {/* Form fields here */}

            <div className="flex gap-3 justify-end mt-6">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsOpen(false)}
                leftIcon={<X />}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={loading}
                leftIcon={<Save />}
              >
                Create Interview
              </Button>
            </div>
          </div>
        </form>
      </Modal>
    </>
  );
}
```

### Loading State Example

```tsx
import { Spinner } from '@/components/ui';

function InterviewList({ interviews, loading }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" label="Loading interviews..." />
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {interviews.map(interview => (
        <InterviewCard key={interview.id} {...interview} />
      ))}
    </div>
  );
}
```
