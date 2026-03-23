import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AcceptInvitationPage from '../AcceptInvitationPage';
import type { PublicInvitationRead } from '../../types/team';

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock API modules
vi.mock('../../lib/api', () => ({
  teamAPI: {
    getInvitation: vi.fn(),
    acceptInvitation: vi.fn(),
  },
}));

// Mock analytics
vi.mock('../../lib/analytics', () => ({
  analytics: { identify: vi.fn(), track: vi.fn(), reset: vi.fn() },
  Events: { PAGE_VIEWED: 'page_viewed' },
}));

// Mock useAuth — default to unauthenticated
const mockUseAuth = vi.fn(() => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  loading: false,
}));

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}));

const mockInvitation: PublicInvitationRead = {
  token: 'test-token-abc',
  org_name: 'Acme Corp',
  inviter_name: 'Alice Admin',
  email: 'charlie@acme.com',
  role: 'member',
  expires_at: '2026-04-01T00:00:00Z',
};

const renderPage = (token = 'test-token-abc') =>
  render(
    <MemoryRouter initialEntries={[`/join/${token}`]}>
      <Routes>
        <Route path="/join/:token" element={<AcceptInvitationPage />} />
      </Routes>
    </MemoryRouter>
  );

describe('AcceptInvitationPage', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      loading: false,
    });
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getInvitation).mockResolvedValue(mockInvitation);
    vi.mocked(teamAPI.acceptInvitation).mockResolvedValue({
      user_id: 'user-3',
      full_name: 'Charlie',
      email: 'charlie@acme.com',
      role: 'member',
      joined_at: new Date().toISOString(),
    });
  });

  it('shows loading state on mount', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getInvitation).mockReturnValue(new Promise(() => {}));
    // Also simulate auth still loading
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      loading: true,
    });

    renderPage();

    expect(screen.getByText(/Loading invitation/i)).toBeInTheDocument();
  });

  it('shows error when token is invalid (404)', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getInvitation).mockRejectedValueOnce({
      response: { status: 404, data: { detail: 'Invitation not found' } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Invitation Unavailable')).toBeInTheDocument();
    });

    expect(
      screen.getByText('This invitation is no longer valid. Contact your team admin.')
    ).toBeInTheDocument();
  });

  it('shows error when invitation is gone (410)', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getInvitation).mockRejectedValueOnce({
      response: { status: 410, data: { detail: 'Invitation expired' } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Invitation Unavailable')).toBeInTheDocument();
    });
  });

  it('shows invitation card with org name and inviter when valid', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.getByText("You're invited to join")).toBeInTheDocument();
    expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    expect(screen.getByText('Invited by')).toBeInTheDocument();
  });

  it('unauthenticated user sees Sign In link with redirect param', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    const signInLink = screen.getByRole('link', { name: /Sign In/i });
    expect(signInLink).toBeInTheDocument();
    expect(signInLink.getAttribute('href')).toContain('/login');
    expect(signInLink.getAttribute('href')).toContain('redirect=/join/test-token-abc');
  });

  it('unauthenticated user sees Create Account link with redirect param', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    const registerLink = screen.getByRole('link', { name: /Create Account/i });
    expect(registerLink).toBeInTheDocument();
    expect(registerLink.getAttribute('href')).toContain('/register');
    expect(registerLink.getAttribute('href')).toContain('redirect=/join/test-token-abc');
  });

  it('authenticated user sees Accept Invitation button', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 'user-3', email: 'charlie@acme.com', full_name: 'Charlie' },
      isAuthenticated: true,
      isLoading: false,
      loading: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Accept Invitation/i })).toBeInTheDocument();
  });

  it('Accept button calls POST /teams/invitations/{token}/accept', async () => {
    const { teamAPI } = await import('../../lib/api');
    mockUseAuth.mockReturnValue({
      user: { id: 'user-3', email: 'charlie@acme.com', full_name: 'Charlie' },
      isAuthenticated: true,
      isLoading: false,
      loading: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Accept Invitation/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Accept Invitation/i }));

    await waitFor(() => {
      expect(teamAPI.acceptInvitation).toHaveBeenCalledWith('test-token-abc');
    });
  });

  it('navigates to /team on successful accept', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 'user-3', email: 'charlie@acme.com', full_name: 'Charlie' },
      isAuthenticated: true,
      isLoading: false,
      loading: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Accept Invitation/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Accept Invitation/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/team');
    });
  });

  it('shows error when accept fails', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.acceptInvitation).mockRejectedValueOnce({
      response: { status: 409, data: { detail: 'Already a member of this organization' } },
    });
    mockUseAuth.mockReturnValue({
      user: { id: 'user-3', email: 'charlie@acme.com', full_name: 'Charlie' },
      isAuthenticated: true,
      isLoading: false,
      loading: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Accept Invitation/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Accept Invitation/i }));

    await waitFor(() => {
      expect(
        screen.getByText('Already a member of this organization')
      ).toBeInTheDocument();
    });
  });
});
