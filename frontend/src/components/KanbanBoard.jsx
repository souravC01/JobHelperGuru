import React from 'react';
import { Building2, MapPin, DollarSign, Calendar, ExternalLink, ArrowRight, ArrowLeft } from 'lucide-react';

const COLUMNS = [
  { id: 'Wishlist', label: 'Wishlist', color: 'border-slate-600/60', badge: 'status-wishlist' },
  { id: 'Applied', label: 'Applied', color: 'border-blue-500/60', badge: 'status-applied' },
  { id: 'Interviewing', label: 'Interviewing', color: 'border-amber-500/60', badge: 'status-interviewing' },
  { id: 'Offered', label: 'Offered', color: 'border-emerald-500/60', badge: 'status-offered' },
  { id: 'Rejected', label: 'Rejected', color: 'border-rose-500/60', badge: 'status-rejected' },
];

export default function KanbanBoard({ applications = [], onUpdateStatus, onSelectApp }) {
  const getNextStatus = (current) => {
    const idx = COLUMNS.findIndex((c) => c.id === current);
    if (idx !== -1 && idx < COLUMNS.length - 1) {
      return COLUMNS[idx + 1].id;
    }
    return null;
  };

  const getPrevStatus = (current) => {
    const idx = COLUMNS.findIndex((c) => c.id === current);
    if (idx > 0) {
      return COLUMNS[idx - 1].id;
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 overflow-x-auto pb-4">
      {COLUMNS.map((col) => {
        const columnApps = applications.filter((app) => app.status === col.id);

        return (
          <div
            key={col.id}
            className="flex flex-col bg-slate-900/50 rounded-xl border border-slate-800 p-3 min-w-[260px]"
          >
            {/* Column Header */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className={`badge-pill ${col.badge} text-[11px] py-0.5`}>
                  {col.label}
                </span>
              </div>
              <span className="text-xs font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
                {columnApps.length}
              </span>
            </div>

            {/* Column Cards */}
            <div className="space-y-3 flex-1 overflow-y-auto max-h-[70vh] pr-1">
              {columnApps.length === 0 ? (
                <div className="py-8 text-center text-slate-600 text-xs italic">
                  No applications
                </div>
              ) : (
                columnApps.map((app) => {
                  const nextStatus = getNextStatus(app.status);
                  const prevStatus = getPrevStatus(app.status);

                  return (
                    <div
                      key={app.id}
                      className="glass-card p-3.5 space-y-2.5 border-slate-800 hover:border-slate-700 transition-all text-xs"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-1">
                          <h4 className="font-bold text-slate-100 line-clamp-1">{app.company}</h4>
                          {app.url && (
                            <a
                              href={app.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-slate-500 hover:text-indigo-400 p-0.5"
                            >
                              <ExternalLink size={12} />
                            </a>
                          )}
                        </div>
                        <p className="text-slate-300 font-medium line-clamp-1">{app.role}</p>
                      </div>

                      <div className="space-y-1 text-[11px] text-slate-400">
                        {app.location && app.location !== 'Unknown' && (
                          <div className="flex items-center gap-1">
                            <MapPin size={11} className="text-slate-500" />
                            <span className="line-clamp-1">{app.location}</span>
                          </div>
                        )}
                        {app.salary && app.salary !== 'Not specified' && (
                          <div className="flex items-center gap-1 text-emerald-400">
                            <DollarSign size={11} />
                            <span className="line-clamp-1">{app.salary}</span>
                          </div>
                        )}
                        {app.follow_up_date && (
                          <div className="flex items-center gap-1 text-amber-400 font-medium">
                            <Calendar size={11} />
                            <span>Follow-up: {app.follow_up_date}</span>
                          </div>
                        )}
                      </div>

                      {/* Card Move Actions */}
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                        {prevStatus ? (
                          <button
                            onClick={() => onUpdateStatus(app.id, prevStatus)}
                            title={`Move back to ${prevStatus}`}
                            className="text-[10px] text-slate-400 hover:text-white flex items-center gap-0.5 p-1 rounded hover:bg-slate-800"
                          >
                            <ArrowLeft size={11} />
                            <span>Back</span>
                          </button>
                        ) : (
                          <span />
                        )}

                        {nextStatus && (
                          <button
                            onClick={() => onUpdateStatus(app.id, nextStatus)}
                            title={`Advance to ${nextStatus}`}
                            className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-0.5 p-1 rounded hover:bg-indigo-950/40"
                          >
                            <span>{nextStatus}</span>
                            <ArrowRight size={11} />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
