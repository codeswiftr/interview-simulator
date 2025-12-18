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
      expect(screen.getByText('Progress')).toBeInTheDocument();
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
      const progressLink = screen.getByText('Progress').closest('a');
      const settingsLink = screen.getByText('Settings').closest('a');

      expect(homeLink).toHaveAttribute('href', '/dashboard');
      expect(practiceLink).toHaveAttribute('href', '/practice');
      expect(progressLink).toHaveAttribute('href', '/progress');
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

    it('should highlight progress link when on /progress route', () => {
      render(
        <MemoryRouter initialEntries={['/progress']}>
          <Routes>
            <Route path="*" element={<BottomNav />} />
          </Routes>
        </MemoryRouter>
      );

      const progressLink = screen.getByText('Progress').closest('a');
      expect(progressLink).toHaveClass('text-electric-blue');
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
