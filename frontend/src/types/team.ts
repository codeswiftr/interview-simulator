export interface TeamRead {
  id: string;
  name: string;
  slug: string;
  seat_count: number;
  seats_used: number;
  subscription_status: string | null;
  is_admin: boolean;
  members: TeamMemberRead[];
  pending_invitations: InvitationRead[];
}

export interface TeamMemberRead {
  user_id: string;
  full_name: string | null;
  email: string;
  role: 'admin' | 'member';
  joined_at: string;
}

export interface InvitationRead {
  id: string;
  org_id: string;
  email: string;
  role: 'admin' | 'member';
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
}

export interface PublicInvitationRead {
  token: string;
  org_name: string;
  inviter_name: string;
  email: string;
  role: 'admin' | 'member';
  expires_at: string;
}

export interface MemberUsageResponse {
  user_id: string;
  full_name: string | null;
  email: string;
  role: 'admin' | 'member';
  interviews_total: number;
  interviews_this_month: number;
}
