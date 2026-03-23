import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TeamDashboardPage from '../TeamDashboardPage';
import type { TeamRead } from '../../types/team';

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
    getMyTeam: vi.fn(),
    removeMember: vi.fn(),
    revokeInvitation: vi.fn(),
    updateMemberRole: vi.fn(),
    inviteMembers: vi.fn(),
  },
  subscriptionsAPI: {
    createPortalSession: vi.fn(),
  },
}));

// Mock analytics
vi.mock('../../lib/analytics', () => ({
  analytics: { identify: vi.fn(), track: vi.fn(), reset: vi.fn() },
  Events: { PAGE_VIEWED: 'page_viewed' },
}));

// Mock useAuth
vi.mock('../../hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: 'user-1', email: 'alice@acme.com', full_name: 'Alice Admin' },
    isAuthenticated: true,
    loading: false,
  })),
}));

const mockTeam: TeamRead = {
  id: 'org-123',
  name: 'Acme Corp',
  slug: 'acme-corp-abc123',
  seat_count: 5,
  seats_used: 2,
  subscription_status: 'active',
  is_admin: true,
  members: [
    {
      user_id: 'user-1',
      full_name: 'Alice Admin',
      email: 'alice@acme.com',
      role: 'admin',
      joined_at: '2026-01-01T00:00:00Z',
    },
    {
      user_id: 'user-2',
      full_name: 'Bob Member',
      email: 'bob@acme.com',
      role: 'member',
      joined_at: '2026-01-15T00:00:00Z',
    },
  ],
  pending_invitations: [
    {
      id: 'inv-1',
      org_id: 'org-123',
      email: 'charlie@acme.com',
      role: 'member',
      status: 'pending',
      expires_at: '2026-04-01T00:00:00Z',
      accepted_at: null,
      created_at: '2026-03-15T00:00:00Z',
    },
  ],
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <TeamDashboardPage />
    </MemoryRouter>
  );

describe('TeamDashboardPage', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockResolvedValue(mockTeam);
  });

  it('renders loading skeleton initially', async () => {
    // Delay resolution so we can catch the loading state
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockReturnValue(new Promise(() => {}));

    renderPage();

    // Skeleton has animate-pulse class
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  it('navigates to /pricing when GET /teams/me returns 404', async () => {
    const { teamAPI } = await import('../../lib/api');
    const error = { response: { status: 404, data: { detail: 'Not found' } } };
    vi.mocked(teamAPI.getMyTeam).mockRejectedValueOnce(error);

    renderPage();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/pricing');
    });
  });

  it('shows team name and seat usage when data loads', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.getByText(/2 of 5 seats used/i)).toBeInTheDocument();
  });

  it('shows members table with member names and emails', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    });

    expect(screen.getByText('alice@acme.com')).toBeInTheDocument();
    expect(screen.getByText('Bob Member')).toBeInTheDocument();
    expect(screen.getByText('bob@acme.com')).toBeInTheDocument();
  });

  it('shows pending invitations table', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('charlie@acme.com')).toBeInTheDocument();
    });

    expect(screen.getByText(/Pending Invitations/i)).toBeInTheDocument();
  });

  it('admin sees Invite Members button', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Invite Members/i })).toBeInTheDocument();
  });

  it('non-admin does not see Invite Members button', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockResolvedValueOnce({
      ...mockTeam,
      is_admin: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /Invite Members/i })).not.toBeInTheDocument();
  });

  it('admin sees Settings button', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Settings/i })).toBeInTheDocument();
  });

  it('non-admin does not see Settings button', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockResolvedValueOnce({
      ...mockTeam,
      is_admin: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /^Settings$/i })).not.toBeInTheDocument();
  });

  it('admin sees Remove button per member row for other members', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Bob Member')).toBeInTheDocument();
    });

    // Bob is not self (current user is alice), so Remove button should appear
    expect(screen.getByRole('button', { name: /Remove bob@acme.com/i })).toBeInTheDocument();
  });

  it('non-admin does not see Remove buttons', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockResolvedValueOnce({
      ...mockTeam,
      is_admin: false,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Bob Member')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /Remove/i })).not.toBeInTheDocument();
  });

  it('admin sees Promote/Demote buttons for other members', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Bob Member')).toBeInTheDocument();
    });

    // Bob is a member so admin sees Promote button
    expect(screen.getByRole('button', { name: /Promote/i })).toBeInTheDocument();
  });

  it('Invite Members modal opens when button is clicked', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Invite Members/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Invite Members/i }));

    await waitFor(() => {
      expect(screen.getByText('Invite Team Members')).toBeInTheDocument();
    });
  });

  it('Remove member calls delete endpoint and refreshes', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.removeMember).mockResolvedValueOnce(undefined);

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Remove bob@acme.com/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Remove bob@acme.com/i }));

    await waitFor(() => {
      expect(teamAPI.removeMember).toHaveBeenCalledWith('org-123', 'user-2');
    });
  });

  it('shows error state on API failure', async () => {
    const { teamAPI } = await import('../../lib/api');
    const error = {
      response: { status: 500, data: { detail: 'Server error' } },
    };
    vi.mocked(teamAPI.getMyTeam).mockRejectedValueOnce(error);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Team')).toBeInTheDocument();
    });

    expect(screen.getByText('Server error')).toBeInTheDocument();
  });
});
