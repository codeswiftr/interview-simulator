import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TeamSettingsPage from '../TeamSettingsPage';
import type { TeamRead, MemberUsageResponse } from '../../types/team';

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
    getTeamUsage: vi.fn(),
    updateTeam: vi.fn(),
  },
}));

// Mock analytics
vi.mock('../../lib/analytics', () => ({
  analytics: { identify: vi.fn(), track: vi.fn(), reset: vi.fn() },
  Events: { PAGE_VIEWED: 'page_viewed' },
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
  pending_invitations: [],
};

const mockUsage: MemberUsageResponse[] = [
  {
    user_id: 'user-1',
    full_name: 'Alice Admin',
    email: 'alice@acme.com',
    role: 'admin',
    interviews_total: 12,
    interviews_this_month: 3,
  },
  {
    user_id: 'user-2',
    full_name: 'Bob Member',
    email: 'bob@acme.com',
    role: 'member',
    interviews_total: 5,
    interviews_this_month: 1,
  },
];

const renderPage = () =>
  render(
    <MemoryRouter>
      <TeamSettingsPage />
    </MemoryRouter>
  );

describe('TeamSettingsPage', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockResolvedValue(mockTeam);
    vi.mocked(teamAPI.getTeamUsage).mockResolvedValue(mockUsage);
    vi.mocked(teamAPI.updateTeam).mockResolvedValue(mockTeam);
  });

  it('redirects non-admin to /team', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getMyTeam).mockResolvedValue({
      ...mockTeam,
      is_admin: false,
    });

    renderPage();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/team');
    });
  });

  it('renders org name in input field', async () => {
    renderPage();

    await waitFor(() => {
      const input = screen.getByPlaceholderText('Organization name') as HTMLInputElement;
      expect(input.value).toBe('Acme Corp');
    });
  });

  it('renders seat count selector', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('5');
  });

  it('Save button is disabled when name is unchanged', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Organization name')).toBeInTheDocument();
    });

    // Find the Save button (not Update Seats)
    const buttons = screen.getAllByRole('button');
    const saveButton = buttons.find((btn) => btn.textContent?.match(/^Save$/));
    expect(saveButton).toBeDefined();
    expect(saveButton).toBeDisabled();
  });

  it('Save button calls PATCH /teams/{id} when name is changed', async () => {
    const { teamAPI } = await import('../../lib/api');

    renderPage();

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Organization name')).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText('Organization name');
    fireEvent.change(nameInput, { target: { value: 'New Corp Name' } });

    const buttons = screen.getAllByRole('button');
    const saveButton = buttons.find((btn) => btn.textContent?.match(/^Save$/));
    expect(saveButton).not.toBeDisabled();
    fireEvent.click(saveButton!);

    await waitFor(() => {
      expect(teamAPI.updateTeam).toHaveBeenCalledWith('org-123', { name: 'New Corp Name' });
    });
  });

  it('seat count selector only shows options >= current seats_used', async () => {
    // seats_used = 2, so options < 2 should not appear
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    const options = Array.from(select.querySelectorAll('option')).map((o) =>
      Number(o.value)
    );

    // All rendered options must be >= seats_used (2)
    expect(options.every((n) => n >= mockTeam.seats_used)).toBe(true);
  });

  it('Update Seats button is disabled when seat count is unchanged', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const buttons = screen.getAllByRole('button');
    const updateSeatsBtn = buttons.find((btn) => btn.textContent?.match(/Update Seats/));
    expect(updateSeatsBtn).toBeDefined();
    expect(updateSeatsBtn).toBeDisabled();
  });

  it('Update Seats button calls PATCH /teams/{id} when count changes', async () => {
    const { teamAPI } = await import('../../lib/api');

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    // Change from 5 to 10
    fireEvent.change(select, { target: { value: '10' } });

    const buttons = screen.getAllByRole('button');
    const updateSeatsBtn = buttons.find((btn) => btn.textContent?.match(/Update Seats/));
    expect(updateSeatsBtn).not.toBeDisabled();
    fireEvent.click(updateSeatsBtn!);

    await waitFor(() => {
      expect(teamAPI.updateTeam).toHaveBeenCalledWith('org-123', { seat_count: 10 });
    });
  });

  it('shows usage analytics table with member data', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Usage Analytics')).toBeInTheDocument();
    });

    expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    expect(screen.getByText('Bob Member')).toBeInTheDocument();
    // Alice's totals: 12 total, 3 this month
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('shows No usage data message when usage is empty', async () => {
    const { teamAPI } = await import('../../lib/api');
    vi.mocked(teamAPI.getTeamUsage).mockResolvedValueOnce([]);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('No usage data available yet.')).toBeInTheDocument();
    });
  });
});
