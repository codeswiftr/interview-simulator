import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';

describe('Test Setup Verification', () => {
  it('should render a button correctly', () => {
    render(<button>Click me</button>);
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  it('should handle button clicks', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<button onClick={handleClick}>Click me</button>);

    const button = screen.getByRole('button');
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should render disabled button', () => {
    render(<button disabled>Disabled</button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
