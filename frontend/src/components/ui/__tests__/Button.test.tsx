import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../Button';
import { CheckCircle, ArrowRight } from 'lucide-react';

describe('Button', () => {
  describe('Variants', () => {
    it('renders primary variant by default', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('btn-primary');
    });

    it('renders secondary variant', () => {
      render(<Button variant="secondary">Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('btn-secondary');
    });

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('btn-ghost');
    });

    it('renders danger variant', () => {
      render(<Button variant="danger">Delete</Button>);
      const button = screen.getByRole('button', { name: /delete/i });
      expect(button).toHaveClass('bg-status-error');
    });
  });

  describe('Sizes', () => {
    it('renders medium size by default', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('px-6', 'py-3');
    });

    it('renders small size', () => {
      render(<Button size="sm">Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('px-3', 'py-1.5', 'text-sm');
    });

    it('renders large size', () => {
      render(<Button size="lg">Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('px-8', 'py-4', 'text-lg');
    });
  });

  describe('Icons', () => {
    it('renders left icon', () => {
      render(
        <Button leftIcon={<CheckCircle data-testid="left-icon" />}>
          Submit
        </Button>
      );
      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
    });

    it('renders right icon', () => {
      render(
        <Button rightIcon={<ArrowRight data-testid="right-icon" />}>
          Next
        </Button>
      );
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    });

    it('renders both icons', () => {
      render(
        <Button
          leftIcon={<CheckCircle data-testid="left-icon" />}
          rightIcon={<ArrowRight data-testid="right-icon" />}
        >
          Continue
        </Button>
      );
      expect(screen.getByTestId('left-icon')).toBeInTheDocument();
      expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    });
  });

  describe('Loading state', () => {
    it('shows spinner when loading', () => {
      render(<Button loading>Loading</Button>);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('hides icons when loading', () => {
      render(
        <Button loading leftIcon={<CheckCircle data-testid="icon" />}>
          Submit
        </Button>
      );
      expect(screen.queryByTestId('icon')).not.toBeInTheDocument();
    });

    it('disables button when loading', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button', { name: /loading/i });
      expect(button).toBeDisabled();
    });
  });

  describe('Disabled state', () => {
    it('disables button when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button', { name: /disabled/i });
      expect(button).toBeDisabled();
    });

    it('applies disabled styles', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button', { name: /disabled/i });
      expect(button).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
    });
  });

  describe('Full width', () => {
    it('applies full width class', () => {
      render(<Button fullWidth>Full Width</Button>);
      const button = screen.getByRole('button', { name: /full width/i });
      expect(button).toHaveClass('w-full');
    });
  });

  describe('Interaction', () => {
    it('calls onClick handler when clicked', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(<Button onClick={handleClick}>Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });

      await user.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      );
      const button = screen.getByRole('button', { name: /disabled/i });

      await user.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not call onClick when loading', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(
        <Button loading onClick={handleClick}>
          Loading
        </Button>
      );
      const button = screen.getByRole('button', { name: /loading/i });

      await user.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper button role', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('supports custom aria attributes', () => {
      render(<Button aria-label="Custom label">Click me</Button>);
      expect(screen.getByLabelText('Custom label')).toBeInTheDocument();
    });

    it('is keyboard accessible', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();

      render(<Button onClick={handleClick}>Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });

      button.focus();
      expect(button).toHaveFocus();

      await user.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Custom className', () => {
    it('merges custom className with default classes', () => {
      render(<Button className="custom-class">Click me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toHaveClass('custom-class');
      expect(button).toHaveClass('btn-primary'); // default variant
    });
  });
});
