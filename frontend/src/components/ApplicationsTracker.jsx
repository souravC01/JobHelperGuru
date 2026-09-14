import { useState } from 'react';
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
import {
  updateApplication,
  deleteApplication,
  downloadExcelReport,
} from '../api/client';
import { localDate } from '../utils/localDate';

const STATUS_OPTIONS = ['Wishlist', 'Applied', 'Interviewing', 'Offered', 'Rejected', 'Archived'];
const METRIC_CARD_CLASS = 'card-corporate p-4 bg-white border border-[#e0e0e0] rounded-lg flex items-center justify-between shadow-none text-left cursor-pointer outline-offset-2 focus-visible:outline-2 focus-visible:outline-[#0a66c2] aria-pressed:outline-2 aria-pressed:outline-[#0a66c2]';

export default function ApplicationsTracker({
  applications = [],
  onApplicationsChanged,
}) {
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'kanban'
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [followUpFilter, setFollowUpFilter] = useState('ALL'); // 'ALL', 'DUE', or 'SET'
  const [editingNotesId, setEditingNotesId] = useState(null);
  const [tempNotes, setTempNotes] = useState('');

  const selectSummaryFilter = (status = 'ALL', followUp = 'ALL') => {
    setStatusFilter(status);
    setFollowUpFilter(followUp);
    setSearchQuery('');
  };

  const isSummarySelected = (status = 'ALL', followUp = 'ALL') => (
    statusFilter === status && followUpFilter === followUp && searchQuery === ''
  );

  const handleStatusChange = async (appId, newStatus) => {
    try {
      const updates = { status: newStatus };
      if (newStatus === 'Applied') {
        updates.application_date = localDate();
      }
      const updated = await updateApplication(appId, updates);
      onApplicationsChanged?.(
        applications.map((app) => (app.id === appId ? updated : app))
      );
    } catch (err) {
      alert('Failed to update status');
    }
  };

  const handleFollowUpDateChange = async (appId, newDate) => {
    try {
      const updated = await updateApplication(appId, { follow_up_date: newDate });
      onApplicationsChanged?.(
        applications.map((app) => (app.id === appId ? updated : app))
      );
    } catch (err) {
      alert('Failed to update follow-up date');
    }
  };

  const handleSaveNotes = async (appId) => {
    try {
      const updated = await updateApplication(appId, { notes: tempNotes });
      onApplicationsChanged?.(
        applications.map((app) => (app.id === appId ? updated : app))
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
      onApplicationsChanged?.(applications.filter((app) => app.id !== appId));
    } catch (err) {
      alert('Failed to delete application');
    }
  };

  // KPIs
  const totalApps = applications.length;
  const interviewCount = applications.filter((a) => a.status === 'Interviewing').length;
  const offerCount = applications.filter((a) => a.status === 'Offered').length;
  const followUpCount = applications.filter((a) => a.follow_up_date).length;

  const todayStr = localDate();
  const isFollowUpDue = (app) => Boolean(
    app.follow_up_date && app.follow_up_date <= todayStr &&
    !['Rejected', 'Archived', 'Offered'].includes(app.status)
  );
  const dueFollowUpCount = applications.filter(isFollowUpDue).length;

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
    const matchesFollowUp = followUpFilter === 'DUE'
      ? isFollowUpDue(app)
      : followUpFilter === 'SET' ? Boolean(app.follow_up_date) : true;
    return matchesStatus && matchesSearch && matchesFollowUp;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 4 KPI Metrics Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        <button
          type="button"
          onClick={() => selectSummaryFilter()}
          aria-pressed={isSummarySelected()}
          className={METRIC_CARD_CLASS}
        >
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Total Tracked</div>
            <div className="text-2xl font-bold font-mono text-[#000000] mt-1">{totalApps}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#0a66c2]/10 border border-[#0a66c2]/20 flex items-center justify-center text-[#0a66c2]">
            <Briefcase size={18} />
          </div>
        </button>

        <button
          type="button"
          onClick={() => selectSummaryFilter('Interviewing')}
          aria-pressed={isSummarySelected('Interviewing')}
          className={METRIC_CARD_CLASS}
        >
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Interviewing</div>
            <div className="text-2xl font-bold font-mono text-[#004e99] mt-1">{interviewCount}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#004e99]/10 border border-[#004e99]/20 flex items-center justify-center text-[#004e99]">
            <CheckCircle2 size={18} />
          </div>
        </button>

        <button
          type="button"
          onClick={() => selectSummaryFilter('Offered')}
          aria-pressed={isSummarySelected('Offered')}
          className={METRIC_CARD_CLASS}
        >
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Offers Received</div>
            <div className="text-2xl font-bold font-mono text-[#057642] mt-1">{offerCount}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#057642]/10 border border-[#057642]/20 flex items-center justify-center text-[#057642]">
            <Sparkles size={18} />
          </div>
        </button>

        <button
          type="button"
          onClick={() => selectSummaryFilter('ALL', 'SET')}
          aria-pressed={isSummarySelected('ALL', 'SET')}
          className={METRIC_CARD_CLASS}
        >
          <div>
            <div className="text-[11px] font-bold text-[#666666] uppercase tracking-wider">Follow-ups Set</div>
            <div className="text-2xl font-bold font-mono text-[#b24020] mt-1">{followUpCount}</div>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#b24020]/10 border border-[#b24020]/20 flex items-center justify-center text-[#b24020]">
            <Calendar size={18} />
          </div>
        </button>
      </div>

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
        <div className="flex flex-col xl:flex-row gap-3 items-stretch xl:items-center justify-between pt-1">
          {/* Status Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              onClick={() => selectSummaryFilter()}
              className={`px-3 py-1 rounded-full font-semibold transition-all whitespace-nowrap ${
                statusFilter === 'ALL'
                  ? 'bg-[#0a66c2] text-white'
                  : 'bg-[#f3f6f8] text-[#666666] hover:text-[#000000] border border-[#e0e0e0]'
              }`}
            >
              All ({totalApps})
            </button>
            <button
              type="button"
              onClick={() => setFollowUpFilter((value) => value === 'DUE' ? 'ALL' : 'DUE')}
              aria-pressed={followUpFilter === 'DUE'}
              title="Show follow-ups due today or overdue"
              className={`px-3 py-1 rounded-full font-semibold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                followUpFilter === 'DUE'
                  ? 'bg-[#0a66c2] text-white'
                  : 'bg-[#f3f6f8] text-[#666666] hover:text-[#000000] border border-[#e0e0e0]'
              }`}
            >
              <Calendar size={12} />
              <span>Follow-up due ({dueFollowUpCount})</span>
            </button>
            {followUpFilter === 'SET' && (
              <button
                type="button"
                onClick={() => setFollowUpFilter('ALL')}
                aria-pressed="true"
                title="Clear the follow-ups set filter"
                className="px-3 py-1 rounded-full font-semibold bg-[#0a66c2] text-white whitespace-nowrap"
              >
                Follow-ups set ({followUpCount}) ×
              </button>
            )}
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
          <div className="relative w-full xl:w-60 shrink-0">
            <input
              type="text"
              placeholder="Search company, role, skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-corporate input-with-leading-icon w-full text-xs py-1.5"
            />
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666] pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Content: Table or Kanban */}
      {applications.length === 0 ? (
        <div className="card-corporate p-12 bg-white border border-[#e0e0e0] text-center space-y-3 rounded-lg shadow-none">
          <Briefcase className="mx-auto text-[#666666]" size={40} />
          <h3 className="font-bold text-[#000000] text-sm">No tracked applications yet</h3>
          <p className="text-xs text-[#666666] max-w-md mx-auto">
            Analyze a job description link above and click <strong>"Add to Pipeline"</strong> to populate your tracker!
          </p>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="card-corporate p-8 bg-white border border-[#e0e0e0] rounded-lg text-center text-sm text-[#666666]">
          No applications match your filters.
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
            <table className="w-full min-w-[1000px] table-fixed text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#f3f6f8] border-b border-[#e0e0e0] text-[#000000] font-semibold text-xs uppercase tracking-wider">
                  <th className="py-3 px-4 w-[10%]">Date</th>
                  <th className="py-3 px-4 w-[24%]">Company & Role</th>
                  <th className="py-3 px-4 w-[14%]">Status</th>
                  <th className="py-3 px-4 w-[13%]">Location & Salary</th>
                  <th className="py-3 px-4 w-[17%]">Follow-Up</th>
                  <th className="py-3 px-4 w-[14%]">Notes</th>
                  <th className="py-3 px-2 w-[8%] text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e0e0e0]">
                {filteredApps.map((app) => {
                  const isOverdue = isFollowUpDue(app);

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
                          <span className="min-w-0 [overflow-wrap:anywhere]">{app.company}</span>
                          {app.url && (
                            <a
                              href={app.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[#666666] hover:text-[#0a66c2] transition-colors shrink-0"
                              title="Open original job link"
                            >
                              <ExternalLink size={11} />
                            </a>
                          )}
                        </div>
                        <div className="text-[#666666] font-medium text-[11px] mt-0.5 [overflow-wrap:anywhere]">{app.role}</div>
                        {app.required_skills && app.required_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {app.required_skills.slice(0, 3).map((s, i) => (
                              <span key={i} className="block max-w-full px-2 py-1 rounded-md bg-[#f3f6f8] text-[#000000] border border-[#e0e0e0] text-[10px] leading-relaxed font-mono whitespace-normal [overflow-wrap:anywhere]">
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
                          className={`badge-corporate status-${app.status.toLowerCase()} w-full min-w-0 text-xs font-semibold cursor-pointer outline-none border`}
                        >
                          {STATUS_OPTIONS.map((st) => (
                            <option key={st} value={st} className="bg-white text-[#000000]">
                              {st}
                            </option>
                          ))}
                        </select>
                      </td>

                      {/* Location & Salary */}
                      <td className="py-3 px-4 space-y-0.5 text-[#666666] text-[11px] [overflow-wrap:anywhere]">
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
                            className={`input-corporate w-full min-w-0 px-2 py-1 text-xs font-mono ${
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
                              className="input-corporate w-full min-w-0 text-xs py-1"
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
                              className="cursor-pointer text-[#666666] hover:text-[#000000] line-clamp-2 italic text-[11px] [overflow-wrap:anywhere]"
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
