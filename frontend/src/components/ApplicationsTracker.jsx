import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Table as TableIcon,
  Kanban as KanbanIcon,
  Search,
  ExternalLink,
  Trash2,
  Calendar,
  Check,
  FileSpreadsheet,
  Layers,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import KanbanBoard from './KanbanBoard';
import FollowUpBanner from './FollowUpBanner';
import {
  getApplications,
  updateApplication,
  deleteApplication,
  downloadExcelReport,
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

  const todayStr = new Date().toISOString().slice(0, 10);

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
        <div className="card-corporate p-4 bg-white border border-[#e0e0e0] rounded-lg flex items-center justify-between shadow-none">
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Total Tracked</div>
            <div className="text-2xl font-bold font-mono text-[#000000] mt-1">{totalApps}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#0a66c2]/10 border border-[#0a66c2]/20 flex items-center justify-center text-[#0a66c2]">
            <Briefcase size={18} />
          </div>
        </div>

        <div className="card-corporate p-4 bg-white border border-[#e0e0e0] rounded-lg flex items-center justify-between shadow-none">
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Interviewing</div>
            <div className="text-2xl font-bold font-mono text-[#004e99] mt-1">{interviewCount}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#004e99]/10 border border-[#004e99]/20 flex items-center justify-center text-[#004e99]">
            <CheckCircle2 size={18} />
          </div>
        </div>

        <div className="card-corporate p-4 bg-white border border-[#e0e0e0] rounded-lg flex items-center justify-between shadow-none">
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Offers Received</div>
            <div className="text-2xl font-bold font-mono text-[#057642] mt-1">{offerCount}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#057642]/10 border border-[#057642]/20 flex items-center justify-center text-[#057642]">
            <Sparkles size={18} />
          </div>
        </div>

        <div className="card-corporate p-4 bg-white border border-[#e0e0e0] rounded-lg flex items-center justify-between shadow-none">
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Follow-ups Set</div>
            <div className="text-2xl font-bold font-mono text-[#b24020] mt-1">{followUpCount}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#b24020]/10 border border-[#b24020]/20 flex items-center justify-center text-[#b24020]">
            <Calendar size={18} />
          </div>
        </div>
      </div>

      {/* Reminders Banner */}
      <FollowUpBanner applications={applications} />

      {/* Action & Filter Bar */}
      <div className="card-corporate p-5 bg-white border border-[#e0e0e0] rounded-lg space-y-4 shadow-none">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-bold text-[#000000] tracking-tight flex items-center gap-2">
              <Layers size={18} className="text-[#0a66c2]" />
              <span>Application Pipeline</span>
            </h2>
            <span className="badge-corporate bg-[#f3f6f8] text-[#000000] font-mono text-[11px] border border-[#e0e0e0]">
              {filteredApps.length} Roles
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* View Switcher */}
            <div className="flex bg-[#f3f6f8] p-1 rounded-full border border-[#e0e0e0] text-xs">
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1.5 px-3.5 py-1 rounded-full font-semibold transition-all ${
                  viewMode === 'table'
                    ? 'bg-[#0a66c2] text-white shadow-sm'
                    : 'text-[#666666] hover:text-[#000000]'
                }`}
              >
                <TableIcon size={13} />
                <span>Table</span>
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`flex items-center gap-1.5 px-3.5 py-1 rounded-full font-semibold transition-all ${
                  viewMode === 'kanban'
                    ? 'bg-[#0a66c2] text-white shadow-sm'
                    : 'text-[#666666] hover:text-[#000000]'
                }`}
              >
                <KanbanIcon size={13} />
                <span>Kanban</span>
              </button>
            </div>

            {/* Export to Excel */}
            <button
              onClick={() => downloadExcelReport().catch((err) => alert(err.message))}
              className="btn-secondary-corporate text-xs py-1 px-3.5"
              title="Download formatted Excel spreadsheet"
            >
              <FileSpreadsheet size={14} className="text-[#057642]" />
              <span>Export .xlsx</span>
            </button>
          </div>
        </div>

        {/* Filter Pills Bar + Search */}
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between pt-1">
          {/* Status Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            <button
              onClick={() => setStatusFilter('ALL')}
              className={`px-3 py-1 rounded-full font-semibold transition-all whitespace-nowrap ${
                statusFilter === 'ALL'
                  ? 'bg-[#0a66c2] text-white'
                  : 'bg-[#f3f6f8] text-[#666666] hover:text-[#000000] border border-[#e0e0e0]'
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
                  className={`px-3 py-1 rounded-full font-semibold transition-all whitespace-nowrap ${
                    statusFilter === st
                      ? 'bg-[#0a66c2] text-white'
                      : 'bg-[#f3f6f8] text-[#666666] hover:text-[#000000] border border-[#e0e0e0]'
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
              className="input-corporate w-full pl-8 text-xs py-1.5"
            />
            <Search size={13} className="absolute left-2.5 top-2.5 text-[#666666]" />
          </div>
        </div>
      </div>

      {/* Content: Table or Kanban */}
      {loading ? (
        <div className="py-12 text-center text-[#666666] text-xs font-mono">Loading applications...</div>
      ) : applications.length === 0 ? (
        <div className="card-corporate p-12 bg-white border border-[#e0e0e0] text-center space-y-3 rounded-lg shadow-none">
          <Briefcase className="mx-auto text-[#666666]" size={40} />
          <h3 className="font-bold text-[#000000] text-sm">No tracked applications yet</h3>
          <p className="text-xs text-[#666666] max-w-md mx-auto">
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
        <div className="card-corporate bg-white border border-[#e0e0e0] rounded-lg overflow-hidden shadow-none">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#f3f6f8] border-b border-[#e0e0e0] text-[#000000] font-semibold text-xs uppercase tracking-wider">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Company & Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Location & Salary</th>
                  <th className="py-3 px-4">Follow-Up</th>
                  <th className="py-3 px-4">Notes</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e0e0e0]">
                {filteredApps.map((app) => {
                  const isOverdue = app.follow_up_date && app.follow_up_date <= todayStr;

                  return (
                    <tr
                      key={app.id}
                      className="hover:bg-[#f9fafb] transition-colors group"
                    >
                      {/* Date */}
                      <td className="py-3 px-4 font-mono text-[#666666] whitespace-nowrap text-[11px]">
                        {app.date_added}
                      </td>

                      {/* Company & Role */}
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#000000] flex items-center gap-1.5 text-xs">
                          <span>{app.company}</span>
                          {app.url && (
                            <a
                              href={app.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[#666666] hover:text-[#0a66c2] transition-colors"
                              title="Open original job link"
                            >
                              <ExternalLink size={11} />
                            </a>
                          )}
                        </div>
                        <div className="text-[#666666] font-medium text-[11px] mt-0.5">{app.role}</div>
                        {app.required_skills && app.required_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {app.required_skills.slice(0, 3).map((s, i) => (
                              <span key={i} className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0] text-[10px] font-mono">
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
                          className={`badge-corporate status-${app.status.toLowerCase()} text-xs font-semibold cursor-pointer outline-none border`}
                        >
                          {STATUS_OPTIONS.map((st) => (
                            <option key={st} value={st} className="bg-white text-[#000000]">
                              {st}
                            </option>
                          ))}
                        </select>
                      </td>

                      {/* Location & Salary */}
                      <td className="py-3 px-4 space-y-0.5 text-[#666666] text-[11px]">
                        <div>{app.location || 'Unknown'}</div>
                        {app.salary && app.salary !== 'Not specified' && (
                          <div className="text-[#057642] font-mono font-semibold">{app.salary}</div>
                        )}
                      </td>

                      {/* Follow-Up Date */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <input
                            type="date"
                            value={app.follow_up_date || ''}
                            onChange={(e) => handleFollowUpDateChange(app.id, e.target.value)}
                            className={`input-corporate px-2 py-1 text-xs font-mono ${
                              isOverdue ? 'border-[#b24020] text-[#b24020] font-bold bg-[#b24020]/5' : ''
                            }`}
                          />
                        </div>
                      </td>

                      {/* Notes */}
                      <td className="py-3 px-4 max-w-xs">
                        {editingNotesId === app.id ? (
                          <div className="flex items-center gap-1.5">
                            <input
                              type="text"
                              value={tempNotes}
                              onChange={(e) => setTempNotes(e.target.value)}
                              className="input-corporate text-xs py-1"
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveNotes(app.id)}
                              className="text-[#057642] hover:text-[#046338] p-1"
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
                            className="cursor-pointer text-[#666666] hover:text-[#000000] line-clamp-2 italic text-[11px]"
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
                          className="text-[#666666] hover:text-[#b24020] p-1 transition-colors"
                          title="Delete application"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
