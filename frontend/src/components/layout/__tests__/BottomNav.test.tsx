import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { BottomNav } from '../BottomNav';

// Mock useAuth hook
const mockUseAuth = vi.fn();
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

describe('BottomNav', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('when user is not authenticated', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ isAuthenticated: false });
    });

    it('should not render when user is not authenticated', () => {
      render(
        <MemoryRouter>
          <BottomNav />
        </MemoryRouter>
      );

      expect(screen.queryByRole('navigation', { name: /mobile navigation/i })).not.toBeInTheDocument();
    });
  });

  describe('when user is authenticated', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({ isAuthenticated: true });
    });

    it('should render navigation when user is authenticated', () => {
      render(
        <MemoryRouter>
          <BottomNav />
        </MemoryRouter>
      );

      expect(screen.getByRole('navigation', { name: /mobile navigation/i })).toBeInTheDocument();
    });

    it('should render all four navigation items', () => {
      render(
        <MemoryRouter>
          <BottomNav />
        </MemoryRouter>
      );

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Practice')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('should have correct links', () => {
      render(
        <MemoryRouter>
          <BottomNav />
        </MemoryRouter>
      );

      const homeLink = screen.getByText('Home').closest('a');
      const practiceLink = screen.getByText('Practice').closest('a');
      const analyticsLink = screen.getByText('Analytics').closest('a');
      const settingsLink = screen.getByText('Settings').closest('a');

      expect(homeLink).toHaveAttribute('href', '/dashboard');
      expect(practiceLink).toHaveAttribute('href', '/practice');
      expect(analyticsLink).toHaveAttribute('href', '/analytics');
      expect(settingsLink).toHaveAttribute('href', '/settings');
    });

    it('should highlight active link based on current route', () => {
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route path="*" element={<BottomNav />} />
          </Routes>
        </MemoryRouter>
      );

      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toHaveClass('text-electric-blue');
    });

    it('should highlight practice link when on /practice route', () => {
      render(
        <MemoryRouter initialEntries={['/practice']}>
          <Routes>
            <Route path="*" element={<BottomNav />} />
          </Routes>
        </MemoryRouter>
      );

      const practiceLink = screen.getByText('Practice').closest('a');
      expect(practiceLink).toHaveClass('text-electric-blue');
    });

    it('should highlight analytics link when on /analytics route', () => {
      render(
        <MemoryRouter initialEntries={['/analytics']}>
          <Routes>
            <Route path="*" element={<BottomNav />} />
          </Routes>
        </MemoryRouter>
      );

      const analyticsLink = screen.getByText('Analytics').closest('a');
      expect(analyticsLink).toHaveClass('text-electric-blue');
    });

    it('should have aria-hidden on icons', () => {
      render(
        <MemoryRouter>
          <BottomNav />
        </MemoryRouter>
      );

      // Each nav item should have an icon with aria-hidden
      const icons = document.querySelectorAll('svg');
      icons.forEach((icon) => {
        expect(icon).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });
});
