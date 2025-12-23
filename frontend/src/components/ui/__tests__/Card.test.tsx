import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { createRef } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../Card';

describe('Card', () => {
  describe('Default rendering', () => {
    it('renders card with children', () => {
      render(<Card>Card content</Card>);
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('applies default variant classes', () => {
      const { container } = render(<Card>Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('rounded-xl', 'transition-all', 'duration-300');
      expect(card).toHaveClass('bg-white', 'border', 'shadow-sm');
    });
  });

  describe('Variants', () => {
    it('renders default variant', () => {
      const { container } = render(<Card variant="default">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-white', 'border', 'shadow-sm');
    });

    it('renders glass variant', () => {
      const { container } = render(<Card variant="glass">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('card-glass');
    });

    it('renders interactive variant', () => {
      const { container } = render(<Card variant="interactive">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('card-interactive');
    });

    it('renders elevated variant', () => {
      const { container } = render(<Card variant="elevated">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-white', 'border', 'shadow-md');
    });

    it('renders outline variant', () => {
      const { container } = render(<Card variant="outline">Content</Card>);
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-transparent', 'border');
    });
  });

  describe('Slot composition', () => {
    it('renders CardHeader with children', () => {
      render(<CardHeader>Header content</CardHeader>);
      expect(screen.getByText('Header content')).toBeInTheDocument();
    });

    it('applies CardHeader classes', () => {
      const { container } = render(<CardHeader>Content</CardHeader>);
      const header = container.firstChild as HTMLElement;
      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6');
    });

    it('renders CardTitle with children', () => {
      render(<CardTitle>Title text</CardTitle>);
      expect(screen.getByText('Title text')).toBeInTheDocument();
    });

    it('renders CardTitle as h3 element', () => {
      render(<CardTitle>Title text</CardTitle>);
      const title = screen.getByText('Title text');
      expect(title.tagName).toBe('H3');
    });

    it('applies CardTitle classes', () => {
      render(<CardTitle>Title text</CardTitle>);
      const title = screen.getByText('Title text');
      expect(title).toHaveClass('font-semibold', 'tracking-tight', 'text-lg', 'text-text-primary');
    });

    it('renders CardDescription with children', () => {
      render(<CardDescription>Description text</CardDescription>);
      expect(screen.getByText('Description text')).toBeInTheDocument();
    });

    it('renders CardDescription as p element', () => {
      render(<CardDescription>Description text</CardDescription>);
      const description = screen.getByText('Description text');
      expect(description.tagName).toBe('P');
    });

    it('applies CardDescription classes', () => {
      render(<CardDescription>Description text</CardDescription>);
      const description = screen.getByText('Description text');
      expect(description).toHaveClass('text-sm', 'text-text-secondary');
    });

    it('renders CardContent with children', () => {
      render(<CardContent>Content text</CardContent>);
      expect(screen.getByText('Content text')).toBeInTheDocument();
    });

    it('applies CardContent classes', () => {
      const { container } = render(<CardContent>Content</CardContent>);
      const content = container.firstChild as HTMLElement;
      expect(content).toHaveClass('p-6', 'pt-0');
    });

    it('renders CardFooter with children', () => {
      render(<CardFooter>Footer content</CardFooter>);
      expect(screen.getByText('Footer content')).toBeInTheDocument();
    });

    it('applies CardFooter classes', () => {
      const { container } = render(<CardFooter>Footer</CardFooter>);
      const footer = container.firstChild as HTMLElement;
      expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0');
    });

    it('renders complete card with all slots', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
            <CardDescription>Card Description</CardDescription>
          </CardHeader>
          <CardContent>Card Content</CardContent>
          <CardFooter>Card Footer</CardFooter>
        </Card>
      );

      expect(screen.getByText('Card Title')).toBeInTheDocument();
      expect(screen.getByText('Card Description')).toBeInTheDocument();
      expect(screen.getByText('Card Content')).toBeInTheDocument();
      expect(screen.getByText('Card Footer')).toBeInTheDocument();
    });
  });

  describe('Ref forwarding', () => {
    it('forwards ref for Card', () => {
      const ref = createRef<HTMLDivElement>();
      render(<Card ref={ref}>Content</Card>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current?.textContent).toBe('Content');
    });

    it('forwards ref for CardHeader', () => {
      const ref = createRef<HTMLDivElement>();
      render(<CardHeader ref={ref}>Header</CardHeader>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current?.textContent).toBe('Header');
    });

    it('forwards ref for CardTitle', () => {
      const ref = createRef<HTMLHeadingElement>();
      render(<CardTitle ref={ref}>Title</CardTitle>);
      expect(ref.current).toBeInstanceOf(HTMLHeadingElement);
      expect(ref.current?.textContent).toBe('Title');
    });

    it('forwards ref for CardDescription', () => {
      const ref = createRef<HTMLParagraphElement>();
      render(<CardDescription ref={ref}>Description</CardDescription>);
      expect(ref.current).toBeInstanceOf(HTMLParagraphElement);
      expect(ref.current?.textContent).toBe('Description');
    });

    it('forwards ref for CardContent', () => {
      const ref = createRef<HTMLDivElement>();
      render(<CardContent ref={ref}>Content</CardContent>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current?.textContent).toBe('Content');
    });

    it('forwards ref for CardFooter', () => {
      const ref = createRef<HTMLDivElement>();
      render(<CardFooter ref={ref}>Footer</CardFooter>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
      expect(ref.current?.textContent).toBe('Footer');
    });
  });

  describe('Custom className', () => {
    it('merges custom className with Card default classes', () => {
      const { container } = render(
        <Card className="custom-class">Content</Card>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('custom-class');
      expect(card).toHaveClass('rounded-xl', 'transition-all');
    });

    it('merges custom className with CardHeader classes', () => {
      const { container } = render(
        <CardHeader className="custom-header">Header</CardHeader>
      );
      const header = container.firstChild as HTMLElement;
      expect(header).toHaveClass('custom-header');
      expect(header).toHaveClass('flex', 'flex-col', 'p-6');
    });

    it('merges custom className with CardTitle classes', () => {
      render(<CardTitle className="custom-title">Title</CardTitle>);
      const title = screen.getByText('Title');
      expect(title).toHaveClass('custom-title');
      expect(title).toHaveClass('font-semibold', 'text-lg');
    });

    it('merges custom className with CardDescription classes', () => {
      render(
        <CardDescription className="custom-desc">Description</CardDescription>
      );
      const description = screen.getByText('Description');
      expect(description).toHaveClass('custom-desc');
      expect(description).toHaveClass('text-sm', 'text-text-secondary');
    });

    it('merges custom className with CardContent classes', () => {
      const { container } = render(
        <CardContent className="custom-content">Content</CardContent>
      );
      const content = container.firstChild as HTMLElement;
      expect(content).toHaveClass('custom-content');
      expect(content).toHaveClass('p-6', 'pt-0');
    });

    it('merges custom className with CardFooter classes', () => {
      const { container } = render(
        <CardFooter className="custom-footer">Footer</CardFooter>
      );
      const footer = container.firstChild as HTMLElement;
      expect(footer).toHaveClass('custom-footer');
      expect(footer).toHaveClass('flex', 'items-center', 'p-6');
    });
  });

  describe('Children rendering', () => {
    it('renders text children in Card', () => {
      render(<Card>Simple text</Card>);
      expect(screen.getByText('Simple text')).toBeInTheDocument();
    });

    it('renders element children in Card', () => {
      render(
        <Card>
          <div data-testid="child-element">Element content</div>
        </Card>
      );
      expect(screen.getByTestId('child-element')).toBeInTheDocument();
      expect(screen.getByText('Element content')).toBeInTheDocument();
    });

    it('renders multiple children in Card', () => {
      render(
        <Card>
          <span>First child</span>
          <span>Second child</span>
        </Card>
      );
      expect(screen.getByText('First child')).toBeInTheDocument();
      expect(screen.getByText('Second child')).toBeInTheDocument();
    });

    it('renders complex nested structure', () => {
      render(
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>User Profile</CardTitle>
            <CardDescription>Manage your account settings</CardDescription>
          </CardHeader>
          <CardContent>
            <div data-testid="form">
              <input type="text" placeholder="Name" />
              <input type="email" placeholder="Email" />
            </div>
          </CardContent>
          <CardFooter>
            <button>Save Changes</button>
            <button>Cancel</button>
          </CardFooter>
        </Card>
      );

      expect(screen.getByText('User Profile')).toBeInTheDocument();
      expect(screen.getByText('Manage your account settings')).toBeInTheDocument();
      expect(screen.getByTestId('form')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
  });

  describe('HTML attributes', () => {
    it('spreads additional props to Card', () => {
      const { container } = render(
        <Card data-testid="test-card" role="region" aria-label="Test card">
          Content
        </Card>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('data-testid', 'test-card');
      expect(card).toHaveAttribute('role', 'region');
      expect(card).toHaveAttribute('aria-label', 'Test card');
    });

    it('spreads additional props to CardHeader', () => {
      const { container } = render(
        <CardHeader data-testid="test-header" id="header-id">
          Header
        </CardHeader>
      );
      const header = container.firstChild as HTMLElement;
      expect(header).toHaveAttribute('data-testid', 'test-header');
      expect(header).toHaveAttribute('id', 'header-id');
    });

    it('spreads additional props to CardTitle', () => {
      render(
        <CardTitle data-testid="test-title" id="title-id">
          Title
        </CardTitle>
      );
      const title = screen.getByText('Title');
      expect(title).toHaveAttribute('data-testid', 'test-title');
      expect(title).toHaveAttribute('id', 'title-id');
    });

    it('spreads additional props to CardDescription', () => {
      render(
        <CardDescription data-testid="test-desc" id="desc-id">
          Description
        </CardDescription>
      );
      const description = screen.getByText('Description');
      expect(description).toHaveAttribute('data-testid', 'test-desc');
      expect(description).toHaveAttribute('id', 'desc-id');
    });

    it('spreads additional props to CardContent', () => {
      const { container } = render(
        <CardContent data-testid="test-content" id="content-id">
          Content
        </CardContent>
      );
      const content = container.firstChild as HTMLElement;
      expect(content).toHaveAttribute('data-testid', 'test-content');
      expect(content).toHaveAttribute('id', 'content-id');
    });

    it('spreads additional props to CardFooter', () => {
      const { container } = render(
        <CardFooter data-testid="test-footer" id="footer-id">
          Footer
        </CardFooter>
      );
      const footer = container.firstChild as HTMLElement;
      expect(footer).toHaveAttribute('data-testid', 'test-footer');
      expect(footer).toHaveAttribute('id', 'footer-id');
    });
  });

  describe('Display names', () => {
    it('has correct display name for Card', () => {
      expect(Card.displayName).toBe('Card');
    });

    it('has correct display name for CardHeader', () => {
      expect(CardHeader.displayName).toBe('CardHeader');
    });

    it('has correct display name for CardTitle', () => {
      expect(CardTitle.displayName).toBe('CardTitle');
    });

    it('has correct display name for CardDescription', () => {
      expect(CardDescription.displayName).toBe('CardDescription');
    });

    it('has correct display name for CardContent', () => {
      expect(CardContent.displayName).toBe('CardContent');
    });

    it('has correct display name for CardFooter', () => {
      expect(CardFooter.displayName).toBe('CardFooter');
    });
  });
});
