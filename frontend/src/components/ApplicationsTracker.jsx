import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Table as TableIcon,
  Kanban as KanbanIcon,
  Search,
  Filter,
  Download,
  Trash2,
  Calendar,
  ExternalLink,
  Edit2,
  Check,
  Building2,
  FileSpreadsheet,
  Layers,
  Sparkles,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import KanbanBoard from './KanbanBoard';
import FollowUpBanner from './FollowUpBanner';
import {
  getApplications,
  updateApplication,
  deleteApplication,
  getExcelExportUrl,
} from '../api/client';

const STATUS_OPTIONS = ['Wishlist', 'Applied', 'Interviewing', 'Offered', 'Rejected', 'Archived'];

export default function ApplicationsTracker({ refreshTrigger }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'kanban'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [editingNotesId, setEditingNotesId] = useState(null);
  const [tempNotes, setTempNotes] = useState('');

  const loadApplications = async () => {
    setLoading(true);
    try {
      const data = await getApplications();
      setApplications(data);
    } catch (err) {
      console.error('Failed to load applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, [refreshTrigger]);

  const handleStatusChange = async (appId, newStatus) => {
    try {
      await updateApplication(appId, { status: newStatus });
      setApplications((prev) =>
        prev.map((app) => (app.id === appId ? { ...app, status: newStatus } : app))
      );
    } catch (err) {
      alert('Failed to update status');
    }
  };

  const handleFollowUpDateChange = async (appId, newDate) => {
    try {
      await updateApplication(appId, { follow_up_date: newDate });
      setApplications((prev) =>
        prev.map((app) => (app.id === appId ? { ...app, follow_up_date: newDate } : app))
      );
    } catch (err) {
      alert('Failed to update follow-up date');
    }
  };

  const handleSaveNotes = async (appId) => {
    try {
      await updateApplication(appId, { notes: tempNotes });
      setApplications((prev) =>
        prev.map((app) => (app.id === appId ? { ...app, notes: tempNotes } : app))
      );
      setEditingNotesId(null);
    } catch (err) {
      alert('Failed to update notes');
    }
  };

  const handleDelete = async (appId) => {
    if (!window.confirm('Delete this tracked application?')) return;
    try {
      await deleteApplication(appId);
      setApplications((prev) => prev.filter((app) => app.id !== appId));
    } catch (err) {
      alert('Failed to delete application');
    }
  };

  // KPIs
  const totalApps = applications.length;
  const appliedCount = applications.filter((a) => a.status === 'Applied').length;
  const interviewCount = applications.filter((a) => a.status === 'Interviewing').length;
  const offerCount = applications.filter((a) => a.status === 'Offered').length;
  const followUpCount = applications.filter((a) => a.follow_up_date).length;

  // Filtered applications
  const filteredApps = applications.filter((app) => {
    const matchesStatus = statusFilter === 'ALL' || app.status === statusFilter;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !query ||
      app.company.toLowerCase().includes(query) ||
      app.role.toLowerCase().includes(query) ||
      (app.location && app.location.toLowerCase().includes(query)) ||
      (app.required_skills && app.required_skills.some((s) => s.toLowerCase().includes(query)));
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 4 KPI Metrics Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        <div className="glass-card p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">Total Tracked</div>
            <div className="text-2xl font-bold font-mono text-white mt-1">{totalApps}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Briefcase size={18} />
          </div>
        </div>

        <div className="glass-card p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">Interviewing</div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{interviewCount}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <CheckCircle2 size={18} />
          </div>
        </div>

        <div className="glass-card p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">Offers Received</div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">{offerCount}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Sparkles size={18} />
          </div>
        </div>

        <div className="glass-card p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">Follow-ups Set</div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{followUpCount}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Calendar size={18} />
          </div>
        </div>
      </div>

      {/* Reminders Banner */}
      <FollowUpBanner applications={applications} />

      {/* Action & Filter Bar */}
      <div className="glass-panel p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <Layers size={18} className="text-indigo-400" />
              <span>Application Pipeline</span>
            </h2>
            <span className="badge-pill bg-white/[0.04] text-indigo-300 font-mono text-[11px] border border-white/10">
              {filteredApps.length} Roles
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* View Switcher */}
            <div className="flex bg-white/[0.03] p-1 rounded-full border border-white/[0.08] text-xs">
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <TableIcon size={13} />
                <span>Table</span>
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-medium transition-all ${
                  viewMode === 'kanban'
                    ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <KanbanIcon size={13} />
                <span>Kanban</span>
              </button>
            </div>

            {/* Export to Excel */}
            <a
              href={getExcelExportUrl()}
              download="job_tracker.xlsx"
              className="btn-excel text-xs"
            >
              <FileSpreadsheet size={14} />
              <span>Export .xlsx</span>
            </a>
          </div>
        </div>

        {/* Filter Pills Bar + Search */}
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between pt-1">
          {/* Status Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => setStatusFilter('ALL')}
              className={`px-3 py-1 rounded-full font-medium transition-all whitespace-nowrap ${
                statusFilter === 'ALL'
                  ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                  : 'bg-white/[0.03] text-zinc-400 hover:text-white border border-white/[0.06]'
              }`}
            >
              All ({totalApps})
            </button>
            {STATUS_OPTIONS.map((st) => {
              const count = applications.filter((a) => a.status === st).length;
              return (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1 rounded-full font-medium transition-all whitespace-nowrap ${
                    statusFilter === st
                      ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                      : 'bg-white/[0.03] text-zinc-400 hover:text-white border border-white/[0.06]'
                  }`}
                >
                  {st} {count > 0 && `(${count})`}
                </button>
              );
            })}
          </div>

          {/* Search Box */}
          <div className="relative min-w-[240px]">
            <input
              type="text"
              placeholder="Search company, role, skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-8 text-xs py-1.5"
            />
            <Search size={13} className="absolute left-2.5 top-2.5 text-zinc-500" />
          </div>
        </div>
      </div>

      {/* Content: Table or Kanban */}
      {loading ? (
        <div className="py-12 text-center text-zinc-500 text-xs font-mono">Loading applications...</div>
      ) : applications.length === 0 ? (
        <div className="glass-panel p-12 text-center space-y-3">
          <Briefcase className="mx-auto text-zinc-600" size={40} />
          <h3 className="font-semibold text-zinc-200 text-sm">No tracked applications yet</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            Analyze a job description link above and click <strong>"Add to Pipeline"</strong> to populate your tracker!
          </p>
        </div>
      ) : viewMode === 'kanban' ? (
        <KanbanBoard
          applications={filteredApps}
          onUpdateStatus={handleStatusChange}
        />
      ) : (
        /* High-Density Data Grid Table */
        <div className="glass-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-white/[0.02] border-b border-white/[0.06] text-zinc-400 font-mono uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Company & Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Location & Salary</th>
                  <th className="py-3 px-4">Follow-Up</th>
                  <th className="py-3 px-4">Notes</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredApps.map((app) => (
                  <tr
                    key={app.id}
                    className="hover:bg-white/[0.025] transition-colors group"
                  >
                    {/* Date */}
                    <td className="py-3 px-4 font-mono text-zinc-400 whitespace-nowrap text-[11px]">
                      {app.date_added}
                    </td>

                    {/* Company & Role */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-zinc-100 flex items-center gap-1.5 text-xs">
                        <span>{app.company}</span>
                        {app.url && (
                          <a
                            href={app.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-zinc-500 hover:text-indigo-400 transition-colors"
                            title="Open original job link"
                          >
                            <ExternalLink size={11} />
                          </a>
                        )}
                      </div>
                      <div className="text-zinc-400 font-medium text-[11px] mt-0.5">{app.role}</div>
                      {app.required_skills && app.required_skills.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {app.required_skills.slice(0, 3).map((s, i) => (
                            <span key={i} className="badge-pill bg-white/[0.03] text-zinc-400 text-[9px] py-0.2 px-1.5 font-mono">
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>

                    {/* Status Dropdown */}
                    <td className="py-3 px-4">
                      <select
                        value={app.status}
                        onChange={(e) => handleStatusChange(app.id, e.target.value)}
                        className={`badge-pill status-${app.status.toLowerCase()} text-xs font-semibold cursor-pointer outline-none bg-transparent font-mono`}
                      >
                        {STATUS_OPTIONS.map((st) => (
                          <option key={st} value={st} className="bg-[#121215] text-zinc-100">
                            {st}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Location & Salary */}
                    <td className="py-3 px-4 space-y-0.5 text-zinc-400 text-[11px]">
                      <div>{app.location || 'Unknown'}</div>
                      {app.salary && app.salary !== 'Not specified' && (
                        <div className="text-emerald-400 font-mono font-medium">{app.salary}</div>
                      )}
                    </td>

                    {/* Follow-Up Date */}
                    <td className="py-3 px-4">
                      <input
                        type="date"
                        value={app.follow_up_date || ''}
                        onChange={(e) => handleFollowUpDateChange(app.id, e.target.value)}
                        className="bg-white/[0.03] border border-white/10 rounded-lg px-2 py-1 text-zinc-300 text-xs font-mono outline-none focus:border-indigo-500/50"
                      />
                    </td>

                    {/* Notes */}
                    <td className="py-3 px-4 max-w-xs">
                      {editingNotesId === app.id ? (
                        <div className="flex items-center gap-1.5">
                          <input
                            type="text"
                            value={tempNotes}
                            onChange={(e) => setTempNotes(e.target.value)}
                            className="input-field text-xs py-1"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveNotes(app.id)}
                            className="text-emerald-400 hover:text-emerald-300 p-1"
                          >
                            <Check size={14} />
                          </button>
                        </div>
                      ) : (
                        <div
                          onClick={() => {
                            setEditingNotesId(app.id);
                            setTempNotes(app.notes || '');
                          }}
                          className="cursor-pointer text-zinc-400 hover:text-zinc-200 line-clamp-2 italic text-[11px]"
                          title="Click to edit notes"
                        >
                          {app.notes || 'Add notes...'}
                        </div>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(app.id)}
                        className="text-zinc-600 hover:text-rose-400 p-1 transition-colors"
                        title="Delete application"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
