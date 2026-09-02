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
      {/* Reminders Banner */}
      <FollowUpBanner applications={applications} />

      {/* Action & Filter Bar */}
      <div className="glass-panel p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Briefcase size={20} className="text-indigo-400" />
              <span>Job Applications Tracker</span>
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-indigo-300 font-semibold border border-slate-700">
              {filteredApps.length} Jobs
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* View Switcher */}
            <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <TableIcon size={14} />
                <span>Table</span>
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-all ${
                  viewMode === 'kanban'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <KanbanIcon size={14} />
                <span>Kanban</span>
              </button>
            </div>

            {/* Export to Excel */}
            <a
              href={getExcelExportUrl()}
              download="job_tracker.xlsx"
              className="btn-excel text-xs"
            >
              <FileSpreadsheet size={15} />
              <span>Export to Excel (.xlsx)</span>
            </a>
          </div>
        </div>

        {/* Search & Filter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="relative sm:col-span-2">
            <input
              type="text"
              placeholder="Search by company, role, or skill..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-9 text-xs"
            />
            <Search size={14} className="absolute left-3 top-3 text-slate-500" />
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field text-xs"
            >
              <option value="ALL">All Statuses</option>
              {STATUS_OPTIONS.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Content: Table or Kanban */}
      {loading ? (
        <div className="py-12 text-center text-slate-500 text-sm">Loading applications...</div>
      ) : applications.length === 0 ? (
        <div className="glass-panel p-12 text-center space-y-3">
          <Briefcase className="mx-auto text-slate-600" size={44} />
          <h3 className="font-semibold text-slate-300 text-base">No tracked applications yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Analyze a job description link above and click <strong>"Save to Tracker"</strong> to build your pipeline!
          </p>
        </div>
      ) : viewMode === 'kanban' ? (
        <KanbanBoard
          applications={filteredApps}
          onUpdateStatus={handleStatusChange}
        />
      ) : (
        /* Table View */
        <div className="glass-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
                  <th className="py-3.5 px-4">Date Added</th>
                  <th className="py-3.5 px-4">Company & Role</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Location & Salary</th>
                  <th className="py-3.5 px-4">Follow-Up</th>
                  <th className="py-3.5 px-4">Notes</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredApps.map((app) => (
                  <tr
                    key={app.id}
                    className="hover:bg-slate-800/30 transition-colors group"
                  >
                    {/* Date */}
                    <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                      {app.date_added}
                    </td>

                    {/* Company & Role */}
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100 flex items-center gap-1.5">
                        <span>{app.company}</span>
                        {app.url && (
                          <a
                            href={app.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-500 hover:text-indigo-400"
                            title="Open original job link"
                          >
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                      <div className="text-slate-300 font-medium">{app.role}</div>
                      {app.required_skills && app.required_skills.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {app.required_skills.slice(0, 3).map((s, i) => (
                            <span key={i} className="badge-pill bg-slate-800 text-slate-400 text-[10px] py-0.2">
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
                        className={`badge-pill status-${app.status.toLowerCase()} text-xs font-semibold cursor-pointer outline-none bg-transparent`}
                      >
                        {STATUS_OPTIONS.map((st) => (
                          <option key={st} value={st} className="bg-slate-900 text-slate-100">
                            {st}
                          </option>
                        ))}
                      </select>
                    </td>

                    {/* Location & Salary */}
                    <td className="py-3 px-4 space-y-0.5 text-slate-400">
                      <div>{app.location || 'Unknown'}</div>
                      {app.salary && app.salary !== 'Not specified' && (
                        <div className="text-emerald-400 font-medium">{app.salary}</div>
                      )}
                    </td>

                    {/* Follow-Up Date */}
                    <td className="py-3 px-4">
                      <input
                        type="date"
                        value={app.follow_up_date || ''}
                        onChange={(e) => handleFollowUpDateChange(app.id, e.target.value)}
                        className="bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-300 text-xs font-mono"
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
                          className="cursor-pointer text-slate-400 hover:text-slate-200 line-clamp-2 italic"
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
                        className="text-slate-600 hover:text-rose-400 p-1 transition-colors"
                        title="Delete application"
                      >
                        <Trash2 size={15} />
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
