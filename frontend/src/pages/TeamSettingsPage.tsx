import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings,
  BarChart3,
  Save,
  AlertTriangle,
  Loader2,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { teamAPI } from '../lib/api';
import { Card } from '../components/ui/Card';
import type { TeamRead, MemberUsageResponse } from '../types/team';

export default function TeamSettingsPage() {
  const navigate = useNavigate();
  const [team, setTeam] = useState<TeamRead | null>(null);
  const [usage, setUsage] = useState<MemberUsageResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Org name form state
  const [orgName, setOrgName] = useState('');
  const [isSavingName, setIsSavingName] = useState(false);
  const [nameSaved, setNameSaved] = useState(false);

  // Seat count form state
  const [seatCount, setSeatCount] = useState(5);
  const [isSavingSeats, setIsSavingSeats] = useState(false);
  const [seatsSaved, setSeatsSaved] = useState(false);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [teamData, usageData] = await Promise.all([
        teamAPI.getMyTeam(),
        teamAPI.getTeamUsage((await teamAPI.getMyTeam()).id),
      ]);
      setTeam(teamData);
      setOrgName(teamData.name);
      setSeatCount(teamData.seat_count);
      setUsage(usageData);
    } catch {
      setError('Failed to load team data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleSaveName = async () => {
    if (!team || !orgName.trim() || orgName === team.name) return;
    try {
      setIsSavingName(true);
      await teamAPI.updateTeam(team.id, { name: orgName.trim() });
      setNameSaved(true);
      setTimeout(() => setNameSaved(false), 2000);
      await loadData();
    } catch {
      setError('Failed to update organization name.');
    } finally {
      setIsSavingName(false);
    }
  };

  const handleSaveSeats = async () => {
    if (!team || seatCount === team.seat_count) return;
    try {
      setIsSavingSeats(true);
      await teamAPI.updateTeam(team.id, { seat_count: seatCount });
      setSeatsSaved(true);
      setTimeout(() => setSeatsSaved(false), 2000);
      await loadData();
    } catch {
      setError('Failed to update seat count.');
    } finally {
      setIsSavingSeats(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">{error || 'Team not found'}</p>
          <button onClick={() => navigate('/team')} className="mt-4 text-indigo-600 hover:underline">
            Back to Team Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!team.is_admin) {
    navigate('/team');
    return null;
  }

  const seatUsagePct = team.seat_count > 0 ? (team.seats_used / team.seat_count) * 100 : 0;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <Settings className="w-7 h-7 text-indigo-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Settings</h1>
          <p className="text-gray-500 text-sm">{team.name}</p>
        </div>
        <button
          onClick={() => navigate('/team')}
          className="ml-auto text-sm text-gray-500 hover:text-gray-700"
        >
          ← Back to Dashboard
        </button>
      </div>

      <div className="space-y-6">
        {/* Organization Name */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Name</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Organization name"
            />
            <button
              onClick={handleSaveName}
              disabled={isSavingName || !orgName.trim() || orgName === team.name}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSavingName ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {nameSaved ? 'Saved!' : 'Save'}
            </button>
          </div>
        </Card>

        {/* Seat Management */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Seat Management</h2>
          <p className="text-sm text-gray-500 mb-4">
            {team.seats_used} of {team.seat_count} seats used
          </p>

          {/* Seat usage bar */}
          <div className="w-full h-2 bg-gray-100 rounded-full mb-6">
            <div
              className={`h-2 rounded-full transition-all ${seatUsagePct >= 80 ? 'bg-amber-400' : 'bg-indigo-500'}`}
              style={{ width: `${Math.min(seatUsagePct, 100)}%` }}
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Seat count:</label>
            <select
              value={seatCount}
              onChange={(e) => setSeatCount(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {[5, 10, 15, 25, 50, 100].filter(n => n >= team.seats_used).map(n => (
                <option key={n} value={n}>{n} seats</option>
              ))}
            </select>
            <button
              onClick={handleSaveSeats}
              disabled={isSavingSeats || seatCount === team.seat_count}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSavingSeats ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {seatsSaved ? 'Saved!' : 'Update Seats'}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Contact us to upgrade your plan for more seats or change billing.
          </p>
        </Card>

        {/* Usage Analytics */}
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-gray-900">Usage Analytics</h2>
          </div>

          {usage.length === 0 ? (
            <p className="text-sm text-gray-500">No usage data available yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-3 pr-4 text-gray-500 font-medium">Member</th>
                    <th className="text-left py-3 pr-4 text-gray-500 font-medium">Role</th>
                    <th className="text-right py-3 pr-4 text-gray-500 font-medium">
                      <span className="flex items-center justify-end gap-1">
                        <Calendar className="w-3.5 h-3.5" /> This Month
                      </span>
                    </th>
                    <th className="text-right py-3 text-gray-500 font-medium">
                      <span className="flex items-center justify-end gap-1">
                        <TrendingUp className="w-3.5 h-3.5" /> Total
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {usage.sort((a, b) => b.interviews_total - a.interviews_total).map((m) => (
                    <tr key={m.user_id} className="border-b border-gray-50 hover:bg-gray-50/50">
                      <td className="py-3 pr-4">
                        <div className="font-medium text-gray-900">{m.full_name || '—'}</div>
                        <div className="text-gray-400 text-xs">{m.email}</div>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          m.role === 'admin'
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {m.role}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-right font-medium text-gray-900">
                        {m.interviews_this_month}
                      </td>
                      <td className="py-3 text-right font-medium text-gray-900">
                        {m.interviews_total}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
